import socket
import re
from Models import Channels, MyDatabase, ActiveUsers
import subprocess
from setup import Config
from gtts import gTTS
import traceback
import threading
import time
from multiprocessing import Process
from swearwords import swear_words
import random
import os
from Parsers import get_channel, get_comment, get_user, parse_message, count_words, is_valid_comment
from datetime import datetime
from blinkytape import BlinkyTape, serial
from dataclasses import dataclass
timestamp_regex = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}'
path_to_vlc = r'C:\Program Files\VideoLAN\VLC\vlc.exe'

swear_words_regex = '|'.join(swear_words)

class Conversions:
    def __init__(self, comment: str):
        """
        container class for weight and temp conversions
        :param comment:
        """
        self.comment: str = comment
        self.to_convert: float = self.get_to_convert(comment)

    def __bool__(self):
        if isinstance(self.to_convert, float):
            return True
        return False

    def __repr__(self):
        return f'to_convert: {self.to_convert}'

    def f_to_c(self, f: float) -> float:
        """
        converts Fahrenheit to Celsius
        :param f: Fahrenheit
        :return: Celsius
        """
        return round((f-32)*(5/9), 1)

    def c_to_f(self, c: float)->float:
        """
        converts celsius to fahrenheit
        :param c: Celsius
        :return: Fahrenheit
        """
        return round((c*1.8)+32, 1)

    def mi_to_km(self, mi: float) -> float:
        """

        :param mi:
        :return:
        """
        return round(mi * 1.60934, 1)

    def km_to_mi(self, km: float) -> float:
        """
        :return:
        """
        return round(1.60934/km, 1)

    def kg_to_pounds(self, kg: float) -> float:
        """

        :param kg:
        :return:
        """
        return round(2.20462262185*kg, 1)

    def pounds_to_kg(self, pounds: float) -> float:
        """

        :param pounds:
        :return:
        """
        return round(pounds/2.20462262185, 1)

    def get_to_convert(self, comment: str) -> float:
        to_convert = comment[len('!convert'):].strip().lower()
        to_convert = re.match('-?\d+(\.\d+)?', to_convert)
        if to_convert:
            return float(to_convert[0])

class Cooldown(MyDatabase):

    def __init__(self):
        super().__init__(dbtype='sqlite', dbname=f'{base_path}\\Database\\Chat.db')
        self.session = self.get_session(self.db_engine)

    def cooldown(self, gcd_cooldown_obj, cooldown_obj, message, current_time) -> str:
        """

        :param message:
        :return:
        """
        global_diff = current_time - gcd_cooldown_obj.last_used
        if global_diff > gcd_cooldown_obj.length:
            user_diff = current_time - cooldown_obj.last_used
            if user_diff > cooldown_obj.length:
                return ''
            else:
                return f'@{get_user(message)} you still got {cooldown_obj.length - int(user_diff)} seconds before you can do that'
        else:
            return f'{gcd_cooldown_obj.length - int(global_diff)} seconds remaining before command available'

@dataclass(order=True, frozen=True)
class ShoutOuts:
    message: str
    seen_today: int = 0
    sound: str = 'defaultshoutout.mp3'

