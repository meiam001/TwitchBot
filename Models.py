from sqlalchemy import Column, Integer, String, ForeignKey, Table, DATETIME, create_engine, MetaData, Float, DateTime
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy.sql import func, desc
from Parsers import get_channel, get_user, get_comment
import os
import log
from setup import Config
import time
Base = declarative_base()

config = Config()
logger = log.logging.getLogger(__name__)

class UserStats(Base):
    __tablename__ = 'userStats'
    userStats_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    channel_id = Column(Integer, ForeignKey('channels.channel_id'), nullable=False)
    stat = Column(String)
    stat_value = Column(String)
    created = Column(DATETIME, default=func.now())
    last_updated = Column(DateTime, onupdate=datetime.datetime.now)

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

class Cooldowns(Base):
    __tablename__='cooldowns'
    cooldowns_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    channel_id = Column(Integer, ForeignKey('channels.channel_id'), nullable=False)
    cd_type = Column(String)
    length = Column(Integer)
    last_used = Column(Float)
    created = Column(DATETIME, default=func.now())
    last_updated = Column(DateTime, onupdate=datetime.datetime.now)


class ConnectDB:
    DB_ENGINE = {
        'sqlite': 'sqlite:///{DB}'
    }
    db_engine = None
    database_folder = 'Database'

    def __init__(self, dbtype='sqlite', dbname='Chat.db', username='', password=''):
        dbtype = dbtype.lower()
        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url, connect_args={'timeout': 20})
        else:
            print("DBType is not found in DB_ENGINE")

    @staticmethod
    def get_session(engine):
        return Session(engine)


