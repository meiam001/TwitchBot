import socket
import log
import traceback
import time
import re
import threading
logger = log.logging.getLogger(__name__)

class Message:

    def __init__(self, resp):
        self.resp = resp
        self.message = self.parse_message(resp)
        self.comment = self.get_comment(self.message)
        self.channel = self.get_channel(self.message)
        self.user = self.get_user(self.message)
        self.is_valid_comment = self.is_valid_comment(self.message)

    def __bool__(self):
        return bool(self.message)

    @staticmethod
    def parse_message(resp: str) -> str:
        """

        :param resp:
        :return:
        """
        regex_parse = ':([a-zA-Z0-9_]*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #([a-zA-Z0-9_]*) :(.*)'
        if re.search(regex_parse, resp):
            resp = str(resp)
            username, channel, message = re.search(regex_parse, resp).groups()
            return f"Channel: {channel} \nUsername: {username} \nMessage: {message}"
        else:
            return resp

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


class Messaging:
    failed = ':tmi.twitch.tv NOTICE * :Login unsuccessful'

    def __init__(self, config):
        self.server = config.server
        self.token = config.token
        self.nick = config.nick
        self.channel = config.channel
        self.port = config.port
        self.sock: socket.socket
        # self.define_sock()

    @staticmethod
    def _connect(server: str, token: str, nick: str, channel: str, port: str) -> socket.socket:
        """
        :return:
        """
        sock = socket.socket()
        sock.connect((server, port))
        sock.send(f"PASS {token}\r\n".encode('utf-8'))
        sock.send(f"NICK {nick}\r\n".encode('utf-8'))
        sock.send(f"JOIN #{channel}\r\n".encode('utf-8'))
        return sock

    def read_chat(self, name='') -> Message:
        retry_time = 5
        try:
            resp = self.sock.recv(2048).decode('utf-8')
            if resp.startswith('PING'):
                self.sock.send(resp.replace('PING', 'PONG').encode('utf-8'))
            elif len(resp) > 0:
                message = Message(resp)
                if not message:
                    self.define_sock()
                if message.is_valid_comment:
                    return message
        except Exception as e:
            logger.error(f'{e}')
            traceback.print_exc()
            time.sleep(retry_time)
            self.define_sock()

    def define_sock(self):
        print('Connecting to socket...')
        self.sock = self._connect(
            self.server, self.token, self.nick, self.channel, self.port
        )

    def __enter__(self):
        self.define_sock()
        return self.sock

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sock.close()

    def send_message(self, comment: str):
        """
        Sends a comment to chat defined in config file
        Attempts to send message one additional time if fails
        :param comment: str: text to be sent
        :return:
        """
        try:
            self.sock.send(f'PRIVMSG #{self.channel} :{comment}\n'.encode('utf-8'))
        except ConnectionAbortedError or ConnectionResetError as e:
            time.sleep(.3)
            logger.error(f'{e}\n{comment}')
            self.define_sock()
            self.sock.send(f'PRIVMSG #{self.channel} :{comment}\n'.encode('utf-8'))

    def PONG(self):
        threading.Thread(target=self._PONG)

    def _PONG(self):
        while True:
            resp = self.sock.recv(2048).decode('utf-8')
            if resp.startswith('PING'):
                print('\n\n\n\nPONG SENT FROM MESSAGING\n\n\n\n')
                self.sock.send(resp.replace('PING', 'PONG').encode('utf-8'))


