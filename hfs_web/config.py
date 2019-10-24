# -*- coding: UTF-8 -*-
#跨站点请求伪造保护功能（CSRF）
CSRF_ENABLED = True
import os
basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@193.168.15.138:3306/hfs_db?charset=utf8"
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
#=========================================================
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_COMMIT_TEARDOWN = True

