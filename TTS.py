from Models import MyDatabase, Cooldowns
import pyttsx3
from Sounds import Sounds
from Messaging import Messaging, Message
from setup import Config
import threading
import time
import re
import os

config = Config()

class Cooldown:

    @staticmethod
    def cooldown(gcd_cooldown_obj: Cooldowns, cooldown_obj: Cooldowns, message: Message, current_time) -> str:
        """
        Deals with cooldowns easily
        :param gcd_cooldown_obj:
        :param cooldown_obj:
        :param message:
        :param current_time:
        :return:
        """
        global_diff = current_time - gcd_cooldown_obj.last_used
        if global_diff > gcd_cooldown_obj.length:
            user_diff = current_time - cooldown_obj.last_used
            if user_diff > cooldown_obj.length:
                return ''
            else:
                return f'@{message.user} you still got ' \
                       f'{cooldown_obj.length - int(user_diff)} seconds before you can do that'
        else:
            return f'{gcd_cooldown_obj.length - int(global_diff)} seconds remaining before command available'


class TTSProcess(MyDatabase):
    user_cd = 60
    global_cd = 0
    def __init__(self, dbtype='sqlite', base_path='.'):
        """
        Process that deals with users text to speech.
        !tts <message>
        :param dbtype: currently only supports sqlite
        :param base_path: base path for bot
        """
        super().__init__(dbtype=dbtype, dbname=f'{base_path}\\Database\\Chat.db')
        # time.sleep(5)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.base_path = base_path
        self.sounds = Sounds(base_path)
        self.cooldowns = Cooldown()
        ttsp = threading.Thread(target=self.tts_read_chat)
        ttsp.start()

    def tts_read_chat(self):
        """
        Reads chat to react to !tts
        """
        time.sleep(3)
        self.messaging = Messaging(config)
        self.messaging.define_sock()
        while True:
            message = self.messaging.read_chat()
            if message:
                self.check_tts(message)

    def check_tts(self, message: Message):
        """
        If user uses !tts command sends it on stream
        :param message:
        :return:
        """
        comment = message.comment
        if comment.startswith('!tts'):
            session = self.get_session(self.db_engine)
            print(f'tts comment: {comment}')
            cd_type = 'tts_user'
            current_time = time.time()
            text = self.fix_tts_text(message.comment)
            user_cd = self.user_cd
            global_cd = self.global_cd
            gcd_obj = self.get_gcd(message, session)
            gcd_obj.length = global_cd
            cooldown_obj = self.get_cooldown_obj(
                message=message, cd_type=cd_type, cd_length=user_cd, session=session
            )
            cooldown = self.cooldowns.cooldown(
                gcd_cooldown_obj=gcd_obj, cooldown_obj=cooldown_obj, message=message,
                current_time=current_time
            )
            if not cooldown:
                self.update_gcd(current_time, session, message)
                self.update_user_cd(cooldown_obj, current_time, session, length=user_cd)
                session.close()
                self.send_tts_text(text)
            else:
                self.messaging.send_message(cooldown)
                session.close()


    @staticmethod
    def fix_tts_text(text: str) -> str:
        """
        People spam dumb annoying shit so, whitelist alphanumeric, ignore rest
        :param text: !tts <message>
        :return:
        """
        char_whitelist = '[^A-Za-z0-9\',.\s\?!]+'
        text = text[4:]
        text = re.sub(char_whitelist, '', text)
        return text

    def generate_tts_filename(self, file_name='tts0.mp3') -> str:
        """
        Recursively checks for file names for TTS,
        If file is currently being played add one and try again.
        Otherwise delete file and return current file_name
        :param file_name:
        :return: str: unused file name for text to speech
        """
        sounds_path = os.path.join(self.base_path, 'Sounds')
        sounds_dir = os.listdir(sounds_path)
        if file_name in sounds_dir:
            file_path = os.path.join(sounds_path, file_name)
            try:
                os.remove(file_path)
            except PermissionError:
                file_number = re.search('\d+', file_name)
                file_number = (int(file_number.group(0)) + 1)
                file_name = re.sub('\d+', str(file_number), file_name, count=1)
                return self.generate_tts_filename(file_name)
        return file_name

    def save_tts(self, text: str) -> str:
        """
        generates a TTS file and returns the file name
        :param text: desired TTS
        :return: str: file path to tts file
        """
        file_name = self.generate_tts_filename()
        file_path = os.path.join(self.base_path, 'Sounds', file_name)
        self.engine.save_to_file(text, file_path)
        self.engine.runAndWait()
        return file_name

    def send_tts_text(self, text: str):
        """
        save TTS and play it
        :param text:
        :return:
        """
        new_process = False
        speed_multiplier = self.sounds.get_speed_multiplier(text)
        tts_file_path = self.save_tts(text)
        self.sounds.send_sound(tts_file_path, new_process, f'--rate={speed_multiplier}')
