# coding:utf8
from . import api, db
from decorators import permission_required
from flask import jsonify, request
from time import sleep
from ipip import IP
import json, urllib2, hashlib, time, sys, os
reload(sys)
sys.setdefaultencoding("utf-8")


#   应用分析表
class AppSflow(db.Model):
    __tablename__ = 'app_sflow'

    id = db.Column(db.Integer, primary_key=True)
    agent = db.Column("agent", db.String)
    timestamp = db.Column("timestamp", db.String)
    src_mac = db.Column("src_mac", db.String)
    dst_mac = db.Column("dst_mac", db.String)
    src_ip = db.Column("src_ip", db.String)
    dst_ip = db.Column("dst_ip", db.String)
    src_port = db.Column("src_port", db.String)
    dst_port = db.Column("dst_port", db.String)
    ip_protocol = db.Column("ip_protocol", db.String)
    ipsize = db.Column("ipsize", db.Integer)


#   数据包分析表
class AppDataAnalysis(db.Model):
    __tablename__ = 'app_data_analysis'

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column("ip", db.String)
    timestamp = db.Column("timestamp", db.String)
    packet = db.Column("packet", db.Integer)
    size = db.Column("size", db.Integer)


#   app ip归属地表
class AppIpRegion(db.Model):
    __tablename__ = 'app_ip_region'

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column("ip", db.String)
    region = db.Column("region", db.String)


#   app ip白名单表
class AppIpWhitelist(db.Model):
    __tablename__ = 'app_ip_whitelist'

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column("ip", db.String)


#   应用源IP流量统计
@api.route("/appsflow/appAnalysis")
@permission_required(["GAME"])
def appsflow_appAnalysis(user):
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    agent = request.args.get('agent')
    type_ = request.args.get('type')
    page = request.args.get('page')
    size = request.args.get('size')
    if page:
        page = int(page)
    else:
        page = 1
    if size:
        size = int(size)
    else:
        size = 10
    MyAppSflow = type('AppSflow_'+str(user.dbname), (AppSflow,), {'__bind_key__': user.dbname})
    MyAppIpRegion = type('AppIpRegion_'+str(user.dbname), (AppIpRegion,), {'__bind_key__': user.dbname})
    #根据查询条件做流量统计
    analysises = db.session.query(MyAppSflow.src_ip, db.func.sum(MyAppSflow.ipsize), MyAppIpRegion.region).\
        select_from(MyAppSflow).outerjoin(MyAppIpRegion, MyAppSflow.src_ip == MyAppIpRegion.ip)
    if type_ == '1':
        analysises = db.session.query(MyAppSflow.dst_ip, db.func.sum(MyAppSflow.ipsize))
    elif type_ == '2':
        analysises = db.session.query(MyAppSflow.src_ip + ' -> ' + MyAppSflow.dst_ip,
                                      db.func.sum(MyAppSflow.ipsize))

    if agent:
        analysises = analysises.filter(MyAppSflow.agent == agent)
    if startTime:
        analysises = analysises.filter(MyAppSflow.timestamp >= startTime)
    if endTime:
        analysises = analysises.filter(MyAppSflow.timestamp <= endTime)

    if type_ == '0':
        MyAppIpWhitelist = type('AppIpWhitelist_' + str(user.dbname), (AppIpWhitelist,),
                                {'__bind_key__': user.dbname})
        whitelists = db.session.query(MyAppIpWhitelist.ip).all()
        ips = []
        for temp in whitelists:
            ips.append(temp[0])
        if len(ips):
            analysises = analysises.filter(~MyAppSflow.src_ip.in_(ips))
        analysises = analysises.group_by(MyAppSflow.src_ip)
    elif type_ == '1':
        analysises = analysises.group_by(MyAppSflow.dst_ip, )
    elif type_ == '2':
        analysises = analysises.group_by(MyAppSflow.src_ip, MyAppSflow.dst_ip)
    analysises = analysises.order_by(db.func.sum(MyAppSflow.ipsize).desc()).paginate(page, size)

    content = {}
    temp = []
    total = 0
    for index in range(len(analysises.items)):
        analysis = analysises.items[index]
        temp.append({'ip': analysis[0], 'ipsize': float(analysis[1]) if float(analysis[1]) else 0})
        total += float(analysis[1]) if float(analysis[1]) else 0
        if type_ == '0':
            temp[index]['region'] = analysis[2]
        if type_ == '1':
            IP.load(os.path.abspath("17monipdb.dat"))
            ip_region = IP.find(analysis[0])
            temp[index]['region'] = ''.join(ip_region.split())
    content['data'] = temp
    content['total'] = total
    return jsonify({'content': content, 'totalElements': analysises.total})