class MyDatabase(ConnectDB):

    def __init__(self, dbtype='sqlite', dbname='Chat.db', username='', password=''):
        """
        Data layer for interacting with database
        :param dbtype: Currently only support sqlite
        :param dbname: database name
        :param username: username for database
        :param password: password for database
        """
        super().__init__(dbtype, dbname, username, password)

    def create_db_tables(self):
        """
        Creates tables if they don't exist
        MUST MATCH TABLE OBJECTS DEFINED ABOVE
        :return:
        """
        self.create_folder('.', 'Database')
        metadata = MetaData()

        activeUsers = Table('activeUsers', metadata,
            Column('activeUsers_id', Integer, primary_key=True),
            Column('user_id', Integer, ForeignKey('users.user_id')),
            Column('user', String),
            Column('logged_in', Float),
            Column('last_checked', Float),
            Column('last_updated', DateTime, onupdate=datetime.datetime.now)
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
        cooldowns = Table('cooldowns', metadata,
                            Column('cooldowns_id', Integer, primary_key=True),
                            Column('user_id', Integer, ForeignKey('users.user_id')),
                            Column('channel_id', Integer, ForeignKey('channels.channel_id'), nullable=False),
                            Column('cd_type', String),
                            Column('last_used', Float),
                            Column('length', Integer),
                            Column('last_updated', DateTime, onupdate=datetime.datetime.now),
                            Column('created', DATETIME, default=func.now())
                          )
        try:
            metadata.create_all(self.db_engine)
            print("Tables created")
        except Exception as e:
            print("Error occurred during Table creation!")
            print(e)

    def write_message(self, message: str, session) -> str:
        """
        Writes user message to database
        :param message:
        :return:
        """
        user = get_user(message)
        comment = get_comment(message)
        channel = get_channel(message)
        user_obj = session.query(Users).where(Users.user==user).first()
        channel_obj = session.query(Channels).where(Channels.channel==channel).first()
        if user_obj:
            self.commit_comment_exists(comment, user_obj, channel_obj, session)
        else:
            return self.commit_comment_dne(comment, user, channel_obj, session, channel)
        return ''

    def commit_comment_exists(self, comment: str, user_obj: Users, channel_obj: Channels, session):
        """
        If user exists, write comment to database
        :param comment: user comment
        :param user_obj: User object
        :param channel_obj: Channel object
        :return:
        """
        comment_obj = Comments(comment=comment, user_id=user_obj.user_id, channel_id=channel_obj.channel_id)
        session.add(comment_obj)
        self.commit(session)

    def get_channel_owed(self, session, message: str, stat: str) -> UserStats:
        """
        Get UserStats object with the label "stat"
        :param stat: string label for type of stat
        """
        channel = get_channel(message)
        user_obj = self.get_user_obj(channel,session)
        stats_obj = self.get_stats_obj(user_obj,channel,stat,session)
        return stats_obj

    def check_for_channel(self, session):
        """
        Checks if channel exists in database, if not create entry for it
        :return:
        """
        channel_obj = session.query(Channels) \
            .where(Channels.channel == config.channel).first()
        if not channel_obj:
            channel_obj = Channels(channel=config.channel)
            session.add(channel_obj)
        self.commit(session)

    def commit_comment_dne(self, comment: str, user: str, channel_obj: Channels, session, channel) -> str:
        """
        if user doesnt exist in database, commit user and comment
        :param comment: user comment
        :param user: user's name string
        :param channel_obj: Channel object
        :return: string welcoming user
        """
        user_obj = Users(user=user)
        session.add(user_obj)
        self.commit(session)
        comment_obj = Comments(
            comment=comment, user_id=user_obj.user_id, channel_id=channel_obj.channel_id
        )
        stats_obj = self.get_stats_obj(user_obj, channel, 'channel_points', session)
        stats_obj.stat_value = '0'
        session.add(stats_obj)
        session.add(comment_obj)
        self.commit(session)
        return f'It\'s @{user}\'s first time in chat! Say hi! (And don\'t forget to follow :D)'

    def create_folder(self, path: str, folder_name: str):
        """
        creates database folder
        :param path: full path leading to folder
        :param folder_name: folder name
        :return:
        """
        if folder_name not in os.listdir(path):
            os.mkdir(f'{path}\\{folder_name}')

    def get_gcd(self, message, session, gcd=0) -> Cooldowns:
        """
        gets global cooldown object
        :param message:
        :param session:
        :param gcd: global cooldown in seconds
        :return:
        """
        channel = get_channel(message)
        cooldown_object = session.query(Cooldowns)\
            .join(Channels, Channels.channel_id == Cooldowns.channel_id) \
            .where(Channels.channel == channel)\
            .where(Cooldowns.cd_type == 'Global')\
            .first()
        if not cooldown_object:
            cooldown_object = self.insert_cooldown(message, session, gcd, 'Global')
        return cooldown_object

    def get_channel_stats_obj(self, message, session, stat='channel_points') -> UserStats:
        """
        get channel_points UserStats object
        :param message:
        :param session:
        :param stat:
        :return:
        """
        channel=get_channel(message)
        user_id = session.query(Users)\
            .where(Users.user==get_user(message))\
                .first().user_id
        channel_id = session.query(Channels)\
            .where(Channels.channel==channel)\
                .first().channel_id
        stats = session.query(UserStats)\
            .where(UserStats.user_id==user_id)\
            .where(UserStats.stat==stat)\
            .where(UserStats.channel_id==channel_id).first()
        if stats:
            return stats
        else:
            stats = UserStats(user_id=user_id, channel_id=channel_id, stat=stat, stat_value='0')
            session.add(stats)
            self.commit(session)
        return session.query(UserStats)\
            .where(UserStats.user_id==user_id)\
            .where(UserStats.stat==stat)\
            .where(UserStats.channel_id==channel_id).first()

    def get_cooldown_obj(self, message, cd_type, session, cd_length=180) -> Cooldowns:
        """
        Gets cooldown object
        :param message:
        :param cd_type:
        :param session:
        :param cd_length:
        :return:
        """
        user = get_user(message)
        user_obj = self.get_user_obj(user, session)
        cooldown_obj = session.query(Cooldowns)\
            .where(Cooldowns.user_id==user_obj.user_id).where(Cooldowns.cd_type==cd_type).first()
        if not cooldown_obj:
            cooldown_obj = self.insert_cooldown(
                message, session, cd_length, cd_type, user_obj.user_id
            )
        return cooldown_obj

    def insert_cooldown(self, message: str, session, cd_length, cd_type, user_id=None) -> Cooldowns:
        """
        inserts new cooldown type
        :param message:
        :param session:
        :param cd_length:
        :param cd_type:
        :param user_id:
        :return:
        """
        channel = self.get_channel_obj(message, session)
        cooldown_object = Cooldowns(channel_id=channel.channel_id,
                                    user_id=user_id,
                                    cd_type=cd_type,
                                    last_used=0,
                                    length=cd_length)
        session.add(cooldown_object)
        self.commit(session)
        return cooldown_object

    def update_gcd(self, current_time, session, message, length=10):
        """
        Updates global cooldown
        :param current_time:
        :param session:
        :param message:
        :param length:
        :return:
        """
        gcd_obj = self.get_gcd(message, session)
        gcd_obj.last_used = current_time
        gcd_obj.length = length
        self.commit(session)

    def update_user_cd(self, cooldown_obj, current_time, session, length=180):
        """
        Updates user cooldown
        :param cooldown_obj:
        :param current_time:
        :param session:
        :param length:
        :return:
        """
        cooldown_obj.last_used = current_time
        cooldown_obj.length = length
        self.commit(session)

    def get_channel_obj(self, message, session) -> Channels:
        """
        get Channel object
        :param message:
        :param session:
        :return:
        """
        channel_name = get_channel(message)
        return session.query(Channels).where(Channels.channel==channel_name).first()

    def get_stats_obj(self, user: Users, channel: str, stat: str, session) -> UserStats:
        """
        get user stats object of label stat
        :param user:
        :param stat:
        :return:
        """
        channel = session.query(Channels) \
            .where(Channels.channel == channel).first()
        stats_obj = session.query(UserStats) \
            .where(UserStats.user_id == user.user_id) \
            .where(UserStats.channel_id == channel.channel_id)\
            .where(UserStats.stat == stat).first()
        if not stats_obj:
            stats_obj = UserStats(
                user_id=user.user_id,
                channel_id=channel.channel_id,
                stat=stat
            )
        return stats_obj

    def add_channel_owed(self, message: str, stat: str, to_add: int, session, default=1) -> int:
        """
        If channel offers rewards to user this adds to_add to it
        :param message:
        :param stat:
        :param to_add:
        :param default:
        :return:
        """
        stats_obj = self.get_channel_owed(session, message, stat)
        if not stats_obj.stat_value:
            channel_owed = default
            session.add(stats_obj)
        else:
            channel_owed = int(stats_obj.stat_value) + to_add
        if channel_owed < 0:
            channel_owed = 0
        stats_obj.stat_value = channel_owed
        self.commit(session)
        return channel_owed

    def get_user_obj(self, user: str, session) -> Users:
        """
        get user object based on user name
        :param user:
        :param session:
        :return:
        """
        user = session.query(Users).where(Users.user==user).first()
        if not user:
            user = Users(user)
            session.add(user)
            self.commit(session)
        return user

    def get_users_comments(self, user, channel, session) -> [Comments]:
        """
        Gets all users comments
        :return:
        """
        channel = session.query(Channels).where(Channels.channel == channel).first()
        users_comments = session.query(Comments)\
            .join(Users, Comments.user_id == Users.user_id)\
            .where(Users.user == user)\
            .where(Comments.channel_id == channel.channel_id)\
            .all()
        return users_comments

    def _give_chatpoints(self, channel, session):
        """
        Gives chatpoints
        :return:
        """
        users = session.query(ActiveUsers).all()
        stat = 'channel_points'
        for active_user in users:
            if active_user.user_id:
                stats_obj = self.get_stats_obj(active_user, stat, session, channel)
                if not stats_obj.stat_value:
                    stats_obj.stat_value = '1'
                else:
                    new_point = int(stats_obj.stat_value) + 1
                    stats_obj.stat_value = str(new_point)
                session.add(stats_obj)
        self.commit(session)

    @staticmethod
    def get_top_commenters(channel, limit, session):
        """
        gets top commentrs
        :param channel:
        :param limit:
        :param session:
        :return:
        """
        return session.query(Comments.user_id, func.count(Comments.user_id), Users.user) \
            .join(Users, Users.user_id == Comments.user_id) \
            .join(Channels, Channels.channel_id == Comments.channel_id) \
            .where(Channels.channel == channel) \
            .where(Users.user != 'slowspoon') \
            .group_by(Comments.user_id) \
            .order_by(desc(func.count(Comments.user_id))) \
            .limit(limit).all()

    def _update_active_users(self, channel, session, viewers):
        """
        Checks twitch API to see who's in chat and updates active users database accordingly
        :return:
        """
        print('='*50)
        print('Viewers: ' + str(viewers))
        print(f'Number Viewers: {len(viewers)}')
        active_database = session.query(ActiveUsers).all()
        for user in viewers:
            active_obj = session.query(ActiveUsers)\
                .where(ActiveUsers.user == user).first()
            if not active_obj:
                user_obj = session.query(Users).where(Users.user == user).first()
                active_obj = ActiveUsers(user=user, logged_in=time.time())
                if user_obj:
                    active_obj.user_id = user_obj.user_id
                session.add(active_obj)
        for user in active_database:
            if user.user not in viewers:
                session.delete(user)
        self.commit(session)

    def commit(self, session):
        """
        Commits the session with some error handling
        :param session:
        :return:
        """
        try:
            session.commit()
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f'{e}')
            session.rollback()
            session.close()

if __name__ == '__main__':
    pass
    x = MyDatabase('sqlite', dbname='.\\Database\\Chat.db')
    sesh = x.get_session(x.db_engine)
    x.create_db_tables()
