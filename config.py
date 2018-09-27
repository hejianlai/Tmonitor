class Config:
    SECRET_KEY = 'the secret key for yxjsweb'
    EXPIRATION = 7200
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://yxjsuser:7758258@192.168.128.166:3306/yxjs_user?charset=utf8'
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost:3306/yxjs_user?charset=utf8'
    SQLALCHEMY_BINDS = {
        'yxjs': SQLALCHEMY_DATABASE_URI.replace('yxjs_user', 'yxjs')
    }
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
