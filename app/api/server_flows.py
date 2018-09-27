#coding=utf8
from flask import request, jsonify
from . import api, db
from .decorators import permission_required
import time


class Serverflow(db.Model):
    __tablename__ = 'serverflow'

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column("ip", db.String)
    svrname = db.Column("svrname", db.String)
    datetime = db.Column("datetime", db.String)
    rrate = db.Column("rrate", db.Integer)
    trate = db.Column("trate", db.Integer)
    nic = db.Column("nic", db.String)

    def __init__(self, ip, svrname, datetime, rrate, trate, nic):
        self.ip = ip
        self.svrname = svrname
        self.datetime = datetime
        self.rrate = rrate
        self.trate = trate
        self.nic = nic

    def to_json(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'svrname': self.svrname,
            'datetime': self.datetime,
            'rrate': self.rrate,
            'trate': self.trate,
            'nic': self.nic
        }


@api.route("/serverflows")
@permission_required(["SERVERLIST"])
def serverflows_findAll(user):
    ip = request.args.get('ip')
    days = int(request.args.get('days'))
    #获取N天前的时间
    starttime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(time.time()) - days * 24 * 60 * 60))
    MyServerflow = type('Serverflow_' + str(user.dbname), (Serverflow,), {'__bind_key__': user.dbname})
    serverflows = MyServerflow.query.filter(MyServerflow.ip == ip).filter(MyServerflow.datetime > starttime).order_by(
        MyServerflow.nic, MyServerflow.datetime).all()
    result = []
    temp_nic = serverflows[0].nic
    temp_timestamp = serverflows[0].datetime
    temp_timestamp = "{0}-{1}-{2} {3}:{4}:{5}".format(temp_timestamp[0:4], temp_timestamp[4:6],
                                                      temp_timestamp[6:8], temp_timestamp[8:10],
                                                      temp_timestamp[10:12], temp_timestamp[12:14])
    # 转换成时间数组
    temp_timestamp = time.strptime(temp_timestamp, "%Y-%m-%d %H:%M:%S")
    # 转换成时间戳
    temp_timestamp = time.mktime(temp_timestamp)
    temp_rrate = []
    temp_trate = []
    maxrate = 0
    for serverflow in serverflows:
        #取某网卡速率峰值
        if maxrate < serverflow.rrate:
            maxrate = serverflow.rrate
        if maxrate < serverflow.trate:
            maxrate = serverflow.trate

        if temp_nic != serverflow.nic:
            fenmu = 1024
            unit = 'Kbps'
            if maxrate > 1024*1024*1024:
                fenmu = 1024*1024*1024
                unit = 'Gbps'
            elif maxrate > 1024*1024:
                fenmu = 1024*1024
                unit = 'Mbps'

            for index in range(len(temp_rrate)):
                if temp_rrate[index][1] != 'null':
                    temp_rrate[index][1] = round(temp_rrate[index][1] * 1.0 / fenmu, 2)
            for index in range(len(temp_trate)):
                if temp_trate[index][1] != 'null':
                    temp_trate[index][1] = round(temp_trate[index][1] * 1.0 / fenmu, 2)
            result.append({'nic': temp_nic, 'unit': unit, 'rrate': temp_rrate, 'trate': temp_trate})
            temp_nic = serverflow.nic
            temp_rrate = []
            temp_trate = []
            maxrate = 0
        dt = serverflow.datetime
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
                temp_rrate.append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 'null'])
                temp_trate.append([(temp_timestamp+i*5*60) * 1000 + 8 * 60 * 60 * 1000, 'null'])
        temp_rrate.append([timestamp*1000 + 8*60*60*1000, serverflow.rrate])
        temp_trate.append([timestamp*1000 + 8*60*60*1000, serverflow.trate])
        temp_timestamp = timestamp

    fenmu = 1024
    unit = 'Kbps'
    if maxrate > 1024 * 1024 * 1024:
        fenmu = 1024 * 1024 * 1024
        unit = 'Gbps'
    elif maxrate > 1024 * 1024:
        fenmu = 1024 * 1024
        unit = 'Mbps'

    for index in range(len(temp_rrate)):
        if temp_rrate[index][1] != 'null':
            temp_rrate[index][1] = round(temp_rrate[index][1] * 1.0 / fenmu, 2)
    for index in range(len(temp_trate)):
        if temp_trate[index][1] != 'null':
            temp_trate[index][1] = round(temp_trate[index][1] * 1.0 / fenmu, 2)
    result.append({'nic': temp_nic, 'unit': unit, 'rrate': temp_rrate, 'trate': temp_trate})
    return jsonify(result), {'Cache-Control': 'max-age=300'}
