from flask_sqlalchemy import SQLAlchemy

login = None
db: SQLAlchemy = None
engine: SQLAlchemy.engine = None