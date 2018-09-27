# coding:utf8
from flask import jsonify, current_app, request
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer)
from .decorators import permission_required
from . import api, db
from .roles import Role
from .whitelists import Whitelist
from time import localtime, strftime, time
import json


#   用户表
class User(db.Model):
    __tablename__ = 'sys_user'

    id = db.Column(db.Integer, primary_key=True)
    loginName = db.Column("loginname", db.String)
    password = db.Column("password", db.String)
    name = db.Column("name", db.String)
    roleId = db.Column('rid', db.Integer)
    datetime = db.Column("datetime", db.String)
    dbname = db.Column("dbname", db.String)
    memo = db.Column("memo", db.String)

    def __init__(self, loginName, password, name, roleId, datetime, dbname, memo):
        self.loginName = loginName
        self.password = password
        self.name = name
        self.roleId = roleId
        self.datetime = datetime
        self.dbname = dbname
        self.memo = memo

    def to_json(self):
        role = Role.query.filter_by(id=self.roleId).first()
        roleName = role.name
        return {
            'id': self.id,
            'loginName': self.loginName,
            'name': self.name,
            'roleId': self.roleId,
            'roleName': roleName,
            'datetime': "{0}-{1}-{2} {3}:{4}:{5}".format(self.datetime[0:4], self.datetime[4:6],
                                                         self.datetime[6:8], self.datetime[8:10],
                                                         self.datetime[10:12], self.datetime[12:14]),
            'dbname': self.dbname,
            'memo': self.memo
        }

    def has_permissions(self, permissions):
        role = Role.query.get(self.roleId)
        if not role:
            return False
        user_permissions = []
        for permission in role.permissions:
            user_permissions.append(permission.code)
        for permission in permissions:
            if user_permissions.count(permission) <= 0:
                return False
        return True


@api.route("/token", methods=['POST'])
def get_auth_token():
    loginName = request.json.get('loginName')
    password = request.json.get('password')
    user = User.query.filter_by(loginName=loginName).first()
    if not user:
        return jsonify({"error": "invalid loginName"}), 401
    else:
        # MyWhitelist = type('Whitelist', (), {'__bind_key__': user.dbname})
        # whitelists = session.query(MyWhitelist).all()
        # session.close()
        # ip = request.remote_addr
        # flag = True
        # for whitelist in whitelists:
        #     if whitelist.ip == ip:
        #         flag = False
        #         break
        # if flag:
        #     return jsonify({"error": "invalid ip", "ip": ip}), 403
        if user.password == password:
            s = Serializer(current_app.config['SECRET_KEY'], expires_in=current_app.config['EXPIRATION'])
            token = s.dumps({'id': user.id}).decode('ascii')
            return jsonify({"token": token})
        else:
            return jsonify({"error": "invalid password"}), 401


#根据条件查找用户列表
@api.route("/users/findByConditions")
@permission_required(["USER"])
def users_findByConditions(user):
    loginName = request.args.get("loginName")
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
    users = User.query
    if loginName:
        users = users.filter(User.loginName.ilike("%"+loginName+"%"))
    users = users.paginate(page, size)
    result = {}
    result["content"] = [user.to_json() for user in users.items]
    result["totalElements"] = users.total
    return jsonify(result)


#新建用户
@api.route("/users/save", methods=['POST'])
@permission_required(["USER"])
def users_save(user):
    data = json.loads(request.data)
    datetime = strftime('%Y%m%d%H%M%S', localtime(time()))
    data['roleId'] = int(data['roleId'])
    data['datetime'] = datetime
    user = User(data['loginName'], data['password'], data['name'], data['roleId'], data['datetime'],
                data['dbname'], data['memo'])
    db.session.add(user)
    db.session.commit()
    return ''


#根据ID批量删除用户
@api.route("/users/byIds", methods=['DELETE'])
@permission_required(["USER"])
def users_deleteByIds(user):
    ids = request.args.get("ids")
    idlist = ids.split(",")
    db.session.query(User).filter(User.id.in_(idlist)).delete(synchronize_session=False)
    return ''


#检查登录名是否已存在
@api.route("/users/checkLoginNameExist")
@permission_required(["USER"])
def users_checkLoginNameExist(user):
    loginName = request.args.get("loginName")
    count = User.query.filter_by(loginName=loginName).count()
    return jsonify({'exist': count > 0})


#根据ID查找用户
@api.route("/users/<int:userId>")
@permission_required(["USER"])
def users_findById(user, userId):
    user = User.query.get(userId)
    return jsonify(user.to_json())


#根据ID更新用户信息
@api.route("/users/<int:userId>", methods=['PUT'])
@permission_required(["USER"])
def users_updateById(user, userId):
    user = User.query.get(userId)
    if not user:
        return jsonify({'error': "invalid userId"}), 500
    loginName = request.json.get("loginName")
    password = request.json.get("password")
    name = request.json.get("name")
    roleId = request.json.get("roleId")
    dbname = request.json.get("dbname")
    memo = request.json.get("memo")
    if loginName:
        user.loginName = loginName
    if password:
        user.password = password
    if name:
        user.name = name
    if roleId:
        user.roleId = roleId
    if dbname:
        user.dbname = dbname
    if memo:
        user.memo = memo
    db.session.commit()
    return ''


#获取当前用户权限列表
@api.route("/users/myPermissions")
@permission_required([])
def users_myPermissions(user):
    role = Role.query.get(user.roleId)
    permissions = role.permissions.all()
    result = []
    for permission in permissions:
        result.append(permission.code)
    return jsonify(result)


#获取当前用户信息
@api.route("/users/getCurrentUser")
@permission_required([])
def users_getCurrentUser(user):
    return jsonify(user.to_json())
