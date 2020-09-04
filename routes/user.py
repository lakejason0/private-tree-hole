import json
import os
from functools import wraps

import bcrypt
import jwt
from flask import Blueprint, request

import shared
from models import User

route = Blueprint('user', __name__)


@route.route('/login', methods=['POST'])
def loginRoute():
    recv_data = json.loads(request.get_data('data', parse_form_data=True))
    try:
        user = User.query.filter_by(username=recv_data['username']).first()
        if user and bcrypt.checkpw(recv_data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
            token = jwt.encode({'uid': user.id}, os.getenv("JWT_SECRET"), algorithm='HS256')
            return {
                'code': 200,
                'data': {
                    'success': True,
                    'token': token.decode('utf-8')
                },
                'toast': []
            }
        return {
            'code': 400,
            'data': {
                'success': False
            },
            'toast': [{'code': 400, 'message': 'The password does not match, or the user does not exist.',
                       'identifier': 'message.userNotMatching'}]
        }
    except Exception as err:
        print(err)
        toastsList = [
            {'code': 500, 'message': 'Internal Server Error', 'identifier': 'message.ise'}]
        return {'code': 500, 'data': {}, 'toast': toastsList}


@route.route('/register', methods=['POST'])
def registerRoute():
    recv_data = json.loads(request.get_data('data', parse_form_data=True))
    try:
        existingUsers = shared.db.session.query(User).filter(User.username == recv_data['username']).all()
        if existingUsers:
            return {
                'code': 400,
                'data': [],
                'toast': [
                    {'code': 400, 'message': 'The requested username is occupied',
                     'identifier': 'message.usernameBeingOccupied'}
                ]
            }
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
            'toast': []
        }
    except Exception as err:
        print(err)
        toastsList = [
            {'code': 500, 'message': 'Internal Server Error', 'identifier': 'message.ise'}]
        return {'code': 500, 'data': {}, 'toast': toastsList}


def needLogin(block=True):
    def _needLogin(f):
        @wraps(f)
        def __needLogin(*args, **kwargs):
            token = ("Authorization" in request.headers and request.headers.get("Authorization") or "")[7:]
            user = None
            try:
                data = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=['HS256'])
                user = User.query.filter_by(id=data['uid']).first()
                if user is None:
                    raise Exception("UserNotFoundException")
                request.user = user

            except Exception as err:
                print(err)
                user = None
                if block:
                    return {
                        'code': 401,
                        'data': {},
                        'toast': [
                            {'code': 401, 'message': 'You are not authorized.', 'identifier': 'message.notAuthorized'}]
                    }
            request.user_logged = user is not None
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
        },
        'toast': []
    }
