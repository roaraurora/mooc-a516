# -*- coding: utf-8 -*-
# @File  : manage.py.py
# @Author: deeeeeeeee
# @Date  : 2017/12/11
import os
import config
import time
import hashlib
import jieba
from PIL import Image
from datetime import datetime
from flask_wtf import Form
from wtforms import StringField,SubmitField
from wtforms.validators import DataRequired
from flask import Flask, render_template, request, redirect, url_for, session, flash, current_app, abort, send_from_directory
from models import User, Permission, Role, Category, Chapter, Course, Comment
from exts import db, login_manager, Index_pic, Chapter_PDF, Chapter_video
from flask_login import login_required, current_user, login_user, logout_user
from decorators import admin_required, permission_required, moderator_required, comment_required, leader_required
from fake import fake_users, fake_category, fake_course, fake_chapter, fake_comment
from flask_uploads import configure_uploads, patch_request_class, UploadNotAllowed
from pyecharts import Scatter3D
import random

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)
login_manager.init_app(app)
configure_uploads(app, (Index_pic, Chapter_video, Chapter_PDF))
patch_request_class(app, size=1024*1024*1024*4)
# set maximum file size, default is 16MB = 1024*1024*64

# TODO:add log func


def scatter3d():
    data1 = []
    for course in Course.query.all():
        data = [course.users.count(), course.num, course.comments.count()]
        data1.append(data)
    range_color = ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf',
                   '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
    scatter3D = Scatter3D("3D scattering plot demo", width=1200, height=600)
    scatter3D.add("", data, is_visualmap=True, visual_range_color=range_color)
    return scatter3D.render_embed()


@app.route('/data')
@leader_required
def data():
    return render_template('pyecharts.html', myechart=scatter3d())

@app.route('/')
def home():
    return redirect(url_for('index'))


@app.route('/admin')
# @login_required
@admin_required
def admin_only():
    return 'Welcome ADMIN'