#调用IP138接口查询IP，暂时不用，改用本地离线库
def getIpRegion(ip, result):
    url = "https://api.ip138.com/query/?ip=" + ip + "&oid=11060&mid=73854&sign=" + \
          hashlib.md5("ip=" + ip + '&token=27f2c63310c1d6d2043a205a0847d763').hexdigest()
    jsondata = {"ret": 'err'}
    for i in range(4):
        try:
            temp = urllib2.urlopen(url, timeout=4).read()
        except Exception, e:
            print ip, e.message
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
    result['region'] = region


#   应用分析->服务器IP列表（下拉框用）
@api.route("/appsflow/agentList")
@permission_required(["GAME"])
def appsflow_agentList(user):
    MyAppSflow = type('AppSflow_' + str(user.dbname), (AppSflow,), {'__bind_key__': user.dbname})
    # 获取服务器IP列表
    agents = db.session.query(db.distinct(MyAppSflow.agent)).all()
    result = []
    for temp in agents:
        result.append(temp[0])
    return jsonify(result)


#   时间范围内每个时间点topN IP流量统计
@api.route("/appsflow/intervalAnalysis")
@permission_required(["GAME"])
def appsflow_intervalAnalysis(user):
    MyAppSflow = type('AppSflow_' + str(user.dbname), (AppSflow,), {'__bind_key__': user.dbname})
    agent = request.args.get('agent')
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    type_ = request.args.get('type')
    data = db.session.query(MyAppSflow.timestamp, MyAppSflow.src_ip, db.func.sum(MyAppSflow.ipsize))
    if type_ == '1':
        data = db.session.query(MyAppSflow.timestamp, MyAppSflow.dst_ip, db.func.sum(MyAppSflow.ipsize))
    elif type_ == '2':
        data = db.session.query(MyAppSflow.timestamp, MyAppSflow.src_ip + ' -> ' + MyAppSflow.dst_ip,
                                db.func.sum(MyAppSflow.ipsize))
    if agent:
        data = data.filter(MyAppSflow.agent == agent)
    if startTime:
        data = data.filter(MyAppSflow.timestamp >= startTime)
    if endTime:
        data = data.filter(MyAppSflow.timestamp <= endTime)

    if type_ == '0':
        data = data.filter(db.func.length(MyAppSflow.src_ip) <= 16)
        data = data.group_by(MyAppSflow.timestamp, MyAppSflow.src_ip)
    elif type_ == '1':
        data = data.filter(db.func.length(MyAppSflow.dst_ip) <= 16)
        data = data.group_by(MyAppSflow.timestamp, MyAppSflow.dst_ip)
    elif type_ == '2':
        data = data.filter(db.func.length(MyAppSflow.src_ip) <= 16)
        data = data.filter(db.func.length(MyAppSflow.dst_ip) <= 16)
        data = data.group_by(MyAppSflow.timestamp, MyAppSflow.src_ip, MyAppSflow.dst_ip)
    data = data.order_by(MyAppSflow.timestamp.desc(), db.func.sum(MyAppSflow.ipsize).desc()).all()

    result = {}
    time_list = []
    top = []
    index = 0
    limit = 0
    if len(data):
        for temp in data:
            if not time_list:
                time_list.append("{0}-{1}-{2} {3}:{4}".format(temp[0][0:4], temp[0][4:6], temp[0][6:8],
                                                              temp[0][8:10], temp[0][10:12]))
                top.append([])
                top[index].append(str(changeUnit(temp[2])) + ' （' + temp[1] + '）')
            else:
                if time_list[index] == "{0}-{1}-{2} {3}:{4}".format(temp[0][0:4], temp[0][4:6], temp[0][6:8],
                                                                    temp[0][8:10], temp[0][10:12]):
                    if limit < 9:
                        top[index].append(str(changeUnit(temp[2])) + ' （' + temp[1] + '）')
                        limit += 1
                    else:
                        continue
                else:
                    index += 1
                    limit = 0
                    time_list.append("{0}-{1}-{2} {3}:{4}".format(temp[0][0:4], temp[0][4:6], temp[0][6:8],
                                                                  temp[0][8:10], temp[0][10:12]))
                    top.append([])
                    top[index].append(str(changeUnit(temp[2])) + ' （' + temp[1] + '）')
    result['time_list'] = time_list
    result['top'] = top
    return jsonify(result)


