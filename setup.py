from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Boolean, Integer, TIMESTAMP, DATETIME, DATE, DECIMAL, Text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pymysql
import json

app = Flask(__name__)

USERNAME = 'treehole'
PASSWORD = '*******'
HOST = 'lakejason0.ml'
PORT = 3306
DATABASE = 'treehole'
DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(USERNAME,PASSWORD,HOST,PORT,DATABASE)
engine = create_engine(DB_URI)

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

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(25),nullable=False,unique=True)
    password_hash = Column(String(128), nullable=False)
    group = Column(Text, nullable=False)
    setting = Column(Text, nullable=False)
    email = Column(Text, nullable=False)

    def to_json(self):
        json_data = {
            'thread': self.thread,
            'is_closed': self.is_closed,
            'is_deleted': self.is_deleted,
            'is_announcement': self.is_announcement,
            'title': self.title
        }
        return json.dumps(json_data, cls=DateEncoder)

Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
