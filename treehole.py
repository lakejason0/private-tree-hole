import json
import os
import random
import string
import time

from flask import Flask, request
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import shared
from db_export import USERNAME, PASSWORD, HOST, PORT, DATABASE

app = Flask(__name__)

DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
    USERNAME, PASSWORD, HOST, PORT, DATABASE)
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
PAGENIATE_PlOSTS_AMOUNT = 30

from models import Post, Thread
from routes.user import route as UserRoute
from routes.thread import route as ThreadRoute
from routes.announcement import route as AnnRoute

app.register_blueprint(UserRoute, url_prefix='/api/user')
app.register_blueprint(ThreadRoute, url_prefix='/api/thread')
app.register_blueprint(AnnRoute, url_prefix='/api/announcement')


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


@app.route('/api')
@app.route('/api/ping')
def api():
    recv_data = {"code": 200, "data": json.loads(request.get_data('data'))}
    return recv_data


@app.route('/api/public')
def announcements():
    session = DBSession()
    announcements = session.query(Thread).filter(
        (Thread.is_announcement == 1) and (Thread.is_deleted == 0)).all()
    announcementsList = []
    for i in announcements:
        announcementsList.append(json.loads(i.to_json()))
    session.close()
    return {'code': 200, 'data': {"announcements": announcementsList}}


@app.route('/api/thread', methods=['POST'])
def unknownThread():
    recv_data = json.loads(request.get_data('data'))
    print(recv_data)
    try:
        print(recv_data['action'])
        if recv_data['action'] == "create":
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
                    toastsList = [{'code': 400, 'message': 'Nothing is provided', 'identifier': 'message.emptyPost'}]
                    return {'code': 400, 'data': {}, 'toast': toastsList}
                if not recv_data['data']['title']:
                    recv_data['data'].update({'title': 'Untitled'})
                if not recv_data['data']['username']:
                    recv_data['data'].update({'username': request.remote_addr})
                if not recv_data['data']['content']:
                    recv_data['data'].update(
                        {'content': 'No description provided.'})
                newThreadMetadata = Thread(thread=newThreadId, is_closed=False, is_deleted=False,
                                           is_announcement=False, title=recv_data['data']['title'])
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


@app.route('/api/thread/<id>', methods=['GET', 'POST'])
def knownThread(id):
    recv_data = json.loads(request.get_data('data'))
    try:
        if recv_data['action'] == "get":
            session = DBSession()
            posts = session.query(Post).filter(
                (Post.thread == id) and (Post.is_deleted == 0)).all()
            postsList = []
            for i in posts:
                postsList.append(json.loads(i.to_json()))
            thread = json.loads(session.query(Thread).filter(
                (Thread.thread == id) and (Thread.is_deleted == 0)).first().to_json())
            if postsList or thread:
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
                    (Thread.thread == id) and (Thread.is_deleted == 0)).first().to_json())
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
                            (Post.thread == id) and (Post.is_deleted == 0)).all()
                        postsList = []
                        for i in posts:
                            postsList.append(json.loads(i.to_json()))
                        thread = json.loads(session.query(Thread).filter(
                            (Thread.thread == id) and (Thread.is_deleted == 0)).first().to_json())
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
        print(err)
        toastsList = [{'code': 403, 'message': 'Forbidden',
                       'identifier': 'message.forbidden'}]
        return {'code': 403, 'data': {}, 'toast': toastsList}


if __name__ == '__main__':
    app.run(debug=True)
