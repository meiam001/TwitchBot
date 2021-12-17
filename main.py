import log
import re
from Models import MyDatabase, ActiveUsers
from Sounds import Sounds
import requests
from setup import Config
import traceback
import time
from multiprocessing import Process
from swearwords import swear_words
import random
from Parsers import get_channel, get_comment, get_user, count_words, Conversions
from datetime import datetime
from ShoutOuts import ShoutOuts
from Messaging import Messaging
from RollDice import Roll
from Compliments import Compliments
from TTS import Cooldown, TTSProcess
timestamp_regex = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}'
path_to_vlc = r'C:\Program Files\VideoLAN\VLC\vlc.exe'

swear_words_regex = '|'.join(swear_words)
logger = log.logging.getLogger(__name__)


class TwitchBot(MyDatabase):
    def __init__(self, dbtype='sqlite'):
        """
        Main process that reacts to user input
        Currently responsible for every reactive command except TTS
        Also saves every message sent to a database
        :param dbtype: The database type. Currently only supports sqlite
        """
        self.messaging = Messaging(config=config)
        self.messaging.define_sock()
        self.rolls = Roll()
        self.removal_options = Roll.rewards
        self.give_shoutout = ShoutOuts(self.messaging)
        self.sounds = Sounds(base_path)
        self.cooldowns = Cooldown()
        sound_commands = ', '.join(self.sounds)
        self.comment_keywords = {
             '!swearjar': self.swearjar,
             '!time': self.send_time,
             '!rollrewards': Roll.reward_string,
             '!convert': '!convert <number><lb/kg/f/c/km/mi>',
             '!sounds': sound_commands,
             '!lurk': self.lurk,
             '!chattyboi': self.chatty_boi,
        }
        super().__init__(dbtype=dbtype, dbname=f'{base_path}\\Database\\Chat.db')
        self.comment_keywords['!commands'] = self._define_commands(self.comment_keywords)
        self.compliments = Compliments(self.messaging)
        self.sock = self.messaging.sock
        self.channel_obj = None
        if config.channel == 'slowspoon':
            self.my_chat = 1
        else:
            self.my_chat = 0
        session = self.get_session(self.db_engine)
        self.check_for_channel(session)
        for user in session.query(ActiveUsers):
            session.delete(user)
            self.commit(session)
        session.close()

    def main(self):
        """
        Begin reading chat. Continues till process is killed
        :return:
        """
        self.read_chat()

    @staticmethod
    def _define_commands(comment_keywords: dict) -> str:
        """
        Truncates command keys into a list to return to users
        :param comment_keywords:
        :return:
        """
        return ', '.join(list(comment_keywords.keys()) + ['!tts <message>', '!roll', '!owed'])

    def read_chat(self):
        """
        Waits for messages to come into chat
        Entry point for every text based command except TTS
        :return:
        """
        while True:
            message = self.messaging.read_chat()
            if message:
                self.save_chat(message)
                if self.my_chat and not self.timeout_spam(message) \
                        and not re.match('!tts', message, flags=re.IGNORECASE):
                    print('SCRIPT: ' + __name__)
                    self.respond_to_message(message)
                    self.give_shoutout(message, self.messaging)
                    self.compliments(message)
                    self.check_sound(message)
                    self.conversions(message)
                    self.rolls.check_roll(message)
                    self.check_remove_channel_owed(message)
                    self.check_owed(message)

    def check_owed(self, message):
        """
        Check what streamer owes chat
        :param message:
        :return:
        """
        stat_objects = []
        comment = get_comment(message)
        if re.match('!owed$', comment, flags=re.IGNORECASE):
            owed_string = ''
            session = self.get_session(self.db_engine)
            channel = get_channel(message)
            user_obj = self.get_user_obj(channel, session)
            for stat in self.rolls.numerical_rewards:
                stat_obj = self.get_stats_obj(user_obj, channel, stat, session)
                stat_objects.append(stat_obj)
            for stat_obj in stat_objects:
                owed_string += f'{stat_obj.stat_value} {stat_obj.stat}. '
            self.messaging.send_message(owed_string)


    def check_remove_channel_owed(self, message):
        """
        Users can roll the dice for certain rewards
        If reward is fulfilled, use this command to remove
        FORMAT: !remove <reward> <value>
            ex: !remove pushups 10
        Can only be used by channel owner
        Times out trolls trying to use it
        :param message:
        :return:
        """
        comment = get_comment(message)
        if re.match('!remove', comment, flags=re.IGNORECASE):
            user = get_user(message).lower()
            channel = get_channel(message).lower()
            if user == channel:
                comment_args = comment.split(' ')
                if len(comment_args) == 3:
                    to_remove = comment_args[1]
                    remove_value = comment_args[2]
                    try:
                        remove_value = -int(remove_value)
                        if to_remove in self.removal_options:
                            session = self.get_session(self.db_engine)
                            value_remaining = self.add_channel_owed(message, to_remove, remove_value, session)
                            response_message = f'{-remove_value} {to_remove} removed! {value_remaining} remaining!'
                            self.messaging.send_message(response_message)
                            session.close()
                        else:
                            self.messaging.send_message('Format it properly ya dummy')
                    except:
                        self.messaging.send_message('Format it properly ya dummy')
                else:
                    self.messaging.send_message('Format it properly ya dummy')
            else:
                self.messaging.send_message(f'@{user} BEGONE THOT')
                self.messaging.send_message(f'/timeout @{user} 30')


    def timeout_spam(self, message: str) -> bool:
        """
        bigfollows is commonly bot spammed,
        automatically timeout any user who uses it in their comment
        :param message:
        :return:
        """
        comment = get_comment(message)
        timeout_len = 60
        if self.check_spam(comment):
            user = get_user(message)
            print('bigfollow thingy')
            self.messaging.send_message(f'/timeout {user} {timeout_len}')
            return True
        return False

    @staticmethod
    def check_spam(comment: str)->bool:
        """
        Checks for common bot spam comments
        :param comment: users comment in chat
        :return: True if spam False otherwise
        """
        if re.search('bigfollow|\.ru|\.cc', comment, flags=re.IGNORECASE):
            return True
        if re.search('buy', comment, flags=re.IGNORECASE) \
                and re.search('follower', comment, flags=re.IGNORECASE):
            return True
        if re.search('become', comment, flags=re.IGNORECASE) \
                and re.search('famous', comment, flags=re.IGNORECASE):
            return True
        return False

    def conversions(self, message: str) -> None:
        """
        processes messages and converts units for chat (f/c/kg/pounds)
        :param message:
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

    @staticmethod
    def proper_conversion_comment(comment: str) -> bool:
        """
        Ensures !convert comment is formatted properly
        :param comment: Comment user sent to chat
        :return:
        """
        return bool(re.match(
            '!convert\s-?\d+(\.\d+)?\s?(f|c|kg|lb)\Z',
            comment,
            flags=re.IGNORECASE
        ))

    @staticmethod
    def get_conversion_return_message(conversion: Conversions) -> str:
        """
        Gets message to send to users using convert command
        :param conversion: Conversion class containing conversion details
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
        self.messaging.send_message(
            f'Thanks for stopping by @{user}! '
            f'Remember, my followers are objectively better than other people.'
        )

    def respond_to_message(self, message: str):
        """
        Responds to keywords defined in self.comment_keywords
        And to SPRINT
        :param message:
        :return:
        """
        comment = get_comment(message)
        user = get_user(message)
        channel = get_channel(message)
        if comment and comment in self.comment_keywords:
            if isinstance(self.comment_keywords[comment], str):
                self.messaging.send_message(self.comment_keywords[comment])
            else:
                self.comment_keywords[comment](message)
        elif re.search('sprint', comment, flags=re.IGNORECASE) \
                and random.randint(0, 100) < 20\
                and channel != user:
            self.messaging.send_message(f'@{user} shutup nerd')
            self.sounds.send_sound('shutup.mp3')

    def check_sound(self, message: str):
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

    def swearjar(self, message: str):
        """
        Lets a user know how many times they've sworn and the ratio of swearwords/total messages
        :param message:
        :return:
        """
        session = self.get_session(self.db_engine)
        user = get_user(message)
        channel = config.channel
        comment_list = self.get_users_comments(user=user, channel=channel, session=session)
        times_sworn = count_words(comment_list, swear_words)
        swear_ratio = str(times_sworn / len(comment_list))
        if len(swear_ratio) >= 4:
            swear_ratio = swear_ratio[:4]
        self.messaging.send_message(f'You have sworn {times_sworn} times.'
                                    f' Your ratio of swear words to total comments is {swear_ratio}')
        session.close()

    def chatty_boi(self, message: str):
        """
        Lets users know who's sent the most messages
        Currently tells of top 3
        :param message:
        :return:
        """
        channel = get_channel(message)
        session = self.get_session(self.db_engine)
        top_commenters = self.get_top_commenters(session=session, limit=3, channel=channel)
        number1 = top_commenters[0]
        number2 = top_commenters[1]
        number3 = top_commenters[2]
        self.messaging.send_message(f'@{number1.user} is the chattiest boi, having sent {number1[1]} messages.'
                                    f' #2: @{number2.user} with {number2[1]}.'
                                    f' #3: @{number3.user} with {number3[1]}')
        session.close()

    def save_chat(self, message: str):
        """
        Save user chat messages to database defined in __init__
        :param message:
        """
        session = None
        try:
            session = self.get_session(self.db_engine)
            return_comment = self.write_message(message, session)
        except:
            if session:
                session.close()
            return_comment = ''
        if self.my_chat and return_comment:
            self.messaging.send_message(return_comment)
            self.sounds.send_sound('cheering.mp3')