streamer_shoutouts = {
    'PiMPleff'.lower():
        ShoutOuts('The speed skating cyclist musician y\'all already know who it is.',
                  sound='pimp.mp3'),
    'pedalgames':
        ShoutOuts('I once saw this man casually chat while doing a 33 minute alpe.',
                  sound='droctagonapus.mp3'),
    'LepageMaster'.lower():
        ShoutOuts('This man is bigger than a barge, the real Gaston.',
                  sound='policeprincess.mp3'),
    'hardclaws':
        ShoutOuts('Fuck this guy and his silly accent and 1600 watt sprint.',
                  sound='princess.mp3'),
    'cyclingwithdoc':
        ShoutOuts('The army vet with the mostest is here!',
                  sound='smoke.mp3'),
    'zavarise':
        ShoutOuts('Everyones favorite DILF is here!',
                  sound='daddy.mp3'),
    'locutus_of_dei':
        ShoutOuts('His number of grey hairs is only second to his watts,'),
    'bulletfall':
        ShoutOuts('King on the streets queen in the sheets.',
                  sound='moneycount.mp3'),
    'felttie':
       ShoutOuts('One of the few respectable zwifters is here!'),
    'ray_space':
        ShoutOuts('His shorts may be short and he may be slow but at least he\'s balding!',
                  sound='howdigethere.mp3'),
    'barney_nz':
        ShoutOuts('If you ever need to be emasculated by someones pure watts I know just the guy!',
                  sound='nuclear.mp3'),
    'drweebles':
        ShoutOuts('This man\'s raw watts could power a city!'),
    'whyskipdodis':
        ShoutOuts('The actual GOAT of WTRL!'),
    'generalelost':
        ShoutOuts('He does zwift, he plays games, he\'s personally responsible for thousands in charitable donations!'),
    'tepilobium':
        ShoutOuts('The demon of A+ is here!'),
    'ladysirene':
        ShoutOuts('The beauty of burlesque is here!',
                  sound='heygirl.mp3'),
    'pookiebutt':
        ShoutOuts('The bionic man!'),
    'marblehead9':
        ShoutOuts('His in game Zwift fro is almost as cool as him!'),
    'bikebeast':
        ShoutOuts('Biggest biceps in the zwift category!',
                  sound='bb.mp3'),
    'ayeetea':
        ShoutOuts('Blazing fast in iRacing, embarrassingly slow in zwift!'),
    'kyoshirogaming':
        ShoutOuts('Dude takes suffering on the bike to the next level!',
                  sound='kyo.mp3'),
    'debbieinshape':
        ShoutOuts('The beauty of the bike!',
                  sound='heygirl.mp3')
    # 'slowspoon':
    #     ShoutOuts('smoke.mp3', sound='smoke.mp3')
}

chat_shoutouts = {
    'MC_Squared_Racing'.lower():
        ShoutOuts('Say hi to the world record holder for oldest man to operate a computer @{0}!'),
    'notmashingalwaysmyturn':
        ShoutOuts('Best put respect on his name @{0} is here!',
                  sound='dadadada.mp3'),
    'gijsvang':
        ShoutOuts('Holy shit it\'s @{0} quick get the cattle prod!',
                  sound='labmonkey.mp3'),
    'OnlyRideUpHills':
        ShoutOuts('Hey it\'s everyones favorite child sized adult @{0}!',
                  sound='BigBoy.mp3'),
}

class Sounds:

    def __init__(self, base_path):
        """
        Add the file name from the Sounds folder along with desired command here for more sounds
        """
        self.base_path = base_path
        self.sounds = {'!vomit': 'vomit.mp3',
                       '!doicare': 'doicare.mp3',
                       '!shotsfired': 'shots.mp3',
                       '!stopwhining': 'stop_whining.mp3',
                       '!kamehameha': 'kamehameha.mp3',
                       '!daddy': 'daddy.mp3',
                       '!nuclear': 'nuclear.mp3',
                       '!baka': 'baka.mp3',
                       '!nani?!': 'nani.mp3',
                       '!haha': 'haha.mp3',
                       '!heyboys': 'heyboys.mp3',
                       '!discipline': 'discipline.mp3',
                       '!egirl': 'egirl.mp3',
                       '!aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.mp3'}

    def __iter__(self):
        return iter(self.sounds.keys())

    def __getitem__(self, item):
        return self.sounds[item]

    def __contains__(self, item):
        if item in self.sounds:
            return True
        return False

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
                file_number = (int(file_number.group(0))+1)
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
        tts = gTTS(text=text, lang='en')
        file_path = os.path.join(self.base_path, 'Sounds', file_name)
        tts.save(file_path)
        return file_name

    def send_tts_text(self, text):
        """
        save TTS and play it
        :param text:
        :return:
        """
        speed_multiplier = self.get_speed_multiplier(text)
        tts_file_path = self.save_tts(text)
        self.send_sound(tts_file_path, f'--rate={speed_multiplier}')

    @staticmethod
    def get_speed_multiplier(text: str) -> float:
        """
        Play tts faster for longer messages
        This gets the multiplier
        :param text: Text to be sent to TTS, max len 500 for twitch
        :return:
        """
        text_len = len(text)
        if text_len < 150:
            return 1.0
        if text_len < 300:
            return 1.5
        if text_len < 400:
            return 2.0
        return 3.0

    def send_sound(self, sound_filename, *flags):
        """
        PLAYS a sound file using VLC subprocess
        :param sound_filename: str: filename in Sounds folder
        :return:
        """
        file_path = f'{self.base_path}\Sounds\{sound_filename}'
        flags = list(flags)
        p = Process(target=subprocess.run, args=(
            [path_to_vlc, file_path, '--play-and-exit', '--qt-start-minimized'] + flags,
            )
        )
        p.start()

