# coding:utf8
from flask import jsonify, request
from sqlalchemy import text
from . import db, api
from .decorators import permission_required
import json, time


#   权限表
class Permission(db.Model):
    __tablename__ = "sys_permission"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    code = db.Column(db.String)
    memo = db.Column(db.String)
    type = db.Column(db.Integer)
    level = db.Column(db.Integer)
    pid = db.Column(db.Integer)
    datetime = db.Column(db.String)

    def __init__(self, name, code, memo, type1, level, pid, datetime):
        self.name = name
        self.code = code
        self.memo = memo
        self.type = type1
        self.level = level
        self.pid = pid
        self.datetime = datetime

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'memo': self.memo,
            'type': self.type,
            'level': self.level,
            'pid': self.pid,
            'datetime': "{0}-{1}-{2} {3}:{4}:{5}".format(self.datetime[0:4], self.datetime[4:6],
                                                         self.datetime[6:8], self.datetime[8:10],
                                                         self.datetime[10:12], self.datetime[12:14])
        }


#   获取所有权限
@api.route("/permissions")
@permission_required(["PERMISSION"])
def permissions_findAll(user):
    tops = Permission.query.filter(text("pid is null")).all()
    permissions = []
    for top in tops:
        permissions.append(top)
        seconds = Permission.query.filter_by(pid=top.id).all()
        if seconds:
            for second in seconds:
                permissions.append(second)
                thirds = Permission.query.filter_by(pid=second.id).all()
                if thirds:
                    for third in thirds:
                        permissions.append(third)
                        fourths = Permission.query.filter_by(pid=third.id).all()
                        if fourths:
                            for fourth in fourths:
                                permissions.append(fourth)
    result = [permission.to_json() for permission in permissions]
    return jsonify(result)


#   新建权限->父级菜单下拉框
@api.route("/permissions/findForSelector")
@permission_required(["PERMISSION"])
def permissions_findForSelector(user):
    tops = Permission.query.filter("pid is null").all()
    permissions = []
    for top in tops:
        permissions.append(top)
        seconds = Permission.query.filter_by(pid=top.id).filter_by(type=0).all()
        if seconds:
            for second in seconds:
                permissions.append(second)
                thirds = Permission.query.filter_by(pid=second.id).filter_by(type=0).all()
                if thirds:
                    for third in thirds:
                        permissions.append(third)
                        fourths = Permission.query.filter_by(pid=third.id).filter_by(type=0).all()
                        if fourths:
                            for fourth in fourths:
                                permissions.append(fourth)
    result = [permission.to_json() for permission in permissions]
    return jsonify(result)


#   编辑权限->父级菜单下拉框
@api.route("/permissions/findForEdit/<int:permissionId>")
@permission_required(["PERMISSION"])
def permissions_findForEdit(user, permissionId):
    tops = Permission.query.filter(text("pid is null"), Permission.id != permissionId).all()
    permissions = []
    for top in tops:
        permissions.append(top)
        seconds = Permission.query.filter(Permission.id != permissionId).filter_by(pid=top.id).filter_by(type=0).all()
        if seconds:
            for second in seconds:
                permissions.append(second)
                thirds = Permission.query.filter(Permission.id != permissionId).filter_by(pid=second.id).filter_by(type=0).all()
                if thirds:
                    for third in thirds:
                        permissions.append(third)
                        fourths = Permission.query.filter(Permission.id != permissionId).filter_by(pid=third.id).\
                            filter_by(type=0).all()
                        if fourths:
                            for fourth in fourths:
                                permissions.append(fourth)
    result = [permission.to_json() for permission in permissions]
    return jsonify(result)


#   新建权限
@api.route("/permissions/save", methods=['POST'])
@permission_required(["PERMISSION"])
def permissions_save(user):
    data = json.loads(request.data)
    if data['pid']:
        parent = Permission.query.filter_by(id=data['pid']).first()
        data['level'] = parent.level + 1
    datetime = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    data['datetime'] = datetime
    permission = Permission(data['name'], data['code'], data['memo'], data['type'], data['level'], data['pid'],
                            data['datetime'])
    db.session.add(permission)
    db.session.commit()
    return ''


#   根据ID删除权限
@api.route("/permissions/<int:permissionId>", methods=['DELETE'])
@permission_required(["PERMISSION"])
def permissions_deleteById(user, permissionId):
    db.session.query(Permission).filter(Permission.id == permissionId).delete()
    return ''


#   根据ID更新权限
@api.route("/permissions/<int:permissionId>", methods=['PUT'])
@permission_required(["PERMISSION"])
def permissions_updateById(user, permissionId):
    permission = Permission.query.get(permissionId)
    if not permission:
        return jsonify({'error': "invalid permissionId"}), 500
    name = request.json.get("name")
    code = request.json.get("code")
    memo = request.json.get("memo")
    type1 = request.json.get("type")
    pid = request.json.get("pid")
    if name:
        permission.name = name
    if code:
        permission.code = code
    if memo:
        permission.memo = memo
    if type:
        permission.type = type1
    if pid and pid != permission.pid:
        permission.pid = pid
        parent = Permission.query.get(pid)
        permission.level = parent.level + 1
    db.session.commit()
    return ''


#   根据ID查找权限
@api.route("/permissions/<int:permissionId>")
@permission_required(["PERMISSION"])
def permissions_findById(user, permissionId):
    permission = Permission.query.get(permissionId)
    return jsonify(permission.to_json())
