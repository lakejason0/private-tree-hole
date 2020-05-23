from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Boolean, Integer, Time, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pymysql

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

class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(25),nullable=False)
    thread = Column(String(30),nullable=False)
    time = Column(Time,nullable=False)
    floor = Column(Integer,nullable=False)
    is_deleted = Column(Boolean,nullable=False)
    report = Column(Integer,nullable=True)

Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
