#coding=utf8
from flask import request, jsonify
from . import api, db
from .decorators import permission_required
import time
#import netsnmp


class Servermonitor(db.Model):
    __tablename__ = 'servermonitor'

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column("ip", db.String)
    svrname = db.Column("svrname", db.String)
    cpurate = db.Column("cpurate", db.Float)
    mu = db.Column("mu", db.BigInteger)
    mt = db.Column("mt", db.BigInteger)
    du = db.Column("du", db.BigInteger)
    dt = db.Column("dt", db.BigInteger)
    ll1 = db.Column("ll1", db.Float)
    ll5 = db.Column("ll5", db.Float)
    ll15 = db.Column("ll15", db.Float)
    conns = db.Column("conns", db.Integer)
    datetime = db.Column("datetime", db.String)

    def __init__(self, ip, svrname, cpurate, mu, mt, du, dt, ll1, ll5, ll15, conns, datetime):
        self.ip = ip
        self.svrname = svrname
        self.cpurate = cpurate
        self.mu = mu
        self.mt = mt
        self.du = du
        self.dt = dt
        self.ll1 = ll1
        self.ll5 = ll5
        self.ll15 = ll15
        self.conns = conns
        self.datetime = datetime

    def to_json(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'svrname': self.svrname,
            'cpurate': self.cpurate,
            'mu': self.mu,
            'mt': self.mt,
            'du': self.du,
            'dt': self.dt,
            'll1': self.ll1,
            'll5': self.ll5,
            'll15': self.ll15,
            'conns': self.conns,
            'datetime': self.datetime
        }


@api.route("/servermonitors")
@permission_required(["SERVERLIST"])
def servermonitors_findAll(user):
    ip = request.args.get('ip')
    days = int(request.args.get('days'))
    #获取N天前的时间
    starttime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(time.time()) - days * 24 * 60 * 60))
    MyServermonitor = type('Servermonitor_' + str(user.dbname), (Servermonitor,), {'__bind_key__': user.dbname})
    servermonitors = MyServermonitor.query.filter(MyServermonitor.ip == ip).\
        filter(MyServermonitor.datetime > starttime).all()
    result = {}
    result['cpurate_list'] = []
    result['mu_list'] = []
    result['mt_list'] = []
    result['du_list'] = []
    result['dt_list'] = []
    result['ll1_list'] = []
    result['ll5_list'] = []
    result['ll15_list'] = []
    result['conns_list'] = []
    temp_timestamp = servermonitors[0].datetime
    temp_timestamp = "{0}-{1}-{2} {3}:{4}:{5}".format(temp_timestamp[0:4], temp_timestamp[4:6],
                                                      temp_timestamp[6:8], temp_timestamp[8:10],
                                                      temp_timestamp[10:12], temp_timestamp[12:14])
    # 转换成时间数组
    temp_timestamp = time.strptime(temp_timestamp, "%Y-%m-%d %H:%M:%S")
    # 转换成时间戳
    temp_timestamp = time.mktime(temp_timestamp)
    for servermonitor in servermonitors:
        dt = servermonitor.datetime
        dt = "{0}-{1}-{2} {3}:{4}:{5}".format(dt[0:4], dt[4:6],
                                              dt[6:8], dt[8:10],
                                              dt[10:12], dt[12:14])
        # 转换成时间数组
        timeArray = time.strptime(dt, "%Y-%m-%d %H:%M:%S")
        # 转换成时间戳
        timestamp = time.mktime(timeArray)
        points = int(timestamp - temp_timestamp)/(5*60)
        # 中间没有的点补0
        if points > 1:
            for i in range(1, points):
                result['cpurate_list'].append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 0])
                result['mu_list'].append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 0])
                result['mt_list'].append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 0])
                result['du_list'].append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 0])
                result['dt_list'].append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 0])
                result['ll1_list'].append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 0])
                result['ll5_list'].append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 0])
                result['ll15_list'].append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 0])
                result['conns_list'].append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 0])
        result['cpurate_list'].append([timestamp*1000 + 8*60*60*1000, servermonitor.cpurate])
        result['mu_list'].append([timestamp*1000 + 8*60*60*1000, round(servermonitor.mu * 1.0 / 1024**3, 2)])
        result['mt_list'].append([timestamp*1000 + 8*60*60*1000, round(servermonitor.mt * 1.0 / 1024**3, 2)])
        result['du_list'].append([timestamp*1000 + 8*60*60*1000, round(servermonitor.du * 1.0 / 1024**3, 2)])
        result['dt_list'].append([timestamp*1000 + 8*60*60*1000, round(servermonitor.dt * 1.0 / 1024**3, 2)])
        result['ll1_list'].append([timestamp*1000 + 8*60*60*1000, servermonitor.ll1])
        result['ll5_list'].append([timestamp*1000 + 8*60*60*1000, servermonitor.ll5])
        result['ll15_list'].append([timestamp*1000 + 8*60*60*1000, servermonitor.ll15])
        result['conns_list'].append([timestamp*1000 + 8*60*60*1000, servermonitor.conns])

        temp_timestamp = timestamp
    return jsonify(result), {'Cache-Control': 'max-age=300'}

'''
@api.route("/servermonitors/getServerInfo")
@permission_required(["SERVERLIST"])
def servermonitors_getServerInfo(user):
    ip = request.args.get("ip")
    session = netsnmp.Session(Version=2, DestHost=ip, Community="Cache@sz1d", Timeout=3000000, Retries=0)
    var_list = netsnmp.VarList()
    var_list.append(netsnmp.Varbind('.1.3.6.1.2.1.1.3.0'))  #sysUptime
    var_list.append(netsnmp.Varbind('.1.3.6.1.2.1.1.5.0'))  #sysName
    var_list.append(netsnmp.Varbind('.1.3.6.1.2.1.1.1.0'))  #SysDesc
    var_list.append(netsnmp.Varbind('.1.3.6.1.2.1.1.6.0'))  #sysLocation
    result = session.get(var_list)
    return jsonify(result), {'Cache-Control': 'max-age=300'}
'''