class Messaging:

    def __init__(self, server: str, token: str, nick: str, channel: str, port: str):
        super().__init__()
        self.server = server
        self.token = token
        self.nick = nick
        self.channel = channel
        self.port = port
        self.sock: socket.socket
        # self.define_sock()

    @staticmethod
    def _connect(server, token, nick, channel, port) -> socket.socket:
        """
        :return:
        """
        sock = socket.socket()
        sock.connect((server, port))
        sock.send(f"PASS {token}\r\n".encode('utf-8'))
        sock.send(f"NICK {nick}\r\n".encode('utf-8'))
        sock.send(f"JOIN #{channel}\r\n".encode('utf-8'))
        return sock

    def define_sock(self):
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
        except ConnectionAbortedError:
            self.define_sock()
            self.sock.send(f'PRIVMSG #{self.channel} :{comment}\n'.encode('utf-8'))
        except ConnectionResetError:
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

class BlinkyBoi:
    def __init__(self, port):
        self.bt = BlinkyTape(port)
        self.commands = {'!police': self.police,
                         '!blue': self.blue,
                         '!red': self.red,
                         '!purple': self.purple,
                         '!green': self.green}

    def police(self):
        """
        flash blue and red for a few seconds
        :return:
        """
        time_on = 10
        interval = .4
        for i in range(int(time_on/interval/2)):
            self.bt.alternate_colors((255, 0, 0), (0, 0, 255))
            time.sleep(interval)
            self.bt.alternate_colors((0, 0, 255), (255, 0, 0))
            time.sleep(interval)
        self.default()

    def blue(self):
        self.default()

    def red(self):
        self.bt.displayColor(255,0,0)

    def purple(self):
        self.bt.displayColor(255, 0, 255)

    def green(self):
        self.bt.displayColor(0,255,0)

    def default(self):
        self.bt.displayColor(0,0,255)

