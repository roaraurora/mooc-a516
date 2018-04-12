# -*- coding: utf-8 -*-
# @File  : models.py.py
# @Author: deeeeeeeee
# @Date  : 2017/12/11
import os
from datetime import datetime
from flask import current_app, url_for
from exts import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from exts import Index_pic, Chapter_PDF, Chapter_video


follows = db.Table('follows', db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                   db.Column('course_id', db.Integer, db.ForeignKey('courses.id')))


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(50), nullable=False, index=True, unique=True)
    telephone = db.Column(db.String(11), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    courses = db.relationship('Course', secondary=follows, backref=db.backref('users', lazy='dynamic'), lazy='dynamic')
    comments = db.relationship('Comment', backref=db.backref('user'), lazy='dynamic')
    #todo:need to handle

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASK_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)


class Permission:
    LEARNING = 1
    COMMENT = 2
    MODERATE = 4
    VIEW_REPORT = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permission = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permission is None:
            self.permission = 0

    @staticmethod
    def insert_roles():
        roles = {
            'Froze_user':[Permission.LEARNING],
            'User': [Permission.LEARNING, Permission.COMMENT],
            'Moderator': [Permission.LEARNING, Permission.COMMENT, Permission.MODERATE],
            'Leader': [Permission.LEARNING, Permission.COMMENT, Permission.VIEW_REPORT],
            'Administrator': [Permission.VIEW_REPORT, Permission.COMMENT, Permission.LEARNING,
                              Permission.MODERATE, Permission.ADMIN]
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permission()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permission += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permission -= perm

    def reset_permission(self):
        self.permission = 0

    def has_permission(self, perm):
        return self.permission & perm == perm


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, default='Untitled')
    last_modify = db.Column(db.DateTime(), default=datetime.utcnow)
    courses = db.relationship('Course', backref='category', lazy='dynamic')

    def delete(self):
        for c in self.courses:
            c.delete()
        db.session.delete(self)
        db.session.commit()


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    teacher = db.Column(db.String(50))
    num = db.Column(db.Integer, nullable=False, default=0)
    index_pic = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    last_modify = db.Column(db.DateTime, default=datetime.utcnow)
    intro = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    chapters = db.relationship('Chapter', backref=db.backref('course'), lazy='dynamic')
    comments = db.relationship('Comment', backref=db.backref('course'), lazy='dynamic')
    #   follows = db.relationship('Follow', backref=db.backref('course'), lazy='dynamic')
    #course.chapters 得到这门课的所有章节

    def delete(self):
        for c in self.chapters:
            c.delete()
        self.init_index()
        os.rmdir(os.getcwd()+'/static/course/'+str(self.id))
        db.session.delete(self)
        db.session.commit()

    def init_index(self):
        if self.index_pic:
            os.remove(Index_pic.path(self.index_pic))


class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), default='untitled')
    PDF = db.Column(db.String(100))
    video = db.Column(db.String(100))
    parent_id = db.Column(db.Integer, default=0)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))

    def get_last(self):
        if self.parent_id == 0:
            return None
        else:
            return Chapter.query.filter_by(id=self.parent_id).first()

    def get_next(self):
        if Chapter.query.filter_by(parent_id=self.id):
            return Chapter.query.filter_by(parent_id=self.id).first()
        else:
            return None

    def insert(self):
        former_chapter = Chapter.query.filter_by(parent_id=self.parent_id).first()
        db.session.add(self)
        db.session.commit()
        if former_chapter:
            former_chapter.parent_id = self.id
            db.session.commit()

    def delete(self):
        #删除章节，传入一个章节实例，删除章节对应的文件，若有子章节，将子章节的parent_id设为该章节的parent_id
        chapter_after = Chapter.query.filter_by(parent_id=self.id).first()
        if chapter_after:
            chapter_after.parent_id = self.parent_id
        self.init_video()
        self.init_pdf()
        db.session.delete(self)
        db.session.commit()

    def init_pdf(self):
        if self.PDF:
            os.remove(Chapter_PDF.path(self.PDF))

    def init_video(self):
        if self.video:
            os.remove(Chapter_video.path(self.video))


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    body = db.Column(db.Text)
    reply_id = db.Column(db.Integer, default=0)
    #评论获取用户名和用户头像需要做大量连接，因此冗余username, user_pic
    username = db.Column(db.String(50))


class AnonymousUser(AnonymousUserMixin):
    def can(self, perm):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
