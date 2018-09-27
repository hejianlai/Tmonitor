# coding:utf8
from flask import jsonify, request
from .decorators import permission_required
from . import api, db


#   域名访问信息表
class DomainStat(db.Model):
    __tablename__ = 'domain_stat'

    id = db.Column(db.Integer, primary_key=True)
    svrname = db.Column("svrname", db.String)
    domain = db.Column("domain", db.String)
    sum = db.Column("sum", db.BigInteger)
    hit = db.Column("hit", db.BigInteger)
    miss = db.Column("miss", db.BigInteger)
    size = db.Column("size", db.BigInteger)
    s_code_000 = db.Column("s_code_000", db.BigInteger)
    s_code_20x = db.Column("s_code_20x", db.BigInteger)
    s_code_30x = db.Column("s_code_30x", db.BigInteger)
    s_code_40x = db.Column("s_code_40x", db.BigInteger)
    s_code_50x = db.Column('s_code_50x', db.BigInteger)
    othercode = db.Column("othercode", db.BigInteger)
    resptime = db.Column("resptime", db.BigInteger)
    datetime = db.Column("datetime", db.String)


#   根据条件查找域名统计数据
@api.route("/domains/findByConditions")
@permission_required(["GAME"])
def domains_findByConditions(user):
    startTime = request.args.get('startTime')
    endTime = request.args.get('endTime')
    svrnameArr = request.args.get('svrnameArr')
    if svrnameArr:
        svrnameArr = svrnameArr.split(",")
    domain = request.args.get('domain')
    orderby = request.args.get('orderby')
    limitNum = request.args.get('limitNum')
    MyDomainStat = type('DomainStat_' + str(user.dbname), (DomainStat,), {'__bind_key__': user.dbname})
    result = db.session.query(MyDomainStat.domain.label("domain"),
                              db.func.sum(MyDomainStat.sum).cast(db.BigInteger).label("sum"),
                              db.func.sum(MyDomainStat.hit).cast(db.BigInteger).label("hit"),
                              db.func.sum(MyDomainStat.miss).cast(db.BigInteger).label("miss"),
                              db.func.sum(MyDomainStat.size).cast(db.BigInteger).label("size"),
                              db.func.avg(MyDomainStat.resptime).label("resptime"),
                              db.func.sum(MyDomainStat.s_code_000).cast(db.BigInteger).label("s_code_000"),
                              db.func.sum(MyDomainStat.s_code_20x).cast(db.BigInteger).label("s_code_20x"),
                              db.func.sum(MyDomainStat.s_code_30x).cast(db.BigInteger).label("s_code_30x"),
                              db.func.sum(MyDomainStat.s_code_40x).cast(db.BigInteger).label("s_code_40x"),
                              db.func.sum(MyDomainStat.s_code_50x).cast(db.BigInteger).label("s_code_50x"),
                              db.func.sum(MyDomainStat.othercode).cast(db.BigInteger).label("othercode"),
                              ((db.func.sum(MyDomainStat.s_code_000) + db.func.sum(MyDomainStat.s_code_40x) +
                               db.func.sum(MyDomainStat.s_code_50x) + db.func.sum(MyDomainStat.othercode)) * 100 /
                              db.func.sum(MyDomainStat.sum)).label("errorrate")).\
        filter(MyDomainStat.datetime >= startTime).filter(MyDomainStat.datetime <= endTime)
    if svrnameArr:
        result = result.filter(MyDomainStat.svrname.in_(svrnameArr))
    if domain:
        result = result.filter(MyDomainStat.domain.ilike(domain))
    result = result.group_by(MyDomainStat.domain)
    if orderby:
        result = result.order_by(db.text(orderby))
    result = result.limit(limitNum).all()
    jresult = []
    rank = 0
    for r in result:
        temp = {}
        rank = rank + 1
        temp["rank"] = rank
        temp["domain"] = r[0]
        temp["sum"] = r[1]
        temp["hit"] = r[2]
        temp["miss"] = r[3]
        temp["size"] = r[4]
        temp["resptime"] = float(r[5])
        temp["s_code_000"] = r[6]
        temp["s_code_20x"] = r[7]
        temp["s_code_30x"] = r[8]
        temp["s_code_40x"] = r[9]
        temp["s_code_50x"] = r[10]
        temp["othercode"] = r[11]
        temp["errorrate"] = str(float("%.2f" % r[12])) + "%"
        if temp["sum"]*temp["resptime"]:
            temp["downrate"] = temp["size"] / (temp["sum"]*temp["resptime"]*0.001)
        else:
            temp["downrate"] = '--'
        temp["hitrate"] = str(float("%.2f" % (temp["hit"] * 100.0 / temp["sum"]))) + "%"
        if temp["size"] > 1024*1024*1024*1024:
            temp["size"] = str(float("%.2f" % (temp["size"]/(1024*1024*1024*1024)))) + " TB"
        elif temp["size"] > 1024*1024*1024:
            temp["size"] = str(float("%.2f" % (temp["size"]/(1024*1024*1024)))) + " GB"
        elif temp["size"] > 1024*1024:
            temp["size"] = str(float("%.2f" % (temp["size"]/(1024*1024)))) + " MB"
        else:
            temp["size"] = str(float("%.2f" % (temp["size"]/1024))) + " KB"

        if temp["resptime"] == 0:
            temp["downrate"] = "--"
        elif temp["downrate"] > 1024*1024*1024*1024:
            temp["downrate"] = str(float("%.2f" % (temp["downrate"]/(1024*1024*1024*1024)))) + " TBps"
        elif temp["downrate"] > 1024*1024*1024:
            temp["downrate"] = str(float("%.2f" % (temp["downrate"]/(1024*1024*1024)))) + " GBps"
        elif temp["downrate"] > 1024*1024:
            temp["downrate"] = str(float("%.2f" % (temp["downrate"]/(1024*1024)))) + " MBps"
        else:
            temp["downrate"] = str(float("%.2f" % (temp["downrate"]/1024))) + " KBps"
        jresult.append(temp)
    return jsonify(jresult)
