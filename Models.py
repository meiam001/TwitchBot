from sqlalchemy import Column, Integer, String, ForeignKey, Table, DATETIME, create_engine, MetaData, Float
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func, desc
import os

Base = declarative_base()

class UserStats(Base):
    __tablename__ = 'userStats'
    userStats_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    channel_id = Column(Integer, ForeignKey('channels.channel_id'), nullable=False)
    stat = Column(String)
    stat_value = Column(String)
    created = Column(DATETIME, default=func.now())

class ActiveUsers(Base):
    __tablename__='activeUsers'
    activeUsers_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    user = Column(String, nullable=False)
    logged_in = Column(Float)

class Users(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    user = Column(String)
    created = Column(DATETIME, default=func.now())

class Channels(Base):
    __tablename__ = 'channels'
    channel_id = Column(Integer, primary_key=True)
    channel = Column(String)
    created = Column(DATETIME, default=func.now())

class Comments(Base):
    __tablename__ = 'comments'
    comment_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    channel_id = Column(Integer, ForeignKey('channels.channel_id'), nullable=False)
    comment = Column(String)
    created = Column(DATETIME, default=func.now())

class MyDatabase:
    DB_ENGINE = {
        'sqlite': 'sqlite:///{DB}'
    }
    db_engine = None
    database_folder = 'Database'
    def __init__(self, dbtype='sqlite', dbname='Chat.db', username='', password=''):
        dbtype = dbtype.lower()
        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url)
            print(self.db_engine)
        else:
            print("DBType is not found in DB_ENGINE")

    @staticmethod
    def get_session(engine):
        return Session(engine)

    def create_db_tables(self):
        self.create_folder('.', 'Database')
        metadata = MetaData()

        activeUsers = Table('activeUsers', metadata,
            Column('activeUsers_id', Integer, primary_key=True),
            Column('user_id', Integer, ForeignKey('users.user_id')),
            Column('user', String),
            Column('logged_in', Float),
            Column('last_checked', Float)
                           )

        userStats = Table('userStats', metadata,
                Column('userStats_id', Integer, primary_key=True),
                Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
                Column('channel_id', Integer, ForeignKey('channels.channel_id'), nullable=False),
                Column('stat', String),
                Column('stat_value', String),
                Column('created', DATETIME, default=func.now()))

        users = Table('users', metadata,
                      Column('user_id', Integer, primary_key=True),
                      Column('user', String),
                      Column('created', DATETIME, default=func.now())
                      )
        comments = Table('comments', metadata,
                         Column('comment_id', Integer, primary_key=True),
                         Column('user_id', None, ForeignKey('users.user_id'), nullable=False),
                         Column('channel_id', None, ForeignKey('channels.channel_id'), nullable=False),
                         Column('comment', String, nullable=False),
                         Column('created', DATETIME, default=func.now())
                         )
        channels = Table('channels', metadata,
                         Column('channel_id', Integer, primary_key=True),
                         Column('channel', String, nullable=False),
                         Column('created', DATETIME, default=func.now())
                         )
        try:
            metadata.create_all(self.db_engine)
            print("Tables created")
        except Exception as e:
            print("Error occurred during Table creation!")
            print(e)

    def create_folder(self, path: str, folder_name: str):
        if folder_name not in os.listdir(path):
            os.mkdir(f'{path}\\{folder_name}')

if __name__ == '__main__':
    pass
    x = MyDatabase('sqlite', dbname='.\\Database\\Chat.db')
    x.create_db_tables()
    session = Session(x.db_engine)
