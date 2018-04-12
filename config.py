# -*- coding: utf-8 -*-
# @File  : config.py.py
# @Author: deeeeeeeee
# @Date  : 2017/12/11
import os

DEBUG = True
SECRET_KEY = os.urandom(24)
FLASK_ADMIN = '83080779@qq.com'
FLASKY_POSTS_PER_PAGE = 10
UPLOAD_FOLDER = 'static/course/'
UPLOADED_PIC_DEST = os.getcwd() + '/static/course/'
UPLOADED_PDF_DEST = os.getcwd() + '/static/course/'
UPLOADED_VIDEO_DEST = os.getcwd() + '/static/course/'
DATABASE = '163qa'
DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = 'root'
PASSWORD = 'root'
HOST = '127.0.0.1'
PORT = '3306'

# print os.getcwd()+'-'*10

SQLALCHEMY_DATABASE_URI = '{}+{}://{}:{}@{}:{}/{}?charset=utf8'.format(DIALECT, DRIVER, USERNAME, PASSWORD,
                                                                       HOST, PORT, DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = True