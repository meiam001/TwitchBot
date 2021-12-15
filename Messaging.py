import socket
from Parsers import parse_message, is_valid_comment
import log
import traceback
import time
import threading
logger = log.logging.getLogger(__name__)

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

    def read_chat(self, name='') -> str:
        retry_time = 5
        try:
            resp = self.sock.recv(2048).decode('utf-8')
            if resp.startswith('PING'):
                self.sock.send(resp.replace('PING', 'PONG').encode('utf-8'))
            elif len(resp) > 0:
                message = parse_message(resp)
                if not message:
                    self.define_sock()
                if is_valid_comment(message):
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
            time.sleep(.1)
            logger.error(f'{e}')
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
