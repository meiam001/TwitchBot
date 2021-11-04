import socket
import re
from Models import Users, Comments, Channels, MyDatabase, ActiveUsers, UserStats
import subprocess
from setup import Config
from gtts import gTTS
import traceback
import time
from multiprocessing import Process
from swearwords import swear_words
import random
import os
from Parsers import get_channel, get_comment, get_user, parse_message, count_words, is_valid_comment
from datetime import datetime

timestamp_regex = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}'
path_to_vlc = r'C:\Program Files\VideoLAN\VLC\vlc.exe'

swear_words_regex = '|'.join(swear_words)

class Cooldowns(MyDatabase):

    def __init__(self, tts_global=10, tts_users=180):
        super().__init__(dbtype='sqlite', dbname=f'{base_path}\\Database\\Chat.db')
        self.session = self.get_session(self.db_engine)
        self.tts_global = tts_global
        self.tts_user = tts_users
        self.tts_users_times = {'global': 0}

    def cooldown(self, message, cd_type: str, _times: str) -> str:
        """

        :param message:
        :param cd_type:
        :param _times:
        :return:
        """
        current_time = time.time()
        gcd_cooldown_obj = self.get_gcd(message, self.session)
        length = getattr(self, cd_type)
        cooldown_obj = self.get_cooldown_obj(message, cd_type, length, self.session)
        global_diff = current_time - gcd_cooldown_obj.last_used
        if global_diff > gcd_cooldown_obj.length:
            user = get_user(message)
            user_diff = current_time - cooldown_obj.last_used
            if user_diff > length:
                self.update_user_cd(cooldown_obj, current_time, self.session)
                self.update_gcd(current_time, self.session, message)
                return ''
            else:
                return f'@{user} you still got {length - int(user_diff)} seconds before you can do that'
        else:
            return f'{gcd_cooldown_obj.length - int(global_diff)} seconds remaining before command available'

class ShoutOuts:

    def __init__(self, message: str, seen_today=0, sound='defaultshoutout.mp3'):
        """

        :param message:
        :param seen_today:
        :param sound:
        """
        self.seen_today = seen_today
        self.message = message
        self.sound = sound