class TwitchBot(MyDatabase):
    def __init__(self, dbtype='sqlite'):
        """
        :param dbtype:
        """
        self.twitch_url = 'https://twitch.tv/'
        self.check_out = f'Check them out at {self.twitch_url}'
        self.sounds = Sounds(base_path)
        self.cooldowns = Cooldown()
        sound_commands = ', '.join(self.sounds)
        self.comment_keywords = {'!ftp': 'Current FTP is 321 (3.8 wkg)',
                            '!stats': self.send_stats,
                            '!zp': 'https://www.zwiftpower.com/profile.php?z=2886856',
                            '!strava': 'https://www.strava.com/athletes/58350447',
                            '!swearjar': self.swearjar,
                            '!time': self.send_time,
                            '!convert': '!convert <number><lb/kg/f/c/km/mi>',
                            '!sounds': sound_commands,
                            '!lurk': self.lurk,
                            '!chattyboi': self.chatty_boi,
                            '!trainer': 'My trainer is the Saris H3. I love it',
                            '!bike': 'I ride the 2020 Trek Emonda 105 groupset with Reynolds Blacklabel 65 wheels'}
        self.complements = [
                        '@{0} are you medusa because you make me rock hard!',
                        'Hey @{0}, my name’s Microsoft. Can I crash at your place tonight?',
                        'Hey @{0}, sexy called, they said it was you!',
                        '@{0}, if you were words on a page, you’d be fine print.',
                        'Damn @{0} are you a parking ticket? Because you\'ve got fine written all over you',
                        '@{0} Are you covid? Because you take my breath away!',
                        '@{0} if you were a flower you’d be a damn-delion.',
                        '@{0} you\'re like my pinky toe, because I’m gonna '
                            'bang you on every piece of furniture in the house.',
                        'I’m not into watching sunsets, but I’d love to see you go down @{0}.'
                       ]
        super().__init__(dbtype=dbtype, dbname=f'{base_path}\\Database\\Chat.db')
        self.comment_keywords['!commands'] = self._define_commands(self.comment_keywords)
        self.messaging = Messaging(
            channel=config.channel, server=config.server, nick=config.nick, port=config.port, token=config.token
        )
        self.messaging.define_sock()
        self.sock = self.messaging.sock
        self.channel_obj = None
        if config.channel == 'slowspoon':
            self.my_chat = 1
        else:
            self.my_chat = 0
        self.session = self.get_session(self.db_engine)
        self.check_for_channel()
        for user in self.session.query(ActiveUsers):
            self.session.delete(user)
            self.session.commit()
        try:
            self.bb = BlinkyBoi('COM6')
            self.bb.default()
            self.comment_keywords['!lights'] = self._define_light_commands()
            self.lights = True
        except serial.serialutil.SerialException:
            print("No blinkylight detected")
            self.lights = False

    def _define_light_commands(self):
        return ', '.join(self.bb.commands.keys())

    def main(self):
        """

        :return:
        """
        self.read_chat()

    def check_for_channel(self):
        """
        Checks if channel exists in database, if not create entry for it
        :return:
        """
        channel_obj = self.session.query(Channels)\
            .where(Channels.channel==config.channel).first()
        if not channel_obj:
            channel_obj = Channels(channel=config.channel)
            self.session.add(channel_obj)
        self.session.commit()

    @staticmethod
    def _define_commands(comment_keywords: dict) -> str:
        """
        Truncates command keys into a list to return to users
        :param comment_keywords:
        :return:
        """
        return ', '.join(list(comment_keywords.keys())+['!tts <message>'])

    def read_chat(self):
        """
        Waits for messages to come into chat
        Entry point for every text based command
        :return:
        """
        retry_time = 5
        while True:
            try:
                resp = self.sock.recv(2048).decode('utf-8')
                if resp.startswith('PING'):
                    self.sock.send(resp.replace('PING', 'PONG').encode('utf-8'))
                elif len(resp) > 0:
                    message = parse_message(resp)
                    if is_valid_comment(message):
                        self.save_chat(message)
                        if self.my_chat and not self.timeout_spam(message):
                            self.respond_to_message(message)
                            self.give_shoutout(message)
                            self.send_complement(message)
                            self.check_tts(message)
                            self.check_sound(message)
                            self.conversions(message)
                            self.check_lights(message)
                    print('='*50)
            except Exception as e:
                traceback.print_exc()
                time.sleep(retry_time)
                self.messaging.define_sock()
                self.sock = self.messaging.sock

    def check_lights(self, message):
        """

        :param message:
        :return:
        """
        comment = get_comment(message).lower()
        if self.lights and comment in self.bb.commands:
            try:
                p = Process(target=self.bb.commands[comment]())
                p.start()
            except:
                print("Lights DISCONNECTED")
                self.lights = False

    def timeout_spam(self, message: str) -> bool:
        """
        bigfollows is commonly bot spammed,
        automatically timeout any user who uses it in their comment
        :param message:
        :return:
        """
        comment = get_comment(message)
        if re.search('bigfollow', comment, flags=re.IGNORECASE):
            user = get_user(message)
            print('bigfollow thingy')
            self.messaging.send_message(f'/timeout {user} 60')
            return True
        return False

    def conversions(self, message: str) -> None:
        """
        processes messages and converts units for chat (f/c/kg/pounds)
        :param message:
        :return: None
        """
        comment = get_comment(message)
        keyword = '!convert'
        if comment.startswith(keyword):
            user = get_user(message)
            if self.proper_conversion_comment(comment):
                conversion = Conversions(comment)
                if conversion:
                    return_message = self.get_conversion_return_message(conversion)
                    self.messaging.send_message(return_message + f' @{user}')
            elif len(comment) != len(keyword):
                self.messaging.send_message(
                    f'@{user} The proper format is <Number to convert><Unit to convert>. '
                    'Supports lb/kg/f/c/mi/km'
                )

    def proper_conversion_comment(self, comment) -> bool:
        return bool(re.match(
            '!convert\s-?\d+(\.\d+)?\s?(f|c|kg|lb)\Z',
            comment,
            flags=re.IGNORECASE
        ))

    def get_conversion_return_message(self, conversion: Conversions) -> str:
        """

        :param conversion:
        :return:
        """
        return_message = ''
        to_convert = conversion.to_convert
        comment = conversion.comment
        if comment.endswith('f'):
            if -100 < to_convert < 5000:
                c = conversion.f_to_c(to_convert)
                return_message = f'{to_convert} Fahrenheit is {c} Celsius'
            else:
                return_message = 'Choose a number between -100 and 5000 ya dingus'
        elif comment.endswith('c'):
            if -100 < to_convert < 5000:
                f = conversion.c_to_f(to_convert)
                return_message = f'{to_convert} Celsius is {f} Fahrenheit'
            else:
                return_message = 'Choose a number between -100 and 5000 ya dingus'
        elif comment.endswith('kg'):
            if 0 <= to_convert < 100000:
                pounds = conversion.kg_to_pounds(to_convert)
                return_message = f'{to_convert} kg is {pounds} lbs'
            else:
                return_message = 'Choose a number between 0 and 100000 ya dingus'
        elif comment.endswith('lb'):
            if 0 <= to_convert < 100000:
                kg = conversion.pounds_to_kg(to_convert)
                return_message = f'{to_convert} lbs is {kg} kg'
            else:
                return_message = 'Choose a number between 0 and 100000 ya dingus'
        elif comment.endswith('mi'):
            if 0 <= to_convert < 1000:
                kg = conversion.mi_to_km(to_convert)
                return_message = f'{to_convert} mi is {kg} km'
            else:
                return_message = 'Choose a number between 0 and 10000 ya dingus'
        elif comment.endswith('km'):
            if 0 <= to_convert < 1000:
                kg = conversion.km_to_mi(to_convert)
                return_message = f'{to_convert} km is {kg} mi'
            else:
                return_message = 'Choose a number between 0 and 1000 ya dingus'
        return return_message

    def send_complement(self, message: str):
        """
        Say a nice thing to chat ~2% of the time
        :param message: IRC formatted message
        :return:
        """
        if random.randint(0, 100) == 1:
            user = get_user(message)
            complement_index = random.randint(0, len(self.complements)-1)
            complement = self.complements[complement_index].format(user)
            self.messaging.send_message(complement)

    def send_time(self, *args):
        """
        Sends the time of the current machine to chat
        :param args: dummy var
        :return:
        """
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        send_string = f'The current time is {current_time} (west coast US)'
        self.messaging.send_message(send_string)

    def lurk(self, *args):
        """
        Sends a nice lil message to lurkers who let me know
        :param args:
        :return:
        """
        message = args[0]
        user = get_user(message)
        self.messaging.send_message(f'Thanks for stopping by @{user}! '
                          f'Remember, my followers are objectively better than other people.')

    # def rewards(self, *args):
    #     # self.messaging.send_message('!tts <message> - 10 SpoonBucks')
    #     self.messaging.send_message('!wordcount <username> <word or regular expression> - 10 SpoonBucks, '
    #                       '!breakaway (Attack from the gun in next race, recorded on GoPro and stream after)'
    #                       ' - 1000 SpoonBucks')

    def respond_to_message(self, message: str):
        """
        Responds to keywords defined in self.comment_keywords
        And to SPRINT
        :param message:
        :return:
        """
        comment = get_comment(message)
        user = get_user(message)
        if comment and comment in self.comment_keywords:
            if isinstance(self.comment_keywords[comment], str):
                self.messaging.send_message(self.comment_keywords[comment])
            else:
                self.comment_keywords[comment](message)
        elif re.search('sprint', comment, flags=re.IGNORECASE) and random.randint(0,100) < 20:
            self.messaging.send_message(f'@{user} shutup nerd')
            self.sounds.send_sound('shutup.mp3')

    def give_shoutout(self, message: str):
        """
        Certain users frequent my chat, this gives them a shoutout with an audio cue!
        :param message: IRC formatted message
        :return:
        """
        user = get_user(message)
        response = ''
        if user.lower() in streamer_shoutouts and streamer_shoutouts[user.lower()].seen_today == 0:
            streamer = streamer_shoutouts[user.lower()]
            streamer.seen_today = 1
            response = f'@{user} ' + streamer.message + f' {self.check_out}{user}.'
            if streamer.sound:
                self.sounds.send_sound(streamer.sound)
        elif user.lower() in chat_shoutouts and chat_shoutouts[user.lower()].seen_today==0:
            chatter = chat_shoutouts[user]
            chatter.seen_today = 1
            response = chatter.message.format(user)
            if chatter.sound:
                self.sounds.send_sound(chatter.sound)
        if response:
            self.messaging.send_message(response)

    def check_sound(self, message):
        """
        Checks chat to see if sound command was sent
        Sends it if so
        :param message:
        :return:
        """
        comment = get_comment(message)
        if comment in self.sounds:
            sound_filename = self.sounds[comment]
            print(f'sound filename: {sound_filename}')
            self.sounds.send_sound(sound_filename)

    def check_tts(self, message):
        """
        If user uses !tts command sends it on stream
        :param message:
        :return:
        """
        comment = get_comment(message)
        if comment.startswith('!tts'):
            cd_type = 'tts_user'
            current_time = time.time()
            text = self.fix_tts_text(get_comment(message))
            length = 60
            gcd_cooldown_obj = self.get_gcd(message, self.session)
            cooldown_obj = self.get_cooldown_obj(
                message=message, cd_type=cd_type, cd_length=length, session=self.session
            )
            cooldown = self.cooldowns.cooldown(
                gcd_cooldown_obj=gcd_cooldown_obj, cooldown_obj=cooldown_obj, message=message,
                current_time=current_time
            )
            if not cooldown:
                self.sounds.send_tts_text(text)
                self.update_gcd(current_time, self.session, message)
                self.update_user_cd(cooldown_obj, current_time, self.session, length=length)
            else:
                self.messaging.send_message(cooldown)

    @staticmethod
    def fix_tts_text(text):
        char_whitelist = '[^A-Za-z0-9\',.\s\?]+'
        text = text[4:]
        text = re.sub('!', '.', text)
        text = re.sub(char_whitelist, '', text)
        return text

    def send_stats(self, message):
        stats = self.get_channel_stats_obj(message, session=self.session)
        if stats != '0':
            points = stats.stat_value
            send_string = f'You have {points} Spoon Bucks!'
        else:
            send_string = 'You have NO POINTS GET THE F*CK OUT (jk). ' \
                          'But seriously you have no points, hang out in chat more and ' \
                          'don\'t forget to keep your volume on.'
        self.messaging.send_message(send_string)

    def swearjar(self, message: str):
        user = get_user(message)
        channel = config.channel
        comment_list = self.get_users_comments(user=user, channel=channel, session=self.session)
        times_sworn = count_words(comment_list, swear_words)
        swear_ratio = str(times_sworn/len(comment_list))
        if len(swear_ratio) >= 4:
            swear_ratio = swear_ratio[:4]
        self.messaging.send_message(f'You have sworn {times_sworn} times.'
                          f' Your ratio of swear words to total comments is {swear_ratio}')

    def chatty_boi(self, message: str):
        """

        :param message:
        :return:
        """
        channel = get_channel(message)
        top_commenters = self.get_top_commenters(session=self.session, limit=3, channel=channel)
        number1 = top_commenters[0]
        number2 = top_commenters[1]
        number3 = top_commenters[2]
        self.messaging.send_message(f'@{number1.user} is the chattiest boi, having sent {number1[1]} messages.'
                          f' #2: @{number2.user} with {number2[1]}.'
                          f' #3: @{number3.user} with {number3[1]}')

    def save_chat(self, message: str):
        """

        :param message:
        :return:
        """
        return_comment = self.write_message(message, self.session)
        if self.my_chat and return_comment:
            self.messaging.send_message(return_comment)
            self.sounds.send_sound('cheering.mp3')

    def is_not_keyword(self, message: str) -> bool:
        """

        :param message:
        :return:
        """
        comment = get_comment(message)
        if comment not in self.comment_keywords and comment not in self.comment_keywords.values():
            return True
        return False

