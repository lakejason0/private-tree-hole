import json
import os

from flask import Blueprint, request

import shared
import jwt
import bcrypt
from models import User
from functools import wraps

route = Blueprint('user', __name__)


@route.route('/login', methods=['POST'])
def loginRoute():
    recv_data = json.loads(request.get_data('data'))
    user = User.query.filter_by(username=recv_data['username']).first()
    if user and bcrypt.checkpw(recv_data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        token = jwt.encode({'uid': user.id}, os.getenv("JWT_SECRET"), algorithm='HS256')
        return {
            'code': 200,
            'data': {
                'success': True,
                'token': token.decode('utf-8')
            },
        }
    return {
        'code': 200,
        'data': {
            'success': False
        },
    }


@route.route('/register', methods=['POST'])
def registerRoute():
    recv_data = json.loads(request.get_data('data'))
    user = User()
    user.email = recv_data['email']
    user.username = recv_data['username']
    user.password_hash = bcrypt.hashpw(recv_data['password'].encode('utf-8'), bcrypt.gensalt())
    shared.db.session.add(user)
    shared.db.session.commit()
    return {
        'code': 200,
        'data': {
            'success': True
        },
    }


def needLogin(block=True):
    def _needLogin(f):
        @wraps(f)
        def __needLogin(*args, **kwargs):
            token = request.headers.get("Authorization")[7:]
            user = None
            try:
                data = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=['HS256'])
                user = User.query.filter_by(id=data['uid']).first()
                if user is None:
                    raise Exception("用户不存在!")
                request.user = user

            except Exception as err:
                print(err)
                user = None
                if block:
                    return {
                        'code': 401
                    }
            request.user_logged = user is None
            result = f(*args, **kwargs)
            return result

        return __needLogin

    return _needLogin


@route.route('/info', methods=['GET'])
@needLogin()
def infoRoute():
    return {
        'code': 200,
        'data': {
            'username': request.user.username
        }
    }
