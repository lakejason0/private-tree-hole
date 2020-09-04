import json
import os
import random
import string
import sys
import time
import traceback

from dotenv import load_dotenv
from flask import Flask, request
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import shared

load_dotenv()
app = Flask(__name__)

DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
    os.getenv("DB_USERNAME"), os.getenv("DB_PASSWORD"), os.getenv("DB_HOST"), os.getenv("DB_PORT"),
    os.getenv("DB_NAME"))
engine = create_engine(DB_URI)
shared.engine = engine
DBSession = sessionmaker(bind=engine)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = 'HUREN YES'
db = SQLAlchemy(app)
shared.db = db

login = LoginManager(app)
shared.login = login

lang_path = 'static/lang/'
permission_path = 'permission/'
DEFAULT_USER_GROUP = 'anonymous'
PAGENIATE_POSTS_AMOUNT = 30


from models import Post, Thread, Base
from routes.user import route as UserRoute
from routes.user import needLogin as needLogin
from routes.thread import route as ThreadRoute
from routes.public import route as AnnRoute

Base.metadata.create_all(engine)

app.register_blueprint(UserRoute, url_prefix='/api/user')
app.register_blueprint(ThreadRoute, url_prefix='/api/thread')
app.register_blueprint(AnnRoute, url_prefix='/api/public')


def getLangName(path):
    ''' 获取指定目录下的所有指定后缀的文件名 '''
    lang_list = []
    f_list = os.listdir(path)
    # print f_list
    for i in f_list:
        # os.path.splitext():分离文件名与扩展名
        if os.path.splitext(i)[-1] == '.json':
            lang_list.append(i)
    return {'path': path, 'lang_list': lang_list}


def loadLang(lang_list):
    langs = {}
    for i in lang_list['lang_list']:
        with open(lang_list['path'] + i, 'r', encoding='utf8') as f:
            lang = json.load(f)
            name = os.path.splitext(i)[0]
            langs.update({name: lang})
    return langs


def getGroupName(path):
    group_list = []
    f_list = os.listdir(path)
    for i in f_list:
        if os.path.splitext(i)[-1] == '.json':
            group_list.append(i)
    return {'path': path, 'group_list': group_list}


def loadGroup(group_list):
    groups = {}
    for i in group_list['group_list']:
        with open(group_list['path'] + i, 'r', encoding='utf8') as f:
            data = json.load(f)
            name = os.path.splitext(i)[0]
            groups.update({name: data})
    return groups

def checkPermission(groupName, permission):
    groupList = loadGroup(getGroupName(permission_path))
    print(groupName)
    permissions = set()
    permissions.update(groupList[groupName]['permissions'])
    for superior_to in groupList[groupName]['superior_to']:
        permissions.update(groupList[superior_to]['permissions'])
    for inferior_to in groupList[groupName]['inferior_to']:
        permissions = permissions.difference(set(groupList[inferior_to]['permissions']))
    if permission in permissions:
        print(f"{permission} is in {groupName}")
        return True
    return False

@app.route('/api/ping')
def ping():
    return {"code": 200, "data": {}, "toast": {}}


@app.route('/api')
def api():
    recv_data = {"code": 200, "data": json.loads(request.get_data('data', parse_form_data=True))}
    return recv_data


@app.route('/api/public')
def publics():
    try:
        session = DBSession()
        publics = session.query(Thread).filter(
            Thread.is_public == True, Thread.is_deleted == False).all()
        publicList = []
        for i in publics:
            publicList.append(json.loads(i.to_json()))
        session.close()
        if publicList:
            return {'code': 200, 'data': {'publics': publicList}, 'toast': []}
        else:
            toastsList = [{'code': 404, 'message': 'No public post exists', 'identifier': 'message.emptyPublic'}]
            return {'code': 404, 'data': {}, 'toast': toastsList}
    except Exception as err:
        print(err)
        toastsList = [{'code': 500, 'message': 'Internal server error', 'identifier': 'message.ise'}]
        return {'code': 500, 'data': {}, 'toast': toastsList}

