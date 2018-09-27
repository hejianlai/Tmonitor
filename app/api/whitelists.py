# coding:utf8
from flask import request, jsonify
from . import api, db
from .decorators import permission_required
from time import localtime, strftime, time
import json


#   白名单表
class Whitelist(db.Model):
    __tablename__ = 'whitelist'

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column("ip", db.String)
    datetime = db.Column("datetime", db.String)

    def __init__(self, ip, datetime):
        self.ip = ip
        self.datetime = datetime

    def to_json(self):
        return {
            'id': self.id,
            'ip': self.ip,
            'datetime': "{0}-{1}-{2} {3}:{4}:{5}".format(self.datetime[0:4], self.datetime[4:6],
                                                         self.datetime[6:8], self.datetime[8:10],
                                                         self.datetime[10:12], self.datetime[12:14])
        }


#   根据条件查找白名单列表
@api.route("/whitelists/findByConditions")
@permission_required(["WHITELIST"])
def whitelists_findByConditions(user):
    ip = request.args.get("ip")
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
    MyWhitelist = type('Whitelist_' + str(user.dbname), (Whitelist,), {'__bind_key__': user.dbname})
    whitelists = MyWhitelist.query
    if ip:
        whitelists = whitelists.filter(MyWhitelist.ip.ilike("%"+ip+"%"))
    whitelists = whitelists.paginate(page, size)
    result = {}
    result["content"] = [whitelist.to_json() for whitelist in whitelists.items]
    result["totalElements"] = whitelists.total
    return jsonify(result)


#   新建白名单
@api.route("/whitelists/save", methods=['POST'])
@permission_required(["WHITELIST"])
def whitelists_save(user):
    data = json.loads(request.data)
    datetime = strftime('%Y%m%d%H%M%S', localtime(time()))
    data['datetime'] = datetime
    MyWhitelist = type('Whitelist_' + str(user.dbname), (Whitelist,), {'__bind_key__': user.dbname})
    whitelist = MyWhitelist(data['ip'], data['datetime'])
    db.session.add(whitelist)
    db.session.commit()
    return ''


#   根据ID编辑白名单
@api.route("/whitelists/<int:whitelistId>", methods=['PUT'])
@permission_required(["WHITELIST"])
def whitelists_updateById(user, whitelistId):
    MyWhitelist = type('Whitelist_' + str(user.dbname), (Whitelist,), {'__bind_key__': user.dbname})
    whitelist = MyWhitelist.query.get(whitelistId)
    if not whitelist:
        return jsonify({'error': "invalid permissionId"}), 500
    ip = request.json.get("ip")
    if ip:
        whitelist.ip = ip
    db.session.commit()
    return ''


#   根据ID查找白名单
@api.route("/whitelists/<int:whitelistId>")
@permission_required(["WHITELIST"])
def whitelists_findById(user, whitelistId):
    MyWhitelist = type('Whitelist_' + str(user.dbname), (Whitelist,), {'__bind_key__': user.dbname})
    whitelist = MyWhitelist.query.get(whitelistId)
    return jsonify(whitelist.to_json())


#   根据ID删除白名单
@api.route("/whitelists/<int:whitelistId>", methods=['DELETE'])
@permission_required(["WHITELIST"])
def whitelists_deleteById(user, whitelistId):
    MyWhitelist = type('Whitelist_' + str(user.dbname), (Whitelist,), {'__bind_key__': user.dbname})
    db.session.query(MyWhitelist).filter(MyWhitelist.id == whitelistId).delete()
    return ''
