# coding:utf8
from flask import jsonify, request
from .decorators import permission_required
from . import api, db
from time import time, sleep
import json, threading, urllib2, hashlib, paramiko


#   客户机表
class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column("hostname", db.String)
    port = db.Column("port", db.Integer)
    username = db.Column('username', db.String)
    password = db.Column("password", db.String)

    def __init__(self, hostname, port, username, password):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

    def to_json(self):
        return {
            'id': self.id,
            'hostname': self.hostname,
            'port': self.port,
            'username': self.username
        }


#   查找所有客户机
@api.route("/clients/findAll")
@permission_required(["GAME"])
def clients_findAll(user):
    MyClient = type('Client_' + str(user.dbname), (Client,), {'__bind_key__': user.dbname})
    clients = MyClient.query.order_by(MyClient.hostname).all()
    return jsonify([client.to_json() for client in clients])


#   保存客户机
@api.route("/clients/save", methods=['POST'])
@permission_required(["GAME"])
def clients_save(user):
    data = json.loads(request.data)
    data['hostname'] = data['hostname']
    data['port'] = data['port']
    data['username'] = data['username']
    data['password'] = data['password']
    MyClient = type('Client_' + str(user.dbname), (Client,), {'__bind_key__': user.dbname})
    client = MyClient(data['hostname'], data['port'], data['username'], data['password'])
    db.session.add(client)
    db.session.commit()
    return ''


#   根据ID删除客户机
@api.route("/clients/byIds", methods=['DELETE'])
@permission_required(["GAME"])
def clients_deleteByIds(user):
    ids = request.args.get("ids")
    idlist = ids.split(",")
    MyClient = type('Client_' + str(user.dbname), (Client,), {'__bind_key__': user.dbname})
    db.session.query(MyClient).filter(MyClient.id.in_(idlist)).delete(synchronize_session=False)
    return ''


#   根据ID查找客户机
@api.route("/clients/<int:clientId>")
@permission_required(["GAME"])
def clients_findById(user, clientId):
    MyClient = type('Client_' + str(user.dbname), (Client,), {'__bind_key__': user.dbname})
    client = MyClient.query.get(clientId)
    return jsonify(client.to_json())


#   根据ID更新客户机
@api.route("/clients/<int:clientId>", methods=['PUT'])
@permission_required(["GAME"])
def clients_updateById(user, clientId):
    MyClient = type('Client_' + str(user.dbname), (Client,), {'__bind_key__': user.dbname})
    client = MyClient.query.get(clientId)
    if not client:
        return jsonify({'error': "invalid clientId"}), 500
    hostname = request.json.get("hostname")
    port = request.json.get("port")
    username = request.json.get("username")
    password = request.json.get("password")
    if hostname:
        client.hostname = hostname
    if port:
        client.port = port
    if username:
        client.username = username
    if password:
        client.password = password
    db.session.commit()
    return ''


#   批量ping
@api.route("/clients/getIpInfo", methods=['POST'])
@permission_required(["GAME"])
def clients_getIpInfo(user):
    start = time()
    data = json.loads(request.data)
    iplist = data['ips'].split(',')
    id = data['id']
    MyClient = type('Client_' + str(user.dbname), (Client,), {'__bind_key__': user.dbname})
    client = MyClient.query.get(id)
    result = []
    threads = []
    con = paramiko.SSHClient()
    try:
        con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        con.connect(hostname=client.hostname, port=client.port, username=client.username, password=client.password)
    except Exception, e:
        return jsonify({'error': str(e)}), 500
    for ip in iplist:
        t = threading.Thread(target=clients_pingIp, args=(con, ip, result))
        t.setDaemon(True)
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    con.close()
    print 'main process: ', time() - start
    return jsonify(sorted(result, key=lambda x: x['domain']))


#   ping ip
def clients_pingIp(con, ip, result):
    start = time()
    stdin, stdout, stderr = con.exec_command('ping -c 4 -w 2 ' + ip)
    ret = stdout.read()
    avg_rtt = '不通'
    region = '无效IP'
    flag = 'rtt min/avg/max/mdev =' #判断PING返回结果的查找标志
    search_ip = ret.split('\n')[0]
    search_ip = search_ip[search_ip.find('(')+1: search_ip.find(')')]
    #url = "http://ip.taobao.com/service/getIpInfo.php?ip=" + search_ip
    url = "https://api.ip138.com/query/?ip="+search_ip+"&oid=11060&mid=73854&sign=" + \
        hashlib.md5("ip="+search_ip+'&token=27f2c63310c1d6d2043a205a0847d763').hexdigest()
    jsondata = {"ret": 'err'}
    for i in range(4):
        try:
            temp = urllib2.urlopen(url, timeout=4).read()
        except Exception, e:
            print search_ip, e.message
            if i == 3:
                region = '查询超时'
            sleep(1)
            continue
        print temp
        jsondata = json.loads(temp)
        break
    if jsondata['ret'] == 'ok':
        region = ''.join(jsondata['data'])
    elif jsondata['ret'] == 'err':
        region = jsondata['msg']
    if ret.find(flag) >= 0:
        avg_rtt = ret[ret.find(flag) + len(flag):].strip().split('/')[1]
    result.append({'domain': ip, 'ip':search_ip, 'avg_rtt': avg_rtt, 'region': region})
    print 'ping ip: ', ip, ' - ', time() - start
