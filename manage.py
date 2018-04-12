# -*- coding: utf-8 -*-
# @File  : manage.py.py
# @Author: deeeeeeeee
# @Date  : 2017/12/11
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from qa163 import app
from exts import db
from models import User, Role, Permission, Category


manager = Manager(app)
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Permission=Permission, Category=Category)


manager.add_command('db', MigrateCommand)
manager.add_command('shell', Shell(make_context=make_shell_context))


if __name__ == '__main__':
        manager.run()