@needLogin(block=False)
@app.route('/api/thread', methods=['POST'])
def unknownThread():
    try:
        recv_data = json.loads(request.get_data('data', parse_form_data=True))
        print(recv_data)
        if recv_data['action'] == "create":
            try:
                if request.user_logged:
                    if (request.user.username != recv_data['data']['username']) and (not checkPermission(request.user.group, 'FAKE_USERNAME')):
                        toastsList = [{'code': 400, 'message': 'Not matching with currently logged-in user.', 'identifier': 'message.fakeUsername'}]
                        return {'code': 400, 'data': {}, 'toast': toastsList}
            except:
                pass
            print(recv_data['action'])

            def rand_str(n):
                return ''.join([random.choice(
                    string.ascii_lowercase + string.ascii_uppercase + string.digits) for i in range(n)])

            newThreadId = rand_str(random.randint(6, 30))
            print(newThreadId)
            session = DBSession()
            existingThreads = session.query(Thread).filter(
                Thread.thread == newThreadId).all()
            print(existingThreads)
            if not existingThreads:
                print(recv_data['data'])
                recv_data['data'].update(
                    {'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())})
                recv_data['data'].update({'floor': 1})
                if (not recv_data['data']['title']) and (not recv_data['data']['content']):
                    session.close()
                    toastsList = [
                        {'code': 400, 'message': 'Nothing is provided', 'identifier': 'message.emptyPost'}]
                    return {'code': 400, 'data': {}, 'toast': toastsList}
                if not recv_data['data']['title']:
                    recv_data['data'].update({'title': 'Untitled'})
                if not recv_data['data']['username']:
                    recv_data['data'].update({'username': request.remote_addr})
                if not recv_data['data']['content']:
                    recv_data['data'].update(
                        {'content': 'No description provided.'})
                if not recv_data['data']['is_public']:
                    recv_data['data'].update(
                        {'is_public': False})
                newThreadMetadata = Thread(thread=newThreadId, is_closed=False, is_deleted=False,
                                           is_public=recv_data['data']['is_public'], title=recv_data['data']['title'])
                newThread = Post(thread=newThreadId, username=recv_data['data']['username'],
                                 time=recv_data['data']['time'],
                                 floor=recv_data['data']['floor'], is_deleted=False,
                                 content=recv_data['data']['content'])
                session.add(newThread)
                session.add(newThreadMetadata)
                session.commit()
                session.close()
                return {'code': 200, 'data': {'thread': newThreadId}}
            else:
                toastsList = [
                    {'code': 500, 'message': 'Internal Server Error', 'identifier': 'message.ise'}]
                return {'code': 500, 'data': {}, 'toast': toastsList}
        elif recv_data['action'] == "query":
            if recv_data['data']['type'] == "thread":
                pass
    except Exception as err:
        print(err)
        toastsList = [
            {'code': 500, 'message': 'Internal Server Error', 'identifier': 'message.ise'}]
        return {'code': 500, 'data': {}, 'toast': toastsList}

@needLogin(block=False)
@app.route('/api/thread/<id>', methods=['GET', 'POST'])
def knownThread(id):
    try:
        recv_data = json.loads(request.get_data('data', parse_form_data=True))
    except:
        recv_data = {"action":"get"}
    try:
        if recv_data['action'] == "get":
            session = DBSession()
            try:
                if request.user_logged:
                    if checkPermission(request.user.group, 'GET_DELETED'):
                        print(1)
                        posts = session.query(Post).filter(
                            Post.thread == id).all()
                    else:
                        posts = session.query(Post).filter(
                            Post.thread == id, Post.is_deleted == False).all()
                else:
                    print(2)
                    posts = session.query(Post).filter(
                        Post.thread == id, Post.is_deleted == False).all()
            except:
                print(3)
                posts = session.query(Post).filter(
                        Post.thread == id, Post.is_deleted == False).all()
            postsList = []
            for i in posts:
                postsList.append(json.loads(i.to_json()))
            try:
                if request.user_logged:
                    if checkPermission(request.user.group, 'GET_DELETED'):
                        thread = json.loads(session.query(Thread).filter(Thread.thread == id).first().to_json())
                    else:
                        thread = json.loads(session.query(Thread).filter(Thread.thread == id, Thread.is_deleted == False).first().to_json())
                else:
                    thread = json.loads(session.query(Thread).filter(Thread.thread == id, Thread.is_deleted == False).first().to_json())
            except:
                thread = json.loads(session.query(Thread).filter(Thread.thread == id, Thread.is_deleted == False).first().to_json())
            print(thread)
            print(postsList)
            if postsList and thread:
                #    print(postslist)
                session.close()
                return {'code': 200, 'data': {"thread": thread, "posts": postsList}}
            else:
                session.close()
                toastsList = [
                    {'code': 403, 'message': 'Forbidden', 'identifier': 'message.forbidden'}]
                return {'code': 403, 'data': {}, 'toast': toastsList}
        elif recv_data['action'] == "reply":
            try:
                session = DBSession()
                thread = json.loads(session.query(Thread).filter(
                    Thread.thread == id, Thread.is_deleted == False).first().to_json())
                if thread:
                    if not thread['is_closed']:
                        print(recv_data['data'])
                        if not recv_data['data']['content']:
                            session.close()
                            toastsList = [
                                {'code': 400, 'message': 'Nothing is provided', 'identifier': 'message.emptyPost'}]
                            return {'code': 400, 'data': {}, 'toast': toastsList}
                        recv_data['data'].update(
                            {'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())})
                        if not recv_data['data']['username']:
                            recv_data['data'].update({'username': 'Anonymous'})
                        if not recv_data['data']['content']:
                            recv_data['data'].update(
                                {'content': 'No description provided.'})
                        posts = session.query(Post).filter(
                            Post.thread == id).all()
                        postsList = []
                        for i in posts:
                            postsList.append(json.loads(i.to_json()))
                        if postsList:
                            floor = postsList[-1]['floor'] + 1
                            recv_data['data'].update({'floor': floor})
                        else:
                            toastsList = [
                                {'message': 'Can\'t find the correct floor number.',
                                 'identifier': 'message.floorNumberError'}]
                            return {'code': 500, 'data': {}, 'toast': toastsList}
                        reply = Post(thread=id, username=recv_data['data']['username'], time=recv_data['data']['time'],
                                     floor=recv_data['data']['floor'], is_deleted=False,
                                     content=recv_data['data']['content'])
                        session.add(reply)
                        session.commit()
                        posts = session.query(Post).filter(
                            Post.thread == id, Post.is_deleted == False).all()
                        postsList = []
                        for i in posts:
                            postsList.append(json.loads(i.to_json()))
                        thread = json.loads(session.query(Thread).filter(
                            Thread.thread == id, Thread.is_deleted == False).first().to_json())
                        session.close()
                        return {'code': 200, 'data': {"thread": thread, "posts": postsList}}
                    else:
                        session.close()
                        toastsList = [
                            {'code': 403, 'message': 'The thread you\'re replying to is closed.',
                             'identifier': 'message.closedThread'}]
                        return {'code': 403, 'data': {}, 'toast': toastsList}
                else:
                    session.close()
                    toastsList = [
                        {'code': 404, 'message': 'The thread you\'re replying to is missing.',
                         'identifier': 'message.missingThread'}]
                    return {'code': 404, 'data': {}, 'toast': toastsList}
            except Exception as err:
                print(err)
                toastsList = [
                    {'code': 500, 'message': 'Internal Server Error', 'identifier': 'message.ise'}]
                return {'code': 500, 'data': {}, 'toast': toastsList}
        elif recv_data['action'] == "edit":
            pass
        elif recv_data['action'] == "delete":
            pass
        elif recv_data['action'] == "close":
            pass
        elif recv_data['action'] == "reopen":
            pass
        elif recv_data['action'] == "publicize":
            pass
        elif recv_data['action'] == "depublicize":
            pass
    except Exception as err:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        toastsList = [{'code': 403, 'message': 'Forbidden',
                       'identifier': 'message.forbidden'}]
        return {'code': 403, 'data': {}, 'toast': toastsList}


if __name__ == '__main__':
    app.run(debug=True)
