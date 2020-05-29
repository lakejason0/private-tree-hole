from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Boolean, Integer, TIMESTAMP, DATETIME, Date, DECIMAL, Text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json
import pymysql

app = Flask(__name__)

USERNAME = 'treehole'
PASSWORD = 'rDbNGdnyasnPjdkb'
HOST = 'lakejason0.ml'
PORT = 3306
DATABASE = 'treehole'
DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(USERNAME,PASSWORD,HOST,PORT,DATABASE)
engine = create_engine(DB_URI)
DBSession = sessionmaker(bind=engine)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

Base = declarative_base(engine)

class DateEncoder(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj, datetime):
            return str(obj)
        elif isinstance(obj,date):
            return str(obj)
        elif isinstance(obj,DECIMAL):
            return str(obj)
        else:
            return json.JSONEncoder.default(self,obj)
class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(25),nullable=False)
    thread = Column(String(30),nullable=False)
    time = Column(TIMESTAMP,nullable=False)
    floor = Column(Integer,nullable=False)
    is_deleted = Column(Boolean,nullable=False)
    report = Column(Integer,nullable=True)
    content = Column(Text,nullable=False)

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
        return json.dumps(json_data,cls=DateEncoder)

class Thread(Base):
    __tablename__ = 'thread'

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread = Column(String(30),nullable=False)
    is_closed = Column(Boolean,nullable=False)
    is_deleted = Column(Boolean,nullable=False)
    is_announcement = Column(Boolean,nullable=False)
    title = Column(Text,nullable=False)

    def to_json(self):
        json_data = {
            'thread': self.thread,
            'is_closed': self.is_closed,
            'is_deleted': self.is_deleted,
            'is_announcement': self.is_announcement,
            'title': self.title
        }
        return json.dumps(json_data,cls=DateEncoder)

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template("default.html")

@app.route('/thread/<id>')
@app.route('/thread/<id>.html')
def thread(id):
    try:
        session = DBSession()
        posts = session.query(Post).filter((Post.thread==id) and (Post.is_deleted==0)).all()
        postslist = []
        for i in posts:
            postslist.append(json.loads(i.to_json()))
        thread = json.loads(session.query(Thread).filter((Thread.thread==id) and (Thread.is_deleted==0)).first().to_json())
        if postslist or thread:
            #    print(postslist)
            return render_template("threadview.html",thread=thread,posts=postslist)
        else:
            return render_template("errorview.html")
    except:
        return render_template("errorview.html")

@app.route('/public')
@app.route('/public.html')
def public():
    return ""

@app.route('/login')
@app.route('/login.html')
def logging():
    return ""

@app.route('/api')
def api():
    recv_data = json.loads(request.get_data('data'))
    return ""

@app.route('/api/thread', methods=['POST'])
def unknownThread():
    recv_data = json.loads(request.get_data('data'))
    return ""

@app.route('/api/thread/<id>', methods=['GET','POST'])
def knownThread(id):
    recv_data = json.loads(request.get_data('data'))
    try:
        if recv_data['action'] == "get":
            session = DBSession()
            posts = session.query(Post).filter((Post.thread==id) and (Post.is_deleted==0)).all()
            postslist = []
            for i in posts:
                postslist.append(json.loads(i.to_json()))
            thread = json.loads(session.query(Thread).filter((Thread.thread==id) and (Thread.is_deleted==0)).first().to_json())
            if postslist or thread:
                #    print(postslist)
                return {'code':200,'data':{"thread":thread,"posts":postslist}}
            else:
                return {'code':403,'data':{'message':'Forbidden'}}
    except:
        return {'code':403,'data':{'message':'Forbidden'}}
if __name__ == '__main__':
    app.run(debug = True)