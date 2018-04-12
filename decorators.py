# -*- coding: utf-8 -*-
# @File  : decorators.py
# @Author: deeeeeeeee
# @Date  : 2017/12/14
from functools import wraps
from flask import abort
from flask_login import current_user
from models import Permission


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def moderator_required(f):
    return permission_required(Permission.MODERATE)(f)


def admin_required(f):
    return permission_required(Permission.ADMIN)(f)


def leader_required(f):
    return permission_required(Permission.VIEW_REPORT)(f)


def comment_required(f):
    return permission_required(Permission.COMMENT)(f)