@app.route("/logout")
@login_required
def logout():
    logout_user()
    #clean cookies
    return redirect(url_for('index'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter(User.email == email).first()
        if user:
            if user.verify_password(password):
                session['user_id'] = user.id
                if request.form.get('remember'):
                    session.permanent = True
                login_user(user)
                user.last_seen = datetime.utcnow()
                return redirect(url_for('index'))
            return render_template('login.html', status_pass=True)
        return render_template('login.html', status_mail=True)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        email = request.form.get('email')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        telephone = request.form.get('telephone')
        user = User.query.filter(User.email == email).first()
        #校验邮箱是否被注册
        if user:
            return render_template('register.html', status_tel=True)
        user = User.query.filter(User.username == username).first()
        if user:
            return render_template('register.html', status_name=True)
        #校验密码
        if password1 != password2:
            return render_template('register.html', status_pass=True)
        else:
            user = User(username=username, email=email, telephone=telephone, password=password1)
            db.session.add(user)
            db.session.commit()
            #如果注册成功，则跳转到登录页面
            return redirect(url_for('login'))


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    if current_user.is_authenticated:
        user = User.query.filter_by(username=username).first_or_404()
        if request.method == 'GET':
            if current_user.username == username or current_user.can(Permission.ADMIN):
                return render_template('modify_user.html', user=user)
            else:
                return render_template('user.html', user=user)
        else:
            password = request.form.get('password')
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')
            telephone = request.form.get('telephone')
            location = request.form.get('location')
            about_me = request.form.get('about_me')
            role = request.form.get('role')
            # 校验密码
            if password:
                if current_user.verify_password(password):
                    if password1 != password2:
                        return render_template('modify_user.html', status_pass1=True, user=user)
                    else:
                        if password1:
                            current_user.password = password1
                        if telephone:
                            current_user.telephone = telephone
                        if location:
                            current_user.location = location
                        if about_me:
                            current_user.about_me = about_me
                        if role:
                            role = Role.query.filter_by(name=role).first()
                            current_user.role = role
                        db.session.commit()
                        return redirect(url_for('user', username=user.username))
                else:
                    return render_template('modify_user.html', status_pass2=True, user=user)
            else:
                if location:
                    current_user.location = location
                if about_me:
                    current_user.about_me = about_me
                if role:
                    role = Role.query.filter_by(name=role).first()
                    current_user.role = role
                db.session.commit()
                return redirect(url_for('user', username=user.username))
    else:
        abort(403)


@app.route('/modify_chapter/<course_id>', methods=['GET', 'POST'])
@moderator_required
def modify_chapter(course_id):
    if request.method == 'GET':
        course = Course.query.filter_by(id=course_id).first_or_404()
        chapter = Chapter.query.filter_by(parent_id=0).first()
        chapter_set = []
        for i in course.chapters:
            chapter_set.append(chapter)
            chapter = Chapter.query.filter_by(parent_id=chapter.id).first()
        if chapter_set:
            return render_template('modify_chapter.html', chapter_set=chapter_set)
        else:
            return render_template('modify_chapter.html', nochapter=True, course_id=course_id)
    else:
        course = Course.query.filter_by(id=course_id).first_or_404()
        chapter = Chapter.query.filter_by(parent_id=0).first()
        chapter_set = []
        for j in course.chapters:
            chapter_set.append(chapter)
            chapter = Chapter.query.filter_by(parent_id=chapter.id).first()
        count = 0
        for i in chapter_set:
            count += 1
            name = request.form.get('input'+str(count))
            if name:
                i.name = name
                if request.files['pdf'+str(count)]:
                    try:
                        name = hashlib.md5(str(i.id) + str(time.time())).hexdigest()[:15]
                        filename = Chapter_PDF.save(request.files['pdf'+str(count)], folder=str(course.id), name=name + '.')
                        i.init_pdf()
                        i.PDF = filename
                    except UploadNotAllowed:
                        return render_template('modify_chapter.html', PDFillegal=True, course=course, chapter_set=chapter_set)
                if request.files['video'+str(count)]:
                    try:
                        name = hashlib.md5(str(i.id) + str(time.time())).hexdigest()[:15]
                        filename = Chapter_video.save(request.files['video'+str(count)], folder=str(course.id), name=name + '.')
                        i.init_video()
                        i.video = filename
                    except UploadNotAllowed:
                        return render_template('modify_chapter.html', videoillegal=True, course=course, chapter_set=chapter_set)
                db.session.commit()
            else:
                return render_template('modify_chapter.html', nameisnull=True, course=course, chapter_set=chapter_set)
        return redirect(url_for('modify_chapter', course_id=course_id))


@app.route('/delete/<chapter_id>')
@moderator_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.filter_by(id=chapter_id).first_or_404()
    course_id = chapter.course_id
    chapter.delete()
    return redirect(url_for('modify_chapter', course_id=course_id))


@app.route('/insert/<chapter_id>')
@moderator_required
def insert_chapter(chapter_id):
    chapter1 = Chapter.query.filter_by(id=chapter_id).first_or_404()
    course_id = chapter1.course_id
    chapter = Chapter(parent_id=chapter_id, course_id=course_id)
    chapter.insert()
    return redirect(url_for('modify_chapter', course_id=course_id))


@app.route('/insert_course/<course_id>')
@moderator_required
def insert_course(course_id):
    chapter = Chapter(parent_id=0, course_id=course_id)
    db.session.add(chapter)
    db.session.commit()
    return redirect(url_for('modify_chapter', course_id=course_id))


@app.route('/modify_course/<course_id>', methods=['GET', 'POST'])
@moderator_required
def modify_course(course_id):
    if request.method == 'GET':
        course = Course.query.filter(Course.id == course_id).first_or_404()
        return render_template('modify_course.html', course=course)
    else:
        course = Course.query.filter(Course.id == course_id).first_or_404()
        course.name = request.form.get('name')
        if course.name:
            course.teacher = request.form.get('teacher')
            category = request.form.get('category')
            course.last_modify = datetime.utcnow()
            # todo: name is not null , 2 add upload time
            course.intro = request.form.get('intro')
            c = Category.query.filter(Category.name == category).first()
            course.category = c
            db.session.commit()
            if request.files['index_pic']:
                try:
                    name = hashlib.md5(str(course.id)+str(time.time())).hexdigest()[:15]
                    filename = Index_pic.save(request.files['index_pic'], folder=str(course.id), name=name+'.')
                    course.init_index()
                    course.index_pic = filename
                    img = Image.open(
                        os.getcwd() + url_for('static', filename='course/' + str(course.id) + '/' + name + '.jpg'))
                    img = img.resize((1098, 500))
                    img.save(os.getcwd() + url_for('static', filename='course/' + str(course.id) + '/' + name + '.jpg'))
                    db.session.commit()
                except UploadNotAllowed:
                    return render_template('modify_course.html', imageillegal=True)
            return redirect(url_for('modify_course', course_id=course_id))
        else:
            course = Course.query.filter(Course.id == course_id).first()
            return render_template('modify_course.html', course=course, nameisnull=True)
        #TODO add flush


@app.route('/upload/', methods=['GET', 'POST'])
@moderator_required
#@permission_required(Permission.MODERATE)
def upload():
    if request.method == 'GET':
        return render_template('modify_course.html')
    else:
        name = request.form.get('name')
        if name:
            teacher = request.form.get('teacher')
            category = request.form.get('category')
            intro = request.form.get('intro')
            c = Category.query.filter(Category.name == category).first()
            course = Course(teacher=teacher, name=name, intro=intro, category=c)
            db.session.add(course)
            db.session.commit()
            if request.files['index_pic']:
                try:
                    name = hashlib.md5(str(course.id) + str(time.time())).hexdigest()[:15]
                    filename = Index_pic.save(request.files['index_pic'], folder=str(course.id), name=name+'.')
                    course.index_pic = filename
                    img = Image.open(os.getcwd()+url_for('static', filename='course/'+str(course.id)+'/'+name+'.jpg'))
                    img = img.resize((1098, 500))
                    img.save(os.getcwd()+url_for('static', filename='course/'+str(course.id)+'/'+name+'.jpg'))
                    # 处理图片分辨率
                    db.session.commit()
                except UploadNotAllowed:
                    return render_template('modify_course.html', imageillegal=True)
            return redirect(url_for('modify_course', course_id=course.id))
        else:
            return render_template('modify_course.html', nameisnull=True)


@app.route('/delete_course/<course_id>', methods=['GET', 'POST'])
@moderator_required
def delete_course(course_id):
    course = Course.query.filter_by(id=course_id).first_or_404()
    course.delete()
    return redirect(url_for('index'))


@app.route('/modify_category', methods=['GET', 'POST'])
@moderator_required
def modify_category():
    if request.method == 'GET':
        category_set = Category.query.all()
        return render_template('modify_category.html', category_set=category_set)
    else:
        category_set = Category.query.all()
        count = 0
        for i in category_set:
            count += 1
            print count
            name = request.form.get('input'+str(count))
            print name
            if name:
                i.name = name
                db.session.commit()
            else:
                return render_template('modify_category.html', category_set=category_set, nameisnull=True)
        return render_template('modify_category.html', category_set=category_set, success=True)


@app.route('/delete_category/<category_id>')
@moderator_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()
    category.delete()
    return redirect(url_for('modify_category'))


@app.route('/insert_category')
@moderator_required
def insert_category():
    category = Category()
    db.session.add(category)
    db.session.commit()
    return redirect(url_for('modify_category'))


@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET' and request.args.get('key') is None:
        return render_template('index.html', search=True)
    page = request.args.get('page', 1, type=int)
    key = request.form.get('key') if request.method == 'POST' else request.args.get('key')
    # search_key_list = jieba.cut_for_search(key, HMM=False)
    # pagenation = None
    # for search_key in search_key_list:
    #     courses = Course.query.filter(Course.name.like("%"+search_key+"%"))
    #     if not pagenation:
    #         pagenation = courses
    #     else:
    #         pagenation += courses
    pagination_all = Course.query.filter(Course.name.like("%"+key+"%")).order_by(Course.timestamp.desc())
    pagination = pagination_all.paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    course_set = pagination.items
    course_set1 = course_set[:5]
    course_set2 = list(set(course_set) - set(course_set1))
    count = 0
    for i in pagination_all:
        count += 1
    return render_template('search.html', course_set1=course_set1, course_set2=course_set2, pagination=pagination, key=key, count=count)


@app.route('/search_by_category/<key>')
def search_by_category(key):
    page = request.args.get('page', 1, type=int)
    category = Category.query.filter_by(id=key).first_or_404()
    pagination = category.courses.order_by(Course.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    course_set = pagination.items
    course_set1 = course_set[:5]
    course_set2 = list(set(course_set) - set(course_set1))
    count = 0
    for i in category.courses:
        count += 1
    return render_template('search.html', course_set1=course_set1, course_set2=course_set2, pagination=pagination, key=key, flag=1, count=count)


@app.route('/comment/<course_id>', methods=['GET', 'POST'])
@comment_required
def comment(course_id):
    course = Course.query.filter(Course.id == course_id).first_or_404()
    if request.method == 'GET':
        comment_set = []
        for comment in course.comments:
            if not comment.reply_id:
                recomments = course.comments.filter_by(reply_id=comment.id).all()
                comment_set.append({comment: recomments})
        return render_template('comment.html', course=course, comment_set=comment_set)
    else:
        for comment in course.comments:
            body = request.form.get(str(comment.id))
            if body:
                print 'done'
                new_comment = Comment(body=body, reply_id=comment.id, user_id=current_user.id, course_id=course_id, username=current_user.username)
                db.session.add(new_comment)
        body1 = request.form.get('0')
        if body1:
            new_comment1 = Comment(body=body1, reply_id=0, user_id=current_user.id, course_id=course_id, username=current_user.username)
            db.session.add(new_comment1)
        db.session.commit()
        return redirect(url_for('comment', course_id=course_id))


@app.route('/detail/<course_id>', methods=['GET', 'POST'])
@login_required
def detail(course_id):
    if current_user.courses.filter(Course.id == course_id).first():
        followed = True
    else:
        followed = False
    course = Course.query.filter_by(id=course_id).first_or_404()
    return render_template('detail.html', course=course, followed=followed)


@app.route('/follow')
def follow():
    user_id = request.args.get('user_id', type=int)
    user = User.query.filter_by(id=user_id).first_or_404()
    course_id = request.args.get('course_id', type=int)
    course = Course.query.filter_by(id=course_id).first_or_404()
    if user.courses.filter(Course.id == course_id).first():
        user.courses.remove(course)
        db.session.commit()
    else:
        user.courses.append(course)
        db.session.add(user)
        db.session.commit()
    return redirect(url_for('detail', course_id=course_id))


@app.route('/user_follow/<key>')
def user_follow(key):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(id=key).first_or_404()
    pagination = user.courses.paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    course_set = pagination.items
    course_set1 = course_set[:5]
    course_set2 = list(set(course_set) - set(course_set1))
    count = 0
    for i in user.courses.all():
        count += 1
    return render_template('search.html', course_set1=course_set1, course_set2=course_set2, pagination=pagination, key=key, flag=2, count=count)


@app.route('/video')
def video():
    chapter_id = request.args.get('chapter_id', type=int)
    chapter = Chapter.query.filter_by(id=chapter_id).first_or_404()
    course = chapter.course
    course.num += 1
    db.session.commit()
    return render_template('video.html', chapter=chapter, course=course)


@app.route('/download')
def download():
    chapter_id = request.args.get('chapter_id', type=int)
    chapter = Chapter.query.filter_by(id=chapter_id).first_or_404()
    return send_from_directory(app.config['UPLOAD_FOLDER'], chapter.PDF, as_attachment=True)


@app.errorhandler(404)
def not_find(e):
    return render_template('404.html')


@app.errorhandler(403)
def not_find(e):
    return render_template('403.html')


@app.errorhandler(500)
def not_find(e):
    return render_template('500.html')


@app.context_processor
def inject_permissions():
    return dict(Permission=Permission, Category=Category, Chapter=Chapter, Course=Course, Index_pic=Index_pic, Role=Role, Chapter_PDF=Chapter_PDF)
# 上下文处理器让Permission 全局都可以访问


def fake_data():
    with app.app_context():
        # fake_chapter()
        fake_users()
        # fake_category()
        fake_course()
        fake_comment()


if __name__ == '__main__':
    #fake_data()
    app.run()
