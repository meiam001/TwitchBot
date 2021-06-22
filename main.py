import socket
import re
from Models import Users, Comments, Channels, MyDatabase, ActiveUsers, UserStats
from sqlalchemy import func, desc
from playsound import playsound
from setup import Config
import requests
import time
from multiprocessing import Process
from swearwords import swear_words
import random

timestamp_regex = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}'

swear_words_regex = '|'.join(swear_words)

class TwitchBot(MyDatabase):
    def __init__(self, token, server, port, nick, channel, base_path, dbtype='sqlite'):
        """

        :param token:
        :param server:
        :param port:
        :param nick:
        :param channel:
        :param base_path:
        :param dbtype:
        """
        self.comment_keywords = {'!ftp': 'My current FTP is 325',
                            '!strava': 'https://www.strava.com/athletes/58350447',
                            '!swearjar': self.swearjar,
                            '!tv': self.tv,
                            '!chattyboi': self.chatty_boi,
                            '!trainer': 'My trainer is the Saris H3. I love it',
                            '!bike': 'I ride the 2020 Trek Emonda 105 groupset with Reynolds Blacklabel 65 wheels'}
        self.complements = [
                        'Damn @{0} you be lookin fly today!',
                        'Hey @{0}, sexy called, they said it was you!',
                        '@{0} if you were a vegetable you\'d be a cute-cumber!',
                        'Damn @{0} are you a parking ticket? Because you\'ve got fine written all over you',
                        '@{0}, If you were a transformer you\'d be Optimus FINE'
                       ]
        super().__init__(dbtype=dbtype, dbname=f'{base_path}\\Database\\Chat.db')
        self.comment_keywords['!commands'] = self._define_commands(self.comment_keywords)
        self.token = token
        self.server = server
        self.port = port
        self.base_path = base_path
        self.nick = nick
        self.channel = f'#{channel}'
        self.sock = self._connect()
        self.channel_obj = None
        if self.channel[1:] == 'slowspoon':
            self.my_chat = 1
        else:
            self.my_chat = 0
        self.session = self.get_session(self.db_engine)
        self.check_for_channel()
        for user in self.session.query(ActiveUsers):
            self.session.delete(user)
            self.session.commit()

    def main(self):
        """

        :return:
        """
        self.read_chat()

    def check_for_channel(self):
        """

        :return:
        """
        channel_obj = self.session.query(Channels)\
            .where(Channels.channel==self.channel[1:]).first()
        if not channel_obj:
            channel_obj = Channels(channel=self.channel[1:])
            self.session.add(channel_obj)
        self.session.commit()

    @staticmethod
    def _define_commands(comment_keywords: dict) -> str:
        """

        :param comment_keywords:
        :return:
        """
        return ', '.join(comment_keywords.keys())

    def _connect(self) -> socket.socket:
        """

        :return:
        """
        sock = socket.socket()
        sock.connect((self.server, self.port))
        sock.send(f"PASS {self.token}\r\n".encode('utf-8'))
        sock.send(f"NICK {self.nick}\r\n".encode('utf-8'))
        sock.send(f"JOIN {self.channel}\r\n".encode('utf-8'))
        return sock

    def send_message(self, message: str):
        """

        :param message:
        :return:
        """
        self.sock.send(f'PRIVMSG {self.channel} :{message}\n'.encode('utf-8'))

    def read_chat(self):
        """

        :return:
        """
        while True:
            resp = self.sock.recv(2048).decode('utf-8')
            if resp.startswith('PING'):
                self.sock.send(resp.replace('PING', 'PONG').encode('utf-8'))
                print('PONGAROO SENT')
            elif len(resp) > 0:
                message = self._parse_message(resp)
                if self.is_valid_comment(message):
                    if self.my_chat:
                        self.respond_to_message(message)
                    if self.is_not_keyword(message):
                        self.save_chat(message)
                        if self.my_chat:
                            self.send_complement(message)
                print('='*50)

    def send_complement(self, message: str):
        """

        :param message:
        :return:
        """
        if random.randint(0, 100) < 8:
            user = self.get_user(message)
            complement_index = random.randint(0, len(self.complements)-1)
            complement = self.complements[complement_index].format(user)
            self.send_message(complement)

    @staticmethod
    def _parse_message(resp: str) -> str:
        """

        :param resp:
        :return:
        """
        regex_parse = ':([a-zA-Z0-9_]*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #([a-zA-Z0-9_]*) :(.*)'
        if re.search(regex_parse, resp):
            resp = str(resp)
            print(resp.strip())
            username, channel, message = re.search(regex_parse, resp).groups()
            return f"Channel: {channel} \nUsername: {username} \nMessage: {message}"
        else:
            return resp

    def respond_to_message(self, message: str):
        """

        :param message:
        :return:
        """
        comment = self.get_comment(message)
        if comment and comment in self.comment_keywords:
            if isinstance(self.comment_keywords[comment], str):
                self.send_message(self.comment_keywords[comment])
            else:
                self.comment_keywords[comment](message)

    def swearjar(self, message: str):
        comment_list = self.get_users_comments(message)
        times_sworn = self.count_swearwords(comment_list)
        self.send_message(f'You have sworn {times_sworn} times')

    def chatty_boi(self, message: str):
        """

        :param message:
        :return:
        """
        channel = self.get_channel(message)
        top_commenter = self.session.query(Comments.user_id, func.count(Comments.user_id), Users.user)\
            .join(Users, Users.user_id==Comments.user_id)\
            .join(Channels, Channels.channel_id==Comments.channel_id)\
            .where(Channels.channel==channel)\
            .where(Users.user!='slowspoon')\
            .group_by(Comments.user_id)\
            .order_by(desc(func.count(Comments.user_id)))\
            .first()
        number_comments = top_commenter[1]
        commenter_name = top_commenter.user
        self.send_message(f'@{commenter_name} is the chattiest boi, having sent {number_comments} messages')

    def tv(self, *args):
        """

        :param args: dummy args
        :return:
        """
        if self.my_chat:
            Process(target=playsound, args=(f'{self.base_path}\Sounds\watchTV.mp3',)).start()

    @staticmethod
    def count_swearwords(comment_list: list) -> int:
        """

        :param comment_list:
        :return:
        """
        comment_string = '\n'.join([x.comment for x in comment_list])
        times_sworn = len(re.findall(swear_words_regex, comment_string, flags=re.IGNORECASE))
        return times_sworn

    def get_users_comments(self, message: str) -> [Comments]:
        """

        :param message:
        :return:
        """
        user = self.get_user(message)
        users_comments = self.session.query(Comments)\
            .join(Users, Comments.user_id==Users.user_id)\
            .where(Users.user==user).all()
        return users_comments

    def save_chat(self, message: str):
        """

        :param message:
        :return:
        """
        self.write_message(message)

    def is_not_keyword(self, message: str) -> bool:
        """

        :param message:
        :return:
        """
        comment = self.get_comment(message)
        if comment not in self.comment_keywords and comment not in self.comment_keywords.values():
            return True
        return False

    def write_message(self, message: str):
        """

        :param message:
        :return:
        """
        user = self.get_user(message)
        comment = self.get_comment(message)
        channel = self.get_channel(message)
        user_obj = self.session.query(Users).where(Users.user==user).first()
        channel_obj = self.session.query(Channels).where(Channels.channel==channel).first()
        if user_obj:
            self.commit_comment_exists(comment, user_obj, channel_obj)
        else:
            self.commit_comment_dne(comment, user, user_obj, channel_obj)

    def commit_comment_exists(self, comment: str, user_obj: Users, channel_obj: Channels):
        """

        :param comment:
        :param user_obj:
        :param channel_obj:
        :return:
        """
        comment_obj = Comments(comment=comment, user_id=user_obj.user_id, channel_id=channel_obj.channel_id)
        self.session.add(comment_obj)
        self.session.commit()

    def commit_comment_dne(self, comment: str, user: str, user_obj: Users, channel_obj: Channels):
        """

        :param comment:
        :param user:
        :param user_obj:
        :param channel_obj:
        :return:
        """
        if not user_obj:
            user_obj = Users(user=user)
            if self.my_chat:
                self.send_message(f'It\'s @{user}\'s first time in chat! Say hi!')
            self.session.add(user_obj)
            self.session.commit()
        comment_obj = Comments(comment=comment, user_id=user_obj.user_id, channel_id=channel_obj.channel_id)
        self.session.add(comment_obj)
        self.session.commit()

    def is_valid_comment(self, message: str) -> bool:
        """

        :param message:
        :return:
        """
        user = self.get_user(message)
        comment = self.get_comment(message)
        channel = self.get_channel(message)
        if user and comment and channel:
            return True
        return False

    @staticmethod
    def get_user(message: str) -> str:
        """

        :param message:
        :return:
        """
        split_message = message.split('\n')
        if len(split_message) == 3:
            message_user = split_message[1]
            if message_user.startswith('Username: '):
                user = message_user[len('Username: '):].strip()
                return user
        return ''

    @staticmethod
    def get_comment(message: str) -> str:
        """

        :param message:
        :return:
        """
        split_message = message.split('\n')
        if len(split_message) == 3:
            message_comment = split_message[2]
            if message_comment.startswith('Message: '):
                comment = message_comment[len('Message: '):].strip()
                return comment
        return ''

    @staticmethod
    def get_channel(message: str) -> str:
        """

        :param message:
        :return:
        """
        split_message = message.split('\n')
        if len(split_message) == 3:
            message_channel = split_message[0]
            if message_channel.startswith('Channel: '):
                channel = message_channel[len('Channel: '):].strip()
                return channel
        return ''