class ActiveUserProcess(MyDatabase):

    def __init__(self, token, server,
                       port, nick, channel, base_path, dbtype='sqlite'
                 ):
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
        self.channel = channel
        self.sounds = Sounds(self.base_path)
        self.messaging = Messaging(
            channel=self.channel, server=self.server, nick=self.nick, port=self.port, token=self.token
        )
        self.session = None
        self.tb = None
        self.main()

    def main(self):
        """
        :return:
        """
        self.session = self.get_session(self.db_engine)
        update_interval = 60
        time_streamed = 0
        intervals_for_ad = 15
        while True:
            self._give_chatpoints(session=self.session, channel=self.channel)
            self._update_active_users(session=self.session, channel=self.channel)
            time.sleep(update_interval)
            if time_streamed%(intervals_for_ad*update_interval) == 0:
                self.send_info()
            time_streamed += update_interval

    def send_info(self):
        """
        Send stream info periodically
        :return:
        """
        message = '!commands to see all the fun shit you can do. Don\'t forget to follow!'
        try:
            with self.messaging as _:
                time.sleep(.1)
                self.sounds.send_sound('follow.mp3')
                self.messaging.send_message(message)
                print('Sent ad')
        except:
            traceback.print_exc()

if __name__ == '__main__':
    pass
    config = Config()
    base_path = config.base_path
    tb = TwitchBot(
        dbtype=config.dbtype
    )
    p = Process(target=ActiveUserProcess, kwargs={"token":config.token, "server":config.server,
        "port":config.port, "nick":config.nick, "channel":config.channel, "base_path":config.base_path})
    p.start()
    tb.main()
