# coding:utf8
from flask import request, jsonify
from . import api, db
from .decorators import permission_required
from .server_types import Servertype
from time import localtime, strftime, time
import json


#   设备管理表
class Serverlist(db.Model):
    __tablename__ = 'serverlist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("name", db.String)
    ip = db.Column("ip", db.String)
    type = db.Column("type", db.Integer)
    model = db.Column("model", db.String)
    os = db.Column("os", db.String)
    mroom = db.Column("mroom", db.String)
    status = db.Column("status", db.Integer)
    datetime = db.Column("datetime", db.String)

    def __init__(self, name, ip, type1, model, os, mroom, status, datetime):
        self.name = name
        self.ip = ip
        self.type = type1
        self.model = model
        self.os = os
        self.mroom = mroom
        self.status = status
        self.datetime = datetime

    def to_json(self):
        servertype = Servertype.query.get(self.type)
        return {
            'id': self.id,
            'name': self.name,
            'ip': self.ip,
            'type': self.type,
            'typeName': servertype.name,
            'model': self.model,
            'os': self.os,
            'mroom': self.mroom,
            'status': self.status,
            'datetime': "{0}-{1}-{2} {3}:{4}:{5}".format(self.datetime[0:4], self.datetime[4:6],
                                                         self.datetime[6:8], self.datetime[8:10],
                                                         self.datetime[10:12], self.datetime[12:14])
        }


#   根据条件查找设备列表
@api.route("/serverlists/findByConditions")
@permission_required(["SERVERLIST"])
def serverlists_findByConditions(user):
    name = request.args.get("name")
    ip = request.args.get("ip")
    type1 = request.args.get("type")
    page = request.args.get("page")
    size = request.args.get("size")
    if page:
        page = int(page)
    else:
        page = 1
    if size:
        size = int(size)
    else:
        size = 10
    MyServerlist = type('Serverlist_' + str(user.dbname), (Serverlist,), {'__bind_key__': user.dbname})
    serverlists = MyServerlist.query
    if name:
        serverlists = serverlists.filter(MyServerlist.name.ilike("%"+name+"%"))
    if ip:
        serverlists = serverlists.filter(MyServerlist.ip.ilike("%"+ip+"%"))
    if type1:
        serverlists = serverlists.filter_by(type=type1)
    serverlists = serverlists.order_by(MyServerlist.name).paginate(page, size)
    result = {}
    result["content"] = [serverlist.to_json() for serverlist in serverlists.items]
    result["totalElements"] = serverlists.total
    return jsonify(result)


#   新建设备
@api.route("/serverlists/save", methods=['POST'])
@permission_required(["SERVERLIST"])
def serverlists_save(user):
    data = json.loads(request.data)
    datetime = strftime('%Y%m%d%H%M%S', localtime(time()))
    data['datetime'] = datetime
    MyServerlist = type('Serverlist_' + str(user.dbname), (Serverlist,), {'__bind_key__': user.dbname})
    serverlist = MyServerlist(data['name'], data['ip'], data['type'], data['model'], data['os'], data['mroom'],
                            data['status'], data['datetime'])
    db.session.add(serverlist)
    db.session.commit()
    return ''


#   根据ID更新设备信息
@api.route("/serverlists/<int:serverlistId>", methods=['PUT'])
@permission_required(["SERVERLIST"])
def serverlists_updateById(user, serverlistId):
    MyServerlist = type('Serverlist_' + str(user.dbname), (Serverlist,), {'__bind_key__': user.dbname})
    serverlist = MyServerlist.query.get(serverlistId)
    if not serverlist:
        return jsonify({'error': "invalid serverlistId"}), 500
    name = request.json.get("name")
    ip = request.json.get("ip")
    type1 = request.json.get("type")
    model = request.json.get("model")
    os = request.json.get("os")
    mroom = request.json.get("mroom")
    status = request.json.get("status")
    if name:
        serverlist.name = name
    if ip:
        serverlist.ip = ip
    if type1:
        serverlist.type = type1
    if model:
        serverlist.model = model
    if os:
        serverlist.os = os
    if mroom:
        serverlist.mroom = mroom
    if status:
        serverlist.status = status
    db.session.commit()
    return ''


#   根据ID查找设备列表
@api.route("/serverlists/<int:serverlistId>")
@permission_required(["SERVERLIST"])
def serverlists_findById(user, serverlistId):
    MyServerlist = type('Serverlist_' + str(user.dbname), (Serverlist,), {'__bind_key__': user.dbname})
    serverlist = MyServerlist.query.get(serverlistId)
    return jsonify(serverlist.to_json())


#   根据ID删除设备
@api.route("/serverlists/<int:serverlistId>", methods=['DELETE'])
@permission_required(["SERVERLIST"])
def serverlists_deleteById(user, serverlistId):
    MyServerlist = type('Serverlist_' + str(user.dbname), (Serverlist,), {'__bind_key__': user.dbname})
    db.session.query(MyServerlist).filter(MyServerlist.id == serverlistId).delete()
    return ''


#   获取设备名称列表
@api.route("/serverlists/findAll")
@permission_required(["SERVERLIST"])
def serverlists_findAll(user):
    MyServerlist = type('Serverlist_' + str(user.dbname), (Serverlist,), {'__bind_key__': user.dbname})
    serverlist = db.session.query(MyServerlist.name).order_by(MyServerlist.name).all()
    return jsonify(serverlist)
