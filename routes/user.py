import json

from flask import Blueprint, request

route = Blueprint('user', __name__)


@route.route('/login', methods=['POST'])
def loginRoute():
    recv_data = json.loads(request.get_data('data'))
    return 'hello'


@route.route('/register', methods=['POST'])
def registerRoute():
    recv_data = json.loads(request.get_data('data'))
    return 'hello'
