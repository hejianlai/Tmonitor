# coding:utf8
from . import api, db
from decorators import permission_required
from sqlalchemy import distinct
from flask import jsonify, request
from time import localtime, strftime, time
import json, IPy


#   游戏IP表
class GameDestIp(db.Model):
    __tablename__ = 'game_destip'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("name", db.String)
    ip = db.Column("ip", db.String)
    ip_range = db.Column("ip_range", db.String)
    datetime = db.Column("datetime", db.String)

    def __init__(self, name, ip, ip_range, datetime):
        self.name = name
        self.ip = ip
        self.ip_range = ip_range
        self.datetime = datetime


#   游戏目标IP流量表
class GameDestIpAnalysis(db.Model):
    __tablename__ = 'game_destip_analysis'

    id = db.Column(db.Integer, primary_key=True)
    destip = db.Column("destip", db.String)
    rsize = db.Column("rsize", db.BigInteger)
    tsize = db.Column("tsize", db.BigInteger)
    datetime = db.Column("datetime", db.String)


#   游戏源IP流量表
class GameSourceIpAnalysis(db.Model):
    __tablename__ = 'game_sourceip_analysis'

    id = db.Column(db.Integer, primary_key=True)
    sourceip = db.Column("sourceip", db.String)
    rsize = db.Column("rsize", db.BigInteger)
    tsize = db.Column("tsize", db.BigInteger)
    datetime = db.Column("datetime", db.String)


#   IP区域表（暂时不用）
class IpRegion(db.Model):
    __tablename__ = 'ip_region'

    id = db.Column(db.Integer, primary_key=True)
    ip_interval = db.Column("ip_interval", db.String)
    region = db.Column("region", db.String)


#   游戏流量分析（五元组）
class GameFlowAnalysis(db.Model):
    __tablename__ = 'game_flow_analysis'

    id = db.Column(db.Integer, primary_key=True)
    sourceip = db.Column("sourceip", db.String)
    destip = db.Column("destip", db.String)
    flow = db.Column("flow", db.Integer)
    datetime = db.Column("datetime", db.String)
    source_region = db.Column("source_region", db.String)
    operator = db.Column("operator", db.String)

    def __init__(self, sourceip, destip, flow, datetime, source_region, operator):
        self.sourceip = sourceip
        self.destip = destip
        self.flow = flow
        self.datetime = datetime
        self.source_region = source_region
        self.operator = operator


#   用户->游戏流向流量表（暂时不用）
class GameUserAnalysis(db.Model):
    __tablename__ = 'game_user_analysis'

    id = db.Column(db.Integer, primary_key=True)
    sourceip = db.Column("sourceip", db.String)
    destip = db.Column("destip", db.String)
    flow = db.Column("flow", db.Integer)
    datetime = db.Column("datetime", db.String)

    def __init__(self, sourceip, destip, flow, datetime):
        self.sourceip = sourceip
        self.destip = destip
        self.flow = flow
        self.datetime = datetime


#   IP库
class MsIpLib(db.Model):
    __tablename__ = 'ms_ip_lib'

    id = db.Column(db.Integer, primary_key=True)
    min = db.Column("min", db.String)
    max = db.Column("max", db.String)
    mask = db.Column("mask", db.String)
    mask_size = db.Column("mask_size", db.Integer)
    operator = db.Column("operator", db.String)
    province = db.Column("province", db.String)
    city = db.Column("city", db.String)


