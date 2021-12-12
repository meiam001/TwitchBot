import re
from Parsers import get_channel, get_comment, get_user, parse_message, count_words, is_valid_comment, Conversions
from Models import MyDatabase
from Sounds import Sounds
from Messaging import Messaging
import time
from setup import Config
import random
config = Config()
base_path = '.'

def register(cls):
    assert hasattr(cls, 'roll_reward')
    assert hasattr(cls, 'roll_value')
    assert hasattr(cls, 'reward_value')
    Roll.rolls[cls.roll_value] = cls()
    Roll.rewards.append(cls.roll_reward)
    Roll.reward_string += f'{cls.roll_value}: {cls.reward_value} {cls.roll_reward}. '

class Roll(MyDatabase):
    rolls = {}
    rewards = []
    reward_string = ''
    def __init__(self, base_path='.', dbtype='sqlite'):
        super().__init__(dbtype=dbtype, dbname=f'{base_path}\\Database\\Chat.db')
        self.base_path = base_path
        self.sounds = Sounds(self.base_path)
        self.messaging = Messaging(
            channel=config.channel, server=config.server, nick=config.nick, port=config.port, token=config.token
        )
        self.messaging.define_sock()

    def __init_subclass__(cls, **kwargs):
        """
        automatically registers any subclass
        :param kwargs:
        :return:
        """
        super().__init_subclass__(**kwargs)
        register(cls)

    def check_roll(self, message):
        """

        :param message:
        :return:
        """
        comment = get_comment(message)
        if re.match('!roll$', comment, flags=re.IGNORECASE):
            session = self.get_session(self.db_engine)
            user = get_user(message)
            cd_type = 'roll_user'
            user_cd = 0
            current_time = time.time()
            cooldown_obj = self.get_cooldown_obj(
                message=message, cd_type=cd_type, cd_length=user_cd, session=session
            )
            diff = current_time - cooldown_obj.last_used
            if diff > user_cd:
                self.sounds.send_sound('dice.mp3')
                roll = self.rigged_roll()
                roll_response = self.determine_roll_reward(roll, message)
                self.update_user_cd(cooldown_obj, current_time, session, length=user_cd)
                self.messaging.send_message(roll_response)
            else:
                no = f'@{user} You got {int(user_cd - diff)} seconds before you can do that!'
                self.messaging.send_message(no)
            session.close()

    def rigged_roll(self):
        """

        :return: int between 1 and 100 excluding the exceptions
        """
        # possible_rolls = [1,5,99,100]
        # return possible_rolls[random.randint(0,len(possible_rolls)-1)]
        # ^ for testing
        roll_result = random.randint(1, 100)
        if roll_result in [69]:
            return self.rigged_roll()
        else:
            return roll_result

    def determine_roll_reward(self, roll, message):
        """

        :param roll:
        :param message:
        :return:
        """
        return_func = self.rolls.get(roll)
        if return_func:
            roll_response = return_func(message)
        else:
            roll_response = f'You rolled {roll}! YOU WIN NOTHING (!rollrewards for potential rewards)'
        return roll_response

    def give_reward(self, message: str, roll_value: int, roll_reward: str, reward_value: int, return_message=''):
        session = self.get_session(self.db_engine)
        owed = self.add_channel_owed(message, roll_reward, reward_value, session)
        session.close()
        user = get_user(message)
        if not return_message:
            return_message = f'@{user} You\'ve rolled a {roll_value}! ' \
                             f'Spoon owes an additional {reward_value} {roll_reward} ' \
                             f'for a total of {owed}'
        return return_message

class roll_1(Roll):
    roll_value = 1
    roll_reward = 'pullups'
    reward_value = 1
    def __init__(self):
        super().__init__()
    def __call__(self, message):
        return self.give_reward(message, self.roll_value, self.roll_reward, self.reward_value)

class roll_5(Roll):
    roll_value = 5
    roll_reward = 'pushups'
    reward_value = 5
    def __init__(self):
        super().__init__()
    def __call__(self, message):
        return self.give_reward(message, self.roll_value, self.roll_reward, self.reward_value)


class roll_69(Roll):
    roll_value = 69
    roll_reward = 'emoji only mode'
    reward_value = '3 minutes'


class roll_99(Roll):
    roll_value = 99
    roll_reward = 'sprints'
    reward_value = 1
    def __init__(self):
        super().__init__()
    def __call__(self, message):
        return self.give_reward(message, self.roll_value, self.roll_reward, self.reward_value)


class roll_100(Roll):
    roll_value = 100
    roll_reward = 'TIMEOUT'
    reward_value = '100 seconds'
    def __init__(self):
        super().__init__()
    def __call__(self, message):
        user = get_user(message)
        self.messaging.send_message(f'/timeout @{user} {self.roll_value}')
        return_message = f'@{user} YOU\'VE WON A 100 SECOND TIMEOUT!'
        return return_message


if __name__=='__main__':
    """
    for debugging
    """
    message = "Channel: slowspoon \nUsername: slowspoon \nMessage: hello"