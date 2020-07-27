import json

from flask import Blueprint, request
from flask_login import login_user

import shared
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
    user = User.query.filter_by(username=recv_data['username']).filter_by(password_hash=recv_data['password']).first()
    print(user)
    if user:
        login_user(user)
        return {
            'code': 200,
            'data': True,
        }
    return {
        'code': 200,
        'data': False
    }


@route.route('/register', methods=['POST'])
def registerRoute():
    recv_data = json.loads(request.get_data('data'))
    user = User()
    user.email = recv_data['email']
    user.username = recv_data['username']
    user.password_hash = recv_data['password']
    shared.db.session.add(user)
    shared.db.session.commit()
    return 'hello'
