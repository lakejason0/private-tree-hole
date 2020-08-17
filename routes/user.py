import json
import os

from flask import Blueprint, request
from flask_login import login_user

import shared
import jwt
import bcrypt
from models import User

route = Blueprint('user', __name__)
print(shared.login)


@shared.login.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    return user


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
