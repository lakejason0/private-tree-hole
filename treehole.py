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


@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template("default.html", getThreadFormVisible="", replyFormVisible="invisible")


@app.route('/thread/<id>')
@app.route('/thread/<id>.html')
def thread(id):
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
            return render_template("threadView.html", thread=thread, posts=postslist, getThreadFormVisible="invisible", replyFormVisible="")
        else:
            session.close()
            return render_template("errorView.html", getThreadFormVisible="invisible", replyFormVisible="")
    except:
        session.close()
        return render_template("errorView.html", getThreadFormVisible="invisible", replyFormVisible="")


@app.route('/public')
@app.route('/public.html')
def public():
    session = DBSession()
    announcements = session.query(Thread).filter(
        (Thread.is_announcement == 1) and (Thread.is_deleted == 0)).all()
    announcementsList = []
    for i in announcements:
        announcementsList.append(json.loads(i.to_json()))
    session.close()
    return render_template("announcementView.html", announcements=announcements)


@app.route('/login')
@app.route('/login.html')
def logging():
    return render_template("loginView.html")


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
                if not recv_data['data']['title']:
                    recv_data['data'].update({'title': 'Untitled'})
                if not recv_data['data']['username']:
                    recv_data['data'].update({'username': 'Anonymous'})
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
                return {'code': 500, 'data': {'message': 'Internal Server Error', 'identifier': 'message.ise'}}
        elif recv_data['action'] == "query":
            pass
    except Exception as err:
        print(err)
        return {'code': 500, 'data': {'message': 'Internal Server Error', 'identifier': 'message.ise'}}


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
                return {'code': 403, 'data': {'message': 'Forbidden'}}
        elif recv_data['action'] == "reply":
            try:
                session = DBSession()
                thread = json.loads(session.query(Thread).filter(
                    (Thread.thread == id) and (Thread.is_deleted == 0)).first().to_json())
                if thread:
                    if not thread['is_closed']:
                        print(recv_data['data'])
                        recv_data['data'].update(
                            {'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())})
                        if not recv_data['data']['username']:
                            recv_data['data'].update({'username': 'Anonymous'})
                        if not recv_data['data']['content']:
                            recv_data['data'].update(
                                {'content': 'No description provided.'})
                        posts = session.query(Post).filter(Post.thread == id).all()
                        postsList = []
                        for i in posts:
                            postsList.append(json.loads(i.to_json()))
                        if postsList:
                            floor = postsList[-1]['floor'] + 1
                            recv_data['data'].update({'floor': floor})
                        else:
                            return {'code': 500, 'data': {'message': 'Can\'t find the correct floor number.', 'identifier': 'message.floorNumberError'}}
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
                        return {'code': 403, 'data': {'message': 'The thread you\'re replying to is closed.', 'identifier': 'message.closedThread'}}
                else:
                    session.close()
                    return {'code': 404, 'data': {'message': 'The thread you\'re replying to is missing.', 'identifier': 'message.missingThread'}}
            except Exception as err:
                print(err)
                return {'code': 500, 'data': {'message': 'Internal Server Error', 'identifier': 'message.ise'}}
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
    except:
        return {'code': 403, 'data': {'message': 'Forbidden', 'identifier': 'message.forbidden'}}


if __name__ == '__main__':
    app.run(debug=True)
