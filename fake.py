# -*- coding: utf-8 -*-
# @File  : fake.py
# @Author: deeeeeeeee
# @Date  : 2017/12/16
from random import randint
from faker import Faker
from sqlalchemy.exc import IntegrityError
from models import User, Course, Chapter, Category, Comment
from exts import db


def fake_users(count=100):
    fake = Faker(locale='zh-cn')
    i = 0
    while i < count:
        u = User(email=fake.email(),
                 username=fake.user_name(),
                 password=fake.password(),
                 telephone=fake.phone_number(),
                 location=fake.address(),
                 about_me=fake.text(),
                 member_since=fake.past_date()
                 )
        db.session.add(u)
        try:
            db.session.commit()
            course_count = Course.query.count()
            course = Course.query.offset(randint(0, course_count - 1)).first()
            u.courses.append(course)
            i += 1
        except IntegrityError:
            db.session.rollback()


def fake_category(count=5):
    fake = Faker(locale='zh-cn')
    i = 0
    while i < count:
        c = Category(name=fake.name(), last_modify=fake.past_date())
        db.session.add(c)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def fake_course(count=1000):
    fake = Faker()
    category_count = Category.query.count()
    for i in range(count):
        u = Category.query.offset(randint(0, category_count - 1)).first()
        c = Course(teacher=fake.name(),
                   num=randint(0, 1000),
                   timestamp=fake.past_date(),
                   name=fake.name(),#unique
                   intro=fake.text(),
                   category=u)
        db.session.add(c)
    db.session.commit()


def fake_chapter(count=1000):
    fake = Faker()
    course_count = Course.query.count()
    for i in range(count):
        u = Course.query.offset(randint(0, course_count - 1)).first()
        c = Chapter(name=fake.name(), course=u)
        db.session.add(c)
    db.session.commit()


def fake_comment(count=1000):
    fake = Faker()
    course_count = Course.query.count()
    user_count = User.query.count()
    for i in range(count):
        course = Course.query.offset(randint(0, course_count - 1)).first()
        u = User.query.offset(randint(0, user_count - 1)).first()
        c = Comment(username=fake.name(), body=fake.text())
        c.course = course
        c.user = u
        db.session.add(c)
    db.session.commit()