streamer_shoutouts = {
    'LepageMaster'.lower():
        ShoutOuts('This man is bigger than a barge, the real Gaston.',
                  sound='policeprincess.mp3'),
    'hardclaws':
        ShoutOuts('Fuck this guy and his silly accent.',
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
        ShoutOuts('This man is LOADED, make sure to ask him for money.',
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
}

class Sounds:

    def __init__(self, base_path):
        """
        Add the file name from the Sounds folder along with desired command here for more sounds
        """
        self.base_path = base_path
        self.sounds = {'!vomit': 'vomit.mp3',
                       '!doicare': 'doicare.mp3',
                       '!stopwhining': 'stop_whining.mp3',
                       '!kamehameha': 'kamehameha.mp3',
                       '!spoonsproblem': 'premature_ejaculation.mp3',
                       '!daddy': 'daddy.mp3',
                       '!goodbye': 'goodbye.mp3',
                       '!pain': 'struggle.mp3',
                       '!showtime': 'showtime.mp3',
                       '!thug': 'thug.mp3',
                       '!shit': 'shit.mp3',
                       '!nuclear': 'nuclear.mp3',
                       '!baka': 'baka.mp3',
                       '!ekeseplosion': 'ekeseplosion.mp3',
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
        tts = gTTS(text=text, lang='en', tld='com.au')
        file_path = os.path.join(self.base_path, 'Sounds', file_name)
        tts.save(file_path)
        return file_name

    def send_sound(self, sound_filename):
        """
        PLAYS a sound file using VLC subprocess
        :param sound_filename: str: filename in Sounds folder
        :return:
        """
        file_path = f'{self.base_path}\Sounds\{sound_filename}'
        p = Process(target=subprocess.run, args=(
            [path_to_vlc, file_path, '--play-and-exit', '--qt-start-minimized'],)
        )
        p.start()

class Messaging:

    def __init__(self, server: str, token: str, nick: str, channel: str, port: str):
        self.server = server
        self.token = token
        self.nick = nick
        self.channel = channel
        self.port = port
        self.sock = self.define_sock()

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

    def define_sock(self) -> socket.socket:
        return self._connect(self.server, self.token, self.nick, self.channel, self.port)

    def send_message(self, comment: str):
        """
        Sends a comment to chat defined in config file
        :param comment: str: text to be sent
        :return:
        """
        self.sock.send(f'PRIVMSG #{self.channel} :{comment}\n'.encode('utf-8'))


class TwitchBot(MyDatabase):
    def __init__(self, dbtype='sqlite'):
        """
        :param dbtype:
        """
        self.twitch_url = 'https://twitch.tv/'
        self.check_out = f'Check them out at {self.twitch_url}'
        self.sounds = Sounds(base_path)
        self.cooldowns = Cooldowns(tts_global=10, tts_users=180)
        sound_commands = ''
        for sound in self.sounds:
            sound_commands += f'{sound}, '
        self.comment_keywords = {'!ftp': 'Literally no idea',
                            # '!spoonbucks': self.send_stats,
                            '!zp': 'https://www.zwiftpower.com/profile.php?z=2886856',
                            '!strava': 'https://www.strava.com/athletes/58350447',
                            '!swearjar': self.swearjar,
                            '!time': self.send_time,
                            '!sounds': sound_commands,
                            '!lurk': self.lurk,
                            # '!rewards': self.rewards,
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
        self.reward_handler = RewardHandler(
            base_path=config.base_path, channel=config.channel, session=self.session
        )

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

    def send_message(self, comment: str):
        """
        Sends a comment to chat defined in config file
        :param comment: str: text to be sent
        :return:
        """
        self.sock.send(f'PRIVMSG #{config.channel} :{comment}\n'.encode('utf-8'))

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
                        if self.my_chat:
                            self.respond_to_message(message)
                            self.give_shoutout(message)
                            self.send_complement(message)
                            self.check_tts(message)
                            self.check_sound(message)
                            reward_response = self.reward_handler.main(message)
                            if reward_response and isinstance(reward_response, str):
                                self.send_message(reward_response)
                    print('='*50)
            except Exception as e:
                traceback.print_exc()
                time.sleep(retry_time)
                self.messaging.define_sock()

    def send_complement(self, message: str):
        """
        Say a nice thing to chat ~2% of the time
        :param message: IRC formatted message
        :return:
        """
        if random.randint(0, 100) < 2:
            user = get_user(message)
            complement_index = random.randint(0, len(self.complements)-1)
            complement = self.complements[complement_index].format(user)
            self.send_message(complement)

    def send_time(self, *args):
        """
        Sends the time of the current machine to chat
        :param args: dummy var
        :return:
        """
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        send_string = f'The current time is {current_time} (west coast US)'
        self.send_message(send_string)

    def lurk(self, *args):
        """
        Sends a nice lil message to lurkers who let me know
        :param args:
        :return:
        """
        message = args[0]
        user = get_user(message)
        self.send_message(f'Thanks for stopping by @{user}! '
                          f'Remember, my followers are objectively better than other people.')

    # def rewards(self, *args):
    #     # self.send_message('!tts <message> - 10 SpoonBucks')
    #     self.send_message('!wordcount <username> <word or regular expression> - 10 SpoonBucks, '
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
                self.send_message(self.comment_keywords[comment])
            else:
                self.comment_keywords[comment](message)
        elif re.search('sprint', comment, flags=re.IGNORECASE) and random.randint(0,100) < 20:
            self.send_message(f'@{user} shutup nerd')
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
            self.send_message(response)

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
            cooldown = self.cooldowns.cooldown(message, 'tts_user', 'tts_users_times')
            if not cooldown:
                text = ''
                tts_list = comment.split('!tts')
                if len(tts_list) > 1:
                    text = tts_list[1]
                if text.strip():
                    tts_file_path = self.sounds.save_tts(text)
                    self.sounds.send_sound(tts_file_path)
            else:
                self.send_message(cooldown)

    def send_stats(self, message):
        stats = self.get_channel_stats_obj(message)
        if stats != '0':
            points = stats.stat_value
            send_string = f'You have {points} Spoon Bucks!'
        else:
            send_string = 'You have NO POINTS GET THE F*CK OUT (jk). ' \
                          'But seriously you have no points, hang out in chat more and ' \
                          'don\'t forget to keep your volume on.'
        self.send_message(send_string)

    def get_channel_stats_obj(self, message, stat='channel_points'):
        user_id = self.session.query(Users)\
            .where(Users.user==get_user(message))\
                .first().user_id
        channel_id = self.session.query(Channels)\
            .where(Channels.channel==config.channel)\
                .first().channel_id
        stats = self.session.query(UserStats)\
            .where(UserStats.user_id==user_id)\
            .where(UserStats.stat==stat)\
            .where(UserStats.channel_id==channel_id).first()
        if stats:
            return stats
        else:
            stats = UserStats(user_id=user_id, channel_id=channel_id, stat='channel_points', stat_value='0')
            self.session.add(stats)
            self.session.commit()
        return self.session.query(UserStats)\
            .where(UserStats.user_id==user_id)\
            .where(UserStats.stat==stat)\
            .where(UserStats.channel_id==channel_id).first()

    def swearjar(self, message: str):
        user = get_user(message)
        channel = config.channel
        comment_list = self.get_users_comments(user=user, channel=channel, session=self.session)
        times_sworn = count_words(comment_list, swear_words)
        swear_ratio = str(times_sworn/len(comment_list))
        if len(swear_ratio) >= 4:
            swear_ratio = swear_ratio[:4]
        self.send_message(f'You have sworn {times_sworn} times.'
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
        self.send_message(f'@{number1.user} is the chattiest boi, having sent {number1[1]} messages.'
                          f' #2: @{number2.user} with {number2[1]}.'
                          f' #3: @{number3.user} with {number3[1]}')

    def save_chat(self, message: str):
        """

        :param message:
        :return:
        """
        return_comment = self.write_message(message, self.session)
        if self.my_chat and return_comment:
            self.send_message(return_comment)
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
        intervals_for_ad = 10
        while True:
            self._give_chatpoints(session=self.session, channel=self.channel)
            self._update_active_users(session=self.session, channel=self.channel)
            time.sleep(update_interval)
            if time_streamed%(intervals_for_ad*update_interval)==0:
                self.send_info()
            time_streamed += update_interval

    def send_info(self):
        """
        Send stream info periodically
        :return:
        """
        message = '!commands to see all the fun shit you can do. Don\'t forget to follow!'
        try:
            self.sounds.send_sound('follow.mp3')
            self.messaging.send_message(message)
            print('Sent ad')
        except Exception as e:
            traceback.print_exc()
            self.messaging.define_sock()


class RewardHandler(MyDatabase):

    def __init__(self, base_path: str, channel: str, session):
        self.session = session
        self.base_path = base_path
        self.channel = channel

    def main(self, message: str):
        user = get_user(message)
        # if user == 'slowspoon':
        #     return
        comment = get_comment(message)
        # if re.match('!tts', comment, flags=re.IGNORECASE):
        #     return self.play_sound(message)
        if re.match('!wordcount', comment, flags=re.IGNORECASE):
            return self.count_words(message)
        # if re.match('!breakaway', comment, flags=re.IGNORECASE):
        #     return self.breakaway(message)
        return ''

    def count_words(self, message):
        """

        :param message:
        :return:
        """
        points_req = 10
        return_response = 'You don\'t have enough points for that ya silly'
        comment = get_comment(message)
        user = get_user(message)
        split_comment = comment.split(' ')
        if len(split_comment) != 3:
            return 'Naaaa ya goof the format is "!wordcount <valid username> <word>"'
        target_user = split_comment[1]
        target_user_obj = self.get_user_obj(target_user, self.session)
        if not target_user_obj:
            return f'Naa ya goof, {target_user} isn\'t a valid username!'
        if self.has_enough_points(message, points_req):
            comments = self.get_users_comments(user=target_user, channel=self.channel, session=self.session)
            word = split_comment[-1]
            times_said = count_words(comments, [word])
            new_value = self.subtract_points(
                user=user, channel=self.channel, points_to_subtract=points_req, session=self.session
            )
            return_response = f'@{target_user} has said {word} {times_said} times! {new_value} Spoon Bucks remaining!'
        self.session.close()
        return return_response

    def breakaway(self, message):
        points_req = 1000
        user = get_user(message)
        return_response = 'You don\'t have enough points for that ya silly'
        if self.has_enough_points(message, points_req):
            target_user = self.get_user_obj(self.channel, self.session)
            stats_obj = self.get_stats_obj(target_user, self.channel, '!breakaway', self.session)
            if not stats_obj.stat_value:
                stats_obj.stat_value = '1'
                self.session.add(stats_obj)
            else:
                stats_obj.stat_value = str(int(stats_obj.stat_value)+1)
            self.subtract_points(
                user=user, channel=self.channel, points_to_subtract=points_req, session=self.session
            )
            return_response = f'I now owe {stats_obj.stat_value} attacks from the gun, ya dick.'
        self.session.commit()
        return return_response

    def has_enough_points(self, message, points_req) -> bool:
        user = get_user(message)
        user_obj = self.get_user_obj(user=user, session=self.session)
        stats_obj = self.get_stats_obj(
            user=user_obj, channel=self.channel, stat='channel_points', session=self.session
        )
        user_points = int(stats_obj.stat_value)
        print('points: ', user_points)
        if user_points > points_req:
            return True
        return False

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
