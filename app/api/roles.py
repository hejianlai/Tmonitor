# coding:utf8
from flask import request, jsonify
from . import db, api
from .decorators import permission_required
from .permissions import Permission
import json

role_permission = db.Table('sys_role_permission',
                           db.Column('rid', db.Integer, db.ForeignKey('sys_role.id')),
                           db.Column('pid', db.Integer, db.ForeignKey('sys_permission.id'))
                           )


#   角色表
class Role(db.Model):
    __tablename__ = "sys_role"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    memo = db.Column(db.String)
    permissions = db.relationship('Permission',
                                  secondary=role_permission,
                                  backref=db.backref('sys_permission', lazy='dynamic'),
                                  lazy='dynamic')

    def __init__(self, name, memo):
        self.name = name
        self.memo = memo

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'memo': self.memo
        }


# 获取所有角色列表
@api.route("/roles")
@permission_required(["ROLE"])
def roles_findAll(user):
    roles = Role.query.all()
    result = [role.to_json() for role in roles]
    return jsonify(result)


# 新建角色
@api.route("/roles/save", methods=['POST'])
@permission_required(["ROLE"])
def roles_save(user):
    data = json.loads(request.data)
    role = Role(data['name'], data['memo'])
    db.session.add(role)
    db.session.commit()
    return ''


# 角色赋权
@api.route("/roles/grant/<int:roleId>", methods=['PUT'])
@permission_required(["ROLE"])
def roles_grant(user, roleId):
    permissions = request.args.get("permissionIds")
    permissionArr = permissions.split(",")
    role = Role.query.get(roleId)
    permissionList = []
    for index in range(len(permissionArr)):
        permissionList.append(Permission.query.get(permissionArr[index]))
    role.permissions = permissionList
    db.session.commit()
    return ''


# 根据角色ID获取角色权限ID
@api.route("/roles/permissions/<int:roleId>")
@permission_required(["ROLE"])
def roles_permissions(user, roleId):
    role = Role.query.get(roleId)
    permissions = role.permissions.all()
    result = []
    for permission in permissions:
        result.append(permission.id)
    return jsonify(result)