class ActiveUserProcess(MyDatabase):

    def __init__(self, config: Config):
        """
        Tracks current users and gives them spoonbucks at given time intervals
        Also sends an "ad" asking users to follow every x time intervals
        :param config: Config class with basic config attributes
        """
        super().__init__(dbtype=config.dbtype, dbname=f'{config.base_path}\\Database\\Chat.db')
        self.token = config.token
        self.server = config.server
        self.port = config.port
        self.base_path = config.base_path
        self.nick = config.nick
        self.channel = config.channel
        self.sounds = Sounds(self.base_path)
        self.messaging = Messaging(config=config)
        self.tb = None
        self.main()

    def main(self):
        """
        Main passive process to give users points every update_interval seconds
        Also sends "follow me" ad every intervals_for_ad intervals
        :return:
        """
        update_interval = 60
        time_streamed = 0
        intervals_for_ad = 11
        while True:
            session = self.get_session(self.db_engine)
            self._give_chatpoints(session=session, channel=self.channel)
            viewers = self._get_current_viewers(self.channel)
            self._update_active_users(session=session, channel=self.channel, viewers=viewers)
            time.sleep(update_interval)
            if time_streamed % (intervals_for_ad * update_interval) == 0:
                self.send_info()
            session.close()
            time_streamed += update_interval

    @staticmethod
    def _get_current_viewers(channel: str) -> [str]:
        """
        Gets list of people currently watching stream for point allocation
        :return: List of current viewers
        """
        channel_viewers = f'https://tmi.twitch.tv/group/user/{channel}/chatters'
        r = requests.get(channel_viewers)
        if r.status_code == 200:
            viewer_json = r.json()
            vips = viewer_json['chatters']['vips']
            mods = viewer_json['chatters']['moderators']
            viewers = viewer_json['chatters']['viewers']
            all_viewers = vips+mods+viewers
            return all_viewers
        return []

    def send_info(self):
        """
        Send stream info periodically
        :return:
        """
        message = '!commands (!convert, !tts, !sounds, !roll, ect) to see all the fun shit you can do. Don\'t forget to follow!'
        try:
            with self.messaging as _:
                time.sleep(.1)
                self.sounds.send_sound('follow.mp3')
                self.messaging.send_message(message)
        except Exception as e:
            logger.error(f'{e}')
            traceback.print_exc()


if __name__ == '__main__':
    pass
    config = Config()
    base_path = config.base_path
    tb = TwitchBot(
        dbtype=config.dbtype
    )
    tts = TTSProcess()
    p = Process(target=ActiveUserProcess, kwargs={
        "config": config}
                )
    p.start()
    tb.main()