class ActiveUserProcess(MyDatabase):

    def __init__(self, token, server,
                       port, nick, channel, base_path, dbtype='sqlite'):
        """

        :param token:
        :param server:
        :param port:
        :param nick:
        :param channel:
        :param base_path:
        """
        super().__init__(dbtype=dbtype, dbname=f'{base_path}\\Database\\Chat.db')
        self.token = token
        self.server = server
        self.port = port
        self.base_path = base_path
        self.nick = nick
        self.channel = f'#{channel}'
        self.session = None
        self.tb = None
        self.main()

    def main(self):
        """

        :return:
        """
        self.session = self.get_session(self.db_engine)
        update_interval = 60
        while True:
            self._give_chatpoints()
            self._update_active_users()
            time.sleep(update_interval)

    def _get_current_viewers(self) -> [str]:
        """

        :return:
        """
        channel_viewers = f'https://tmi.twitch.tv/group/user/{self.channel[1:]}/chatters'
        r = requests.get(channel_viewers)
        if r.status_code == 200:
            viewer_json = r.json()
            viewers = viewer_json['chatters']['viewers']
            print(viewers)
            return viewers
        return []

    def _give_chatpoints(self):
        """

        :return:
        """
        users = self.session.query(ActiveUsers).all()
        stat = 'channel_points'
        for active_user in users:
            if active_user.user_id:
                stats_obj = self.get_stats_obj(active_user, stat)
                if not stats_obj.stat_value:
                    stats_obj.stat_value = '1'
                else:
                    new_point = int(stats_obj.stat_value) + 1
                    stats_obj.stat_value = str(new_point)
                self.session.add(stats_obj)
        self.session.commit()

    def get_stats_obj(self, user: Users, stat: str) -> UserStats:
        """

        :param user:
        :param stat:
        :return:
        """
        channel = self.session.query(Channels) \
            .where(Channels.channel == self.channel[1:]).first()
        stats_obj = self.session.query(UserStats) \
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

    def _update_active_users(self):
        """
        Checks twitch API to see who's in chat and updates active users database accordingly
        :return:
        """
        viewers = self._get_current_viewers()
        print('Viewers: ' + str(viewers))
        active_database = self.session.query(ActiveUsers).all()
        for user in viewers:
            active_obj = self.session.query(ActiveUsers)\
                .where(ActiveUsers.user == user).first()
            if not active_obj:
                user_obj = self.session.query(Users).where(Users.user == user).first()
                active_obj = ActiveUsers(user=user, logged_in=time.time())
                if user_obj:
                    active_obj.user_id = user_obj.user_id
                self.session.add(active_obj)
        for user in active_database:
            if user.user not in viewers:
                self.session.delete(user)
        self.session.commit()


if __name__ == '__main__':
    config = Config()
    tb = TwitchBot(
        token=config.token, server=config.server,
        port=config.port, nick=config.nick, channel=config.channel, base_path=config.base_path, dbtype=config.dbtype
    )
    Process(target=ActiveUserProcess, kwargs={"token":config.token, "server":config.server,
        "port":config.port, "nick":config.nick, "channel":config.channel, "base_path":config.base_path}).start()
    tb.main()
