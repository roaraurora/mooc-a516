# -*- coding: utf-8 -*-
# @File  : exts.py.py
# @Author: deeeeeeeee
# @Date  : 2017/12/11
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_uploads import UploadSet, IMAGES

login_manager = LoginManager()
login_manager.session_protection = 'None'
login_manager.login_view = 'login'
Index_pic = UploadSet('pic', IMAGES)
Chapter_video = UploadSet(name='video', extensions='mp4')
Chapter_PDF = UploadSet(name='pdf', extensions='pdf')




db = SQLAlchemy()