#   根据条件查找游戏列表
@api.route("/games")
@permission_required(["GAME"])
def games_findAll(user):
    page = request.args.get("page")
    size = request.args.get("size")
    name = request.args.get("name")
    if page:
        page = int(page)
    else:
        page = 1
    if size:
        size = int(size)
    else:
        size = 10
    MyGameDestIp = type('MyGameDestIp_'+str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    games = db.session.query(distinct(MyGameDestIp.name))
    if name:
        games = games.filter(MyGameDestIp.name.ilike('%' + name + '%'))
    games = games.order_by(MyGameDestIp.name).paginate(page, size)
    content = []
    for temp in games.items:
        content.append(temp[0])
    return jsonify({'content': content, 'totalElements': games.total})


#   游戏目标IP分析（暂时不用，保留）
@api.route("/games/analysis")
@permission_required(["GAME"])
def games_analysis(user):
    page = request.args.get("page")
    size = request.args.get("size")
    name = request.args.get('name')
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    if page:
        page = int(page)
    if size:
        size = int(size)
    MyGameDestIp = type('GameDestIp_'+str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    MyGameDestIpAnalysis = type('GameDestIpAnalysis_'+str(user.dbname), (GameDestIpAnalysis,), {'__bind_key__': user.dbname})
    analysises = db.session.query(MyGameDestIp.name, db.func.sum(MyGameDestIpAnalysis.rsize),
                                  db.func.sum(MyGameDestIpAnalysis.tsize),
                                  db.func.sum(MyGameDestIpAnalysis.rsize + MyGameDestIpAnalysis.tsize).label("sum")). \
        select_from(MyGameDestIp).outerjoin(MyGameDestIpAnalysis, MyGameDestIp.ip == MyGameDestIpAnalysis.destip)
    if name:
        analysises = analysises.filter(MyGameDestIp.name.ilike('%' + name + '%'))
    if startTime:
        analysises = analysises.filter(MyGameDestIpAnalysis.datetime >= startTime)
    if endTime:
        analysises = analysises.filter(MyGameDestIpAnalysis.datetime <= endTime)
    analysises = analysises.group_by(MyGameDestIp.name).order_by(db.text("sum desc")).paginate(page, size)
    content = []
    for analysis in analysises.items:
        content.append({'name': analysis[0], 'rsize': changeUnit(analysis[1]), 'tsize': changeUnit(analysis[2]),
                        'sum': changeUnit(analysis[3])})
    return jsonify({'content': content, 'totalElements': analysises.total})


#   游戏目标IP分析（暂时不用，保留）->单个游戏流量分析
@api.route("/games/ipAnalysis")
@permission_required(["GAME"])
def games_ipAnalysis(user):
    name = request.args.get('name')
    top = request.args.get('top')
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    MyGameDestIp = type('GameDestIp_'+str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    MyGameDestIpAnalysis = type('GameDestIpAnalysis_'+str(user.dbname), (GameDestIpAnalysis,),
                                {'__bind_key__': user.dbname})
    analysises = db.session.query(MyGameDestIp.ip, db.func.sum(MyGameDestIpAnalysis.rsize),
                                  db.func.sum(MyGameDestIpAnalysis.tsize),
                                  db.func.sum(MyGameDestIpAnalysis.rsize + MyGameDestIpAnalysis.tsize).label("sum")). \
        select_from(MyGameDestIp).outerjoin(MyGameDestIpAnalysis, MyGameDestIp.ip == MyGameDestIpAnalysis.destip).\
        filter(MyGameDestIp.name == name)
    if startTime:
        analysises = analysises.filter(MyGameDestIpAnalysis.datetime >= startTime)
    if endTime:
        analysises = analysises.filter(MyGameDestIpAnalysis.datetime <= endTime)
    analysises = analysises.group_by(MyGameDestIp.ip).order_by(db.text("sum desc")).limit(top).all()
    result = []
    rank = 1
    for analysis in analysises:
        result.append({'rank': rank, 'ip': analysis[0], 'rsize': float(analysis[1]) if analysis[1] else '',
                       'tsize': float(analysis[2]) if analysis[2] else '',
                       'sum': float(analysis[3]) if analysis[3] else ''})
        rank = rank + 1
    return jsonify(result)


#   保存游戏目标IP
@api.route("/games/save", methods=['POST'])
@permission_required(["GAME"])
def games_save(user):
    data = json.loads(request.data)
    datetime = strftime('%Y%m%d%H%M%S', localtime(time()))
    data['datetime'] = datetime
    gamelist = []
    data['iplist'] = list(set(data['iplist']))
    data['iplist'].sort()
    MyGameDestIp = type('GameDestIp_'+str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    for ip in data['iplist']:
        temp_ip = ip.strip()
        temp_ip_range = temp_ip.split('.')
        temp_ip_range[3] = '0/24'
        temp_ip_range = '.'.join(temp_ip_range)
        game = MyGameDestIp(data['name'], ip.strip(), temp_ip_range, data['datetime'])
        gamelist.append(game)
    db.session.query(MyGameDestIp).filter(MyGameDestIp.name == data['name']).delete(synchronize_session=False)
    db.session.add_all(gamelist)
    db.session.commit()
    return ''


#   根据游戏名称查找游戏IP
@api.route("/games/findIpsByName")
@permission_required(["GAME"])
def games_findIpsByName(user):
    name = request.args.get('name')
    MyGameDestIp = type('GameDestIp_'+str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    iplist = db.session.query(distinct(MyGameDestIp.ip)).filter(MyGameDestIp.name == name).order_by(MyGameDestIp.ip).\
        all()
    result = []
    for ip in iplist:
        result.append(ip[0])
    return jsonify(result)


#   根据游戏名称删除游戏
@api.route("/games/byName", methods=['DELETE'])
@permission_required(["GAME"])
def games_deleteByName(user):
    name = request.args.get("name")
    MyGameDestIp = type('GameDestIp_'+str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    db.session.query(MyGameDestIp).filter(MyGameDestIp.name == name).delete()
    return ''


#   流量单位转换函数
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


#   保存游戏源IP
# @api.route("/games/saveSourceIp", methods=['POST'])
# @permission_required(["GAME"])
# def games_saveSourceIp(user):
#     data = json.loads(request.data)
#     datetime = strftime('%Y%m%d%H%M%S', localtime(time()))
#     data['datetime'] = datetime
#     gamelist = []
#     data['iplist'] = list(set(data['iplist']))
#     data['iplist'].sort()
#     MyGameSourceIp = type('GameSourceIp_'+str(user.dbname), (GameSourceIp,), {'__bind_key__': user.dbname})
#     for ip in data['iplist']:
#         game = MyGameSourceIp(data['name'], ip.strip(), '', '', '', '', data['datetime'])
#         gamelist.append(game)
#     db.session.query(MyGameSourceIp).filter(MyGameSourceIp.name == data['name']).delete(synchronize_session=False)
#     db.session.add_all(gamelist)
#     db.session.commit()
#     return ''


#   游戏源IP流量统计（暂时不用，保留）
@api.route("/games/sourceIpAnalysis")
@permission_required(["GAME"])
def games_sourceIpAnalysis(user):
    top = request.args.get('top')
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    MyGameSourceIpAnalysis = type('GameSourceIpAnalysis_'+str(user.dbname), (GameSourceIpAnalysis,),
                                  {'__bind_key__': user.dbname})
    analysises = db.session.query(MyGameSourceIpAnalysis.sourceip, db.func.sum(MyGameSourceIpAnalysis.rsize),
                                  db.func.sum(MyGameSourceIpAnalysis.tsize).label("tsize")).\
        select_from(MyGameSourceIpAnalysis)
    if startTime:
        analysises = analysises.filter(MyGameSourceIpAnalysis.datetime >= startTime)
    if endTime:
        analysises = analysises.filter(MyGameSourceIpAnalysis.datetime <= endTime)
    analysises = analysises.group_by(MyGameSourceIpAnalysis.sourceip).order_by(db.text("tsize desc")).limit(top).all()
    result = []
    rank = 1
    for analysis in analysises:
        result.append({'rank': rank, 'ip': analysis[0], 'rsize': float(analysis[1]) if analysis[1] else '',
                       'tsize': float(analysis[2]) if analysis[2] else ''})
        rank = rank + 1
    return jsonify(result)


#   游戏源IP区域统计（暂时不用，保留）
@api.route("/games/sourceIpRegionAnalysis")
@permission_required(["GAME"])
def games_sourceIpRegionAnalysis(user):
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    MyIpRegion = type('IpRegion_' + str(user.dbname), (IpRegion,), {'__bind_key__': user.dbname})
    ip_regions = MyIpRegion.query.all()
    MyGameSourceIpAnalysis = type('GameSourceIpAnalysis_'+str(user.dbname), (GameSourceIpAnalysis,),
                                  {'__bind_key__': user.dbname})
    sourceips = db.session.query(db.distinct(MyGameSourceIpAnalysis.sourceip)).\
        filter(MyGameSourceIpAnalysis.datetime >= startTime).filter(MyGameSourceIpAnalysis.datetime <= endTime).all()
    ip_stat = {}
    ipCount = len(sourceips)
    other = 0
    for sourceip in sourceips:
        for ip_region in ip_regions:
            if sourceip[0] in IPy.IP(ip_region.ip_interval):
                other += 1
                if ip_stat.has_key(ip_region.region):
                    ip_stat[ip_region.region] += 1
                else:
                    ip_stat[ip_region.region] = 1
    regionlist = sorted(ip_stat.items(), key=lambda x: -x[1])
    other = ipCount - other
    regionlist.append(['其他', other])
    return jsonify({'regionlist': regionlist, 'ipCount': ipCount})


#   游戏分析（五元组）
@api.route("/games/flow")
@permission_required(["GAME"])
def games_flow(user):
    page = request.args.get("page")
    size = request.args.get("size")
    name = request.args.get('name')
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    if page:
        page = int(page)
    else:
        page = 1
    if size:
        size = int(size)
    else:
        size = 10
    MyGameDestIp = type('GameDestIp_'+str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    MyGameFlowAnalysis = type('GameFlowAnalysis_'+str(user.dbname), (GameFlowAnalysis,), {'__bind_key__': user.dbname})
    analysises = db.session.query(MyGameDestIp.name, db.func.sum(MyGameFlowAnalysis.flow).label("flow")). \
        select_from(MyGameDestIp).outerjoin(MyGameFlowAnalysis, MyGameDestIp.ip == MyGameFlowAnalysis.sourceip)
    if name:
        analysises = analysises.filter(MyGameDestIp.name.ilike('%' + name + '%'))
    if startTime:
        analysises = analysises.filter(MyGameFlowAnalysis.datetime >= startTime)
    if endTime:
        analysises = analysises.filter(MyGameFlowAnalysis.datetime <= endTime)
    analysises = analysises.group_by(MyGameDestIp.name).order_by(db.text("flow desc")).paginate(page, size)
    content = []
    for analysis in analysises.items:
        content.append({'name': analysis[0], 'flow': changeUnit(analysis[1])})
    return jsonify({'content': content, 'totalElements': analysises.total}), {'Cache-Control': 'max-age=300'}


#   游戏分析（五元组）->单个游戏流量分析
@api.route("/games/flowAnalysis")
@permission_required(["GAME"])
def games_flowAnalysis(user):
    name = request.args.get('name')
    top = request.args.get('top')
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    MyGameDestIp = type('GameDestIp_' + str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    MyGameFlowAnalysis = type('GameFlowAnalysis_'+str(user.dbname), (GameFlowAnalysis,),
                                  {'__bind_key__': user.dbname})
    analysises = db.session.query(MyGameDestIp.ip_range, db.func.sum(MyGameFlowAnalysis.flow).label("flow")).\
        select_from(MyGameDestIp).outerjoin(MyGameFlowAnalysis, MyGameDestIp.ip == MyGameFlowAnalysis.sourceip).\
        filter(MyGameDestIp.name == name)
    if startTime:
        analysises = analysises.filter(MyGameFlowAnalysis.datetime >= startTime)
    if endTime:
        analysises = analysises.filter(MyGameFlowAnalysis.datetime <= endTime)
    analysises = analysises.group_by(MyGameDestIp.ip_range).order_by(db.text("flow desc")).limit(top).all()
    result = []
    rank = 1
    for analysis in analysises:
        result.append({'rank': rank, 'ip_range': analysis[0], 'flow': float(analysis[1]) if analysis[1] else ''})
        rank = rank + 1
    return jsonify(result), {'Cache-Control': 'max-age=300'}


#   游戏分析（五元组）->单个游戏流量区域统计
@api.route("/games/ipRegionAnalysis")
@permission_required(["GAME"])
def games_ipRegionAnalysis(user):
    name = request.args.get('name')
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    MyIpRegion = type('IpRegion_' + str(user.dbname), (IpRegion,), {'__bind_key__': user.dbname})
    ip_regions = MyIpRegion.query.all()
    MyGameDestIp = type('GameDestIp_' + str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    MyGameUserAnalysis = type('GameUserAnalysis_'+str(user.dbname), (GameUserAnalysis,),
                                  {'__bind_key__': user.dbname})
    userFlows = db.session.query(MyGameUserAnalysis.sourceip, db.func.sum(MyGameUserAnalysis.flow)). \
        select_from(MyGameDestIp).outerjoin(MyGameUserAnalysis, MyGameDestIp.ip == MyGameUserAnalysis.destip).\
        filter(MyGameDestIp.name == name).filter(MyGameUserAnalysis.datetime >= startTime).\
        filter(MyGameUserAnalysis.datetime <= endTime).group_by(MyGameUserAnalysis.sourceip)
    userFlows = userFlows.all()
    ip_stat = {}
    for userFlow in userFlows:
        for ip_region in ip_regions:
            if userFlow[0] in IPy.IP(ip_region.ip_interval):
                if ip_stat.has_key(ip_region.region):
                    ip_stat[ip_region.region] += float(userFlow[1])
                else:
                    ip_stat[ip_region.region] = float(userFlow[1])
    regionlist = sorted(ip_stat.items(), key=lambda x: -x[1])
    return jsonify({'regionlist': regionlist}), {'Cache-Control': 'max-age=300'}


#   游戏分析（区域统计），取前10区域
@api.route("/games/regionAnalysis")
@permission_required(["GAME"])
def games_regionAnalysis(user):
    time = request.args.get('time')
    top = request.args.get('top')
    if not top:
        top = 10
    MyGameFlowAnalysis = type('GameFlowAnalysis_' + str(user.dbname), (GameFlowAnalysis,),
                              {'__bind_key__': user.dbname})
    MyMsIpLib = type('MsIpLib_' + str(user.dbname), (MsIpLib,), {'__bind_key__': user.dbname})
    iplist = db.session.query(db.func.sum(MyGameFlowAnalysis.flow), MyGameFlowAnalysis.sourceip).\
        filter(db.func.left(MyGameFlowAnalysis.datetime, 8) == time).group_by(MyGameFlowAnalysis.sourceip).\
        order_by(db.func.sum(MyGameFlowAnalysis.flow).desc()).limit(top).all()
    data = {}
    for ip in iplist:
        regionlist = db.session.query(MyMsIpLib.province, MyMsIpLib.city, db.func.max(MyMsIpLib.mask_size)).\
            filter(db.func.inet_aton(MyMsIpLib.min) <= db.func.inet_aton(ip[1])).\
            filter(db.func.inet_aton(MyMsIpLib.max) >= db.func.inet_aton(ip[1]))
        regionlist = regionlist.all()
        region = regionlist[0][0]
        if not region:
            region = '其他'
        if regionlist[0][0] != regionlist[0][1]:
            region += regionlist[0][1]
        if not data.has_key(region):
            data[region] = {}
            data[region]['iplist'] = []
            data[region]['flow'] = 0
        data[region]['iplist'].append(ip[1])
        data[region]['flow'] += float(ip[0])
    result = []
    sorted_result = sorted(data.items(), key=lambda x: x[1]['flow'], reverse=True)
    for temp in sorted_result:
        temp_result = {}
        temp_result['region'] = temp[0]
        temp_result['flow'] = changeUnit(temp[1]['flow'])
        temp_result['iplist'] = ','.join(temp[1]['iplist'])
        result.append(temp_result)
    return jsonify(result)


#   获取某区域top10流量游戏
@api.route("/games/regionTopGames")
@permission_required(["GAME"])
def games_regionTopGames(user):
    iplist = request.args.get('iplist').split(',')
    time = request.args.get('time')
    MyGameDestIp = type('GameDestIp_' + str(user.dbname), (GameDestIp,), {'__bind_key__': user.dbname})
    MyGameFlowAnalysis = type('GameFlowAnalysis_' + str(user.dbname), (GameFlowAnalysis,),
                              {'__bind_key__': user.dbname})
    data = db.session.query(db.func.sum(MyGameFlowAnalysis.flow), MyGameDestIp.name).select_from(MyGameFlowAnalysis). \
        outerjoin(MyGameDestIp, MyGameFlowAnalysis.destip == MyGameDestIp.ip).\
        filter(MyGameFlowAnalysis.sourceip.in_(iplist)).filter(MyGameDestIp.name.isnot(None)).\
        filter(db.func.left(MyGameFlowAnalysis.datetime, 8) == time).\
        group_by(MyGameDestIp.name).order_by(db.func.sum(MyGameFlowAnalysis.flow).desc()).limit(10).all()
    content = []
    unit = 'KB'
    fenmu = 1024
    if data:
        max = float(data[0][0])
        if max > 1024 * 1024 * 1024 * 1024:
            fenmu = 1024 * 1024 * 1024 * 1024
            unit = 'TB'
        elif max > 1024 * 1024 * 1024:
            fenmu = 1024 * 1024 * 1024
            unit = 'GB'
        elif max > 1024 * 1024:
            fenmu = 1024 * 1024
            unit = 'MB'
    for temp in data:
        content.append({'flow': round(float(temp[0]) / fenmu, 2), 'game': temp[1]})
    return jsonify({'content': content, 'unit': unit})


#   获取某区域前一周流量趋势
@api.route("/games/regionWeekTrend")
@permission_required(["GAME"])
def games_regionWeekTrend(user):
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    iplist = request.args.get('iplist').split(',')
    MyGameFlowAnalysis = type('GameFlowAnalysis_' + str(user.dbname), (GameFlowAnalysis,),
                              {'__bind_key__': user.dbname})
    data = db.session.query(db.func.sum(MyGameFlowAnalysis.flow),
                            db.func.left(MyGameFlowAnalysis.datetime, 8)).\
        filter(MyGameFlowAnalysis.sourceip.in_(iplist)).\
        filter(db.func.left(MyGameFlowAnalysis.datetime, 8) >= startTime).\
        filter(db.func.left(MyGameFlowAnalysis.datetime, 8) <= endTime).\
        group_by(db.func.left(MyGameFlowAnalysis.datetime, 8)).all()
    content = []
    unit = 'KB'
    fenmu = 1024
    if data:
        max = float(data[0][0])
        if max > 1024 * 1024 * 1024 * 1024:
            fenmu = 1024 * 1024 * 1024 * 1024
            unit = 'TB'
        elif max > 1024 * 1024 * 1024:
            fenmu = 1024 * 1024 * 1024
            unit = 'GB'
        elif max > 1024 * 1024:
            fenmu = 1024 * 1024
            unit = 'MB'
    for temp in data:
        content.append({'flow': round(float(temp[0]) / fenmu, 2), 'time': temp[1]})
    return jsonify({'content': content, 'unit': unit})


#   游戏分析（运营商），取前10运营商
@api.route("/games/operatorAnalysis")
@permission_required(["GAME"])
def games_operatorAnalysis(user):
    time = request.args.get('time')
    top = request.args.get('top')
    if not top:
        top = 10
    MyGameFlowAnalysis = type('GameFlowAnalysis_' + str(user.dbname), (GameFlowAnalysis,),
                              {'__bind_key__': user.dbname})
    MyMsIpLib = type('MsIpLib_' + str(user.dbname), (MsIpLib,), {'__bind_key__': user.dbname})
    iplist = db.session.query(db.func.sum(MyGameFlowAnalysis.flow), MyGameFlowAnalysis.sourceip). \
        filter(db.func.left(MyGameFlowAnalysis.datetime, 8) == time).group_by(MyGameFlowAnalysis.sourceip). \
        order_by(db.func.sum(MyGameFlowAnalysis.flow).desc()).limit(top).all()
    data = {}
    for ip in iplist:
        operatorlist = db.session.query(MyMsIpLib.operator, db.func.max(MyMsIpLib.mask_size)). \
            filter(MyMsIpLib.min <= ip[1]).filter(MyMsIpLib.max >= ip[1]).all()
        operator = operatorlist[0][0]
        if not operator:
            operator = '其他'
        if not data.has_key(operator):
            data[operator] = {}
            data[operator]['iplist'] = []
            data[operator]['flow'] = 0
        data[operator]['iplist'].append(ip[1])
        data[operator]['flow'] += float(ip[0])
    result = []
    sorted_result = sorted(data.items(), key=lambda x: x[1]['flow'], reverse=True)
    for temp in sorted_result:
        temp_result = {}
        temp_result['operator'] = temp[0]
        temp_result['flow'] = changeUnit(temp[1]['flow'])
        temp_result['iplist'] = ','.join(temp[1]['iplist'])
        result.append(temp_result)
    return jsonify(result)


#   获取某运营商top10流量区域
@api.route("/games/operatorTopRegions")
@permission_required(["GAME"])
def games_operatorTopRegions(user):
    time = request.args.get('time')
    top = request.args.get('top')
    iplist = request.args.get('iplist').split(',')
    MyGameFlowAnalysis = type('GameFlowAnalysis_' + str(user.dbname), (GameFlowAnalysis,),
                              {'__bind_key__': user.dbname})
    MyMsIpLib = type('MsIpLib_' + str(user.dbname), (MsIpLib,), {'__bind_key__': user.dbname})
    flow_ip = db.session.query(db.func.sum(MyGameFlowAnalysis.flow), MyGameFlowAnalysis.sourceip). \
        filter(db.func.left(MyGameFlowAnalysis.datetime, 8) == time).\
        filter(MyGameFlowAnalysis.sourceip.in_(iplist)).group_by(MyGameFlowAnalysis.sourceip). \
        order_by(db.func.sum(MyGameFlowAnalysis.flow).desc()).limit(top).all()
    data = {}
    for ip in flow_ip:
        regionlist = db.session.query(MyMsIpLib.province, MyMsIpLib.city, db.func.max(MyMsIpLib.mask_size)). \
            filter(MyMsIpLib.min <= ip[1]).filter(MyMsIpLib.max >= ip[1]).all()
        region = regionlist[0][0]
        if not region:
            region = '其他'
        if regionlist[0][0] != regionlist[0][1]:
            region += regionlist[0][1]
        if not data.has_key(region):
            data[region] = {}
            data[region]['flow'] = 0
        data[region]['flow'] += float(ip[0])
    result = []
    sorted_result = sorted(data.items(), key=lambda x: x[1]['flow'], reverse=True)
    content = []
    unit = 'KB'
    fenmu = 1024
    if data:
        max = float(sorted_result[0][1]['flow'])
        if max > 1024 * 1024 * 1024 * 1024:
            fenmu = 1024 * 1024 * 1024 * 1024
            unit = 'TB'
        elif max > 1024 * 1024 * 1024:
            fenmu = 1024 * 1024 * 1024
            unit = 'GB'
        elif max > 1024 * 1024:
            fenmu = 1024 * 1024
            unit = 'MB'
    for temp in sorted_result:
        content.append({'flow': round(float(temp[1]['flow']) / fenmu, 2), 'region': temp[0]})
    return jsonify({'content': content, 'unit': unit})


#   获取某运营商前一周流量趋势
@api.route("/games/operatorWeekTrend")
@permission_required(["GAME"])
def games_operatorWeekTrend(user):
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    iplist = request.args.get('iplist').split(',')
    MyGameFlowAnalysis = type('GameFlowAnalysis_' + str(user.dbname), (GameFlowAnalysis,),
                              {'__bind_key__': user.dbname})
    data = db.session.query(db.func.sum(MyGameFlowAnalysis.flow),
                            db.func.left(MyGameFlowAnalysis.datetime, 8)). \
        filter(MyGameFlowAnalysis.sourceip.in_(iplist)). \
        filter(db.func.left(MyGameFlowAnalysis.datetime, 8) >= startTime). \
        filter(db.func.left(MyGameFlowAnalysis.datetime, 8) <= endTime).\
        group_by(db.func.left(MyGameFlowAnalysis.datetime, 8)).all()
    content = []
    unit = 'KB'
    fenmu = 1024
    if data:
        max = float(data[0][0])
        if max > 1024 * 1024 * 1024 * 1024:
            fenmu = 1024 * 1024 * 1024 * 1024
            unit = 'TB'
        elif max > 1024 * 1024 * 1024:
            fenmu = 1024 * 1024 * 1024
            unit = 'GB'
        elif max > 1024 * 1024:
            fenmu = 1024 * 1024
            unit = 'MB'
    for temp in data:
        content.append({'flow': round(float(temp[0]) / fenmu, 2), 'time': temp[1]})
    return jsonify({'content': content, 'unit': unit})
