# coding:utf8
from flask import request, jsonify
from . import api, db
from .decorators import permission_required
import json


#   服务类型表
class Servertype(db.Model):
    __tablename__ = 'servertype'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("name", db.String)

    def __init__(self, name):
        self.name = name

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name
        }


#   获取所有服务类型列表
@api.route("/servertypes")
@permission_required([])
def servertypes_findAll(user):
    MyServertype = type('Servertype_' + str(user.dbname), (Servertype,), {'__bind_key__': user.dbname})
    servertypes = MyServertype.query.all()
    return jsonify([servertype.to_json() for servertype in servertypes])


#   新建服务类型
@api.route("/servertypes/save", methods=['POST'])
@permission_required(["SERVERTYPE"])
def servertypes_save(user):
    data = json.loads(request.data)
    MyServertype = type('Servertype_' + str(user.dbname), (Servertype,), {'__bind_key__': user.dbname})
    servertype = MyServertype(data['name'])
    db.session.add(servertype)
    db.session.commit()
    return ''


#   根据ID更新服务类型
@api.route("/servertypes/<int:servertypeId>", methods=['PUT'])
@permission_required(["SERVERTYPE"])
def servertypes_updateById(user, servertypeId):
    MyServertype = type('Servertype_' + str(user.dbname), (Servertype,), {'__bind_key__': user.dbname})
    servertype = MyServertype.query.get(servertypeId)
    if not servertype:
        return jsonify({'error': "invalid servertypeId"}), 500
    name = request.json.get("name")
    if name:
        servertype.name = name
    db.session.commit()
    return ''


#   根据ID查找服务类型
@api.route("/servertypes/<int:servertypeId>")
@permission_required(["SERVERTYPE"])
def servertypes_findById(user, servertypeId):
    MyServertype = type('Servertype_' + str(user.dbname), (Servertype,), {'__bind_key__': user.dbname})
    servertype = MyServertype.query.get(servertypeId)
    return jsonify(servertype.to_json())


#   根据ID删除服务类型
@api.route("/servertypes/<int:servertypeId>", methods=['DELETE'])
@permission_required(["SERVERTYPE"])
def servertypes_deleteById(user, servertypeId):
    MyServertype = type('Servertype_' + str(user.dbname), (Servertype,), {'__bind_key__': user.dbname})
    db.session.query(MyServertype).filter(MyServertype.id == servertypeId).delete()
    return ''
