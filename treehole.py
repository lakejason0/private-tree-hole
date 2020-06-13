from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Boolean, Integer, TIMESTAMP, DATETIME, Date, DECIMAL, Text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date
from db_export import USERNAME, PASSWORD, HOST, PORT, DATABASE
import json
import pymysql
import random
import time
import string
import os

app = Flask(__name__)

DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
    USERNAME, PASSWORD, HOST, PORT, DATABASE)
engine = create_engine(DB_URI)
DBSession = sessionmaker(bind=engine)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

Base = declarative_base(engine)


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj)
        elif isinstance(obj, date):
            return str(obj)
        elif isinstance(obj, DECIMAL):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(25), nullable=False)
    thread = Column(String(30), nullable=False)
    time = Column(TIMESTAMP, nullable=False)
    floor = Column(Integer, nullable=False)
    is_deleted = Column(Boolean, nullable=False)
    report = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)

    def to_json(self):
        json_data = {
            'username': self.username,
            'thread': self.thread,
            'time': self.time,
            'floor': self.floor,
            'is_deleted': self.is_deleted,
            'report': self.report,
            'content': self.content
        }
        return json.dumps(json_data, cls=DateEncoder)


class Thread(Base):
    __tablename__ = 'thread'

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread = Column(String(30), nullable=False)
    is_closed = Column(Boolean, nullable=False)
    is_deleted = Column(Boolean, nullable=False)
    is_announcement = Column(Boolean, nullable=False)
    title = Column(Text, nullable=False)

    def to_json(self):
        json_data = {
            'thread': self.thread,
            'is_closed': self.is_closed,
            'is_deleted': self.is_deleted,
            'is_announcement': self.is_announcement,
            'title': self.title
        }
        return json.dumps(json_data, cls=DateEncoder)


lang_path = 'static/lang/'
permission_path = 'permission/'


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
        with open(lang_list['path']+i, 'r', encoding='utf8') as f:
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
        with open(group_list['path']+i, 'r', encoding='utf8') as f:
            data = json.load(f)
            name = os.path.splitext(i)[0]
            groups.update({name: data})
    return groups

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    langs = loadLang(getLangName(lang_path))
    return render_template("default.html", thread={"thread": ""}, getThreadFormVisible="", replyFormVisible="invisible", langs=langs)


@app.route('/thread/<id>')
@app.route('/thread/<id>.html')
def thread(id):
    langs = loadLang(getLangName(lang_path))
    try:
        session = DBSession()
        posts = session.query(Post).filter(
            (Post.thread == id) and (Post.is_deleted == 0)).all()
        postslist = []
        for i in posts:
            postslist.append(json.loads(i.to_json()))
        thread = json.loads(session.query(Thread).filter(
            (Thread.thread == id) and (Thread.is_deleted == 0)).first().to_json())
        if postslist or thread:
            #    print(postslist)
            session.close()
            return render_template("threadView.html", thread=thread, posts=postslist, getThreadFormVisible="invisible", replyFormVisible="", langs=langs)
        else:
            session.close()
            return render_template("errorView.html", getThreadFormVisible="invisible", replyFormVisible="", langs=langs)
    except:
        session.close()
        return render_template("errorView.html", getThreadFormVisible="invisible", replyFormVisible="", langs=langs)


@app.route('/public')
@app.route('/public.html')
def public():
    langs = loadLang(getLangName(lang_path))
    session = DBSession()
    announcements = session.query(Thread).filter(
        (Thread.is_announcement == 1) and (Thread.is_deleted == 0)).all()
    announcementsList = []
    for i in announcements:
        announcementsList.append(json.loads(i.to_json()))
    session.close()
    return render_template("announcementView.html", thread={"thread": ""}, announcements=announcements, langs=langs)


@app.route('/login')
@app.route('/login.html')
def logging():
    langs = loadLang(getLangName(lang_path))
    return render_template("loginView.html", thread={"thread": ""}, langs=langs)


@app.route('/api')
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
            def rand_str(n): return ''.join([random.choice(
                string.ascii_lowercase+string.ascii_uppercase+string.digits) for i in range(n)])
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
                newThread = Post(thread=newThreadId, username=recv_data['data']['username'], time=recv_data['data']['time'],
                                 floor=recv_data['data']['floor'], is_deleted=False, content=recv_data['data']['content'])
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
                                {'message': 'Can\'t find the correct floor number.', 'identifier': 'message.floorNumberError'}]
                            return {'code': 500, 'data': {}, 'toast': toastsList}
                        reply = Post(thread=id, username=recv_data['data']['username'], time=recv_data['data']['time'],
                                     floor=recv_data['data']['floor'], is_deleted=False, content=recv_data['data']['content'])
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
                            {'code': 403, 'message': 'The thread you\'re replying to is closed.', 'identifier': 'message.closedThread'}]
                        return {'code': 403, 'data': {}, 'toast': toastsList}
                else:
                    session.close()
                    toastsList = [
                        {'code': 404, 'message': 'The thread you\'re replying to is missing.', 'identifier': 'message.missingThread'}]
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