def changeUnit(param):
    if not param:
        return ''
    temp = float(param)
    if temp >= 1024*1024*1024*1024:
        return ('%.2f' % (temp/(1024*1024*1024*1024))) + ' TB'
    elif temp >= 1024*1024*1024:
        return ('%.2f' % (temp/(1024*1024*1024))) + ' GB'
    elif temp >= 1024*1024:
        return ('%.2f' % (temp/(1024*1024))) + ' MB'
    else:
        return ('%.2f' % (temp/1024)) + ' KB'


#   数据包分析->服务器IP列表（下拉框用）
@api.route("/app_data_analysis/findIps")
@permission_required(["GAME"])
def app_data_analysis_findIps(user):
    MyAppDataAnalysis = type('AppDataAnalysis_' + str(user.dbname), (AppDataAnalysis,),
                             {'__bind_key__': user.dbname})
    data = db.session.query(db.distinct(MyAppDataAnalysis.ip)).all()
    result = []
    for temp in data:
        result.append(temp[0])
    return jsonify(result)


#   获取数据包流量数据
@api.route("/app_data_analysis/findAll")
@permission_required(["GAME"])
def app_data_analysis_findAll(user):
    MyAppDataAnalysis = type('AppDataAnalysis_' + str(user.dbname), (AppDataAnalysis,),
                             {'__bind_key__': user.dbname})
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    ip = request.args.get('ip')
    data = db.session.query(MyAppDataAnalysis.timestamp, MyAppDataAnalysis.ip, MyAppDataAnalysis.packet,
                            MyAppDataAnalysis.size)
    max_size = db.session.query(db.func.max(MyAppDataAnalysis.size))
    if ip:
        data = data.filter(MyAppDataAnalysis.ip == ip)
        max_size = max_size.filter(MyAppDataAnalysis.ip == ip)
    if startTime:
        data = data.filter(MyAppDataAnalysis.timestamp >= startTime)
        max_size = max_size.filter(MyAppDataAnalysis.timestamp >= startTime)
    if endTime:
        data = data.filter(MyAppDataAnalysis.timestamp <= endTime)
        max_size = max_size.filter(MyAppDataAnalysis.timestamp <= endTime)
    data = data.order_by(MyAppDataAnalysis.timestamp).all()
    max_size = max_size.all()
    packet = []
    size = []
    fenmu = 1024
    unit = 'Kbps'
    if max_size[0][0]:
        temp = max_size[0][0]/300
        if temp > 1024*1024*1024*1024:
            fenmu = 1024*1024*1024*1024
            unit = 'Tbps'
        elif temp > 1024*1024*1024:
            fenmu = 1024*1024*1024
            unit = 'Gbps'
        elif temp > 1024*1024:
            fenmu = 1024*1024
            unit = 'Mbps'
    for temp in data:
        # 转换成时间数组
        timeArray = time.strptime(temp[0], "%Y%m%d%H%M")
        # 转换成时间戳
        timestamp = time.mktime(timeArray) * 1000 + 8 * 60 * 60 * 1000
        # 每秒数据包个数
        packet.append([timestamp, temp[2]/300])
        # 每秒流量
        size.append([timestamp, round(temp[3]*1.0/fenmu/300, 2)])
    result = {}
    result['ip'] = ip
    result['packet'] = packet
    result['size'] = size
    result['unit'] = unit
    return jsonify(result)
