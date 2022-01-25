import re
from Models import MyDatabase, ActiveUsers
from Sounds import Sounds
from Messaging import Messaging, Message
import time
from setup import Config
import random
from threading import Thread
config = Config()
base_path = '.'

# messaging = Messaging(config)

def register(cls):
    """
    Registers each roll subclass into Roll where roll_value points to the roll object
    For example, roll_1 is registered as {1: roll_1()}
        Now when users roll a 1 it can be passed into Roll.rolls and the implimentation details will be
        handled by roll_1
    :param cls: Roll subclass (roll_1, roll_69..)
    """
    assert hasattr(cls, 'roll_reward')
    assert hasattr(cls, 'roll_value')
    assert hasattr(cls, 'numerical')
    assert hasattr(cls, 'reward_value')
    Roll.rewards.append(cls.roll_reward)
    if cls.numerical:
        Roll.numerical_rewards.append(cls.roll_reward)
    if isinstance(cls.roll_value, int):
        check_for_proper_roll(cls.roll_value)
        add_to_rolls(cls, cls.roll_value)
        rolls = f'{cls.roll_value}'
    elif isinstance(cls.roll_value, tuple):
        rolls = ''
        for roll_value in cls.roll_value:
            check_for_proper_roll(roll_value)
            add_to_rolls(cls, roll_value)
            rolls += f'{roll_value}/'
        rolls = rolls[:-1]
    else:
        raise AssertionError('roll_value must be either int or tuple of ints')
    Roll.reward_string += f'[{rolls}: {cls.reward_value} {cls.roll_reward}.]'

def add_to_rolls(cls, roll_value):
    """
    Ensures roll_value is an int and registers it with Roll
    Dissallows duplicates
    :param cls: roll subclass
    :param roll_value: Value to register roll class under
    :return:
    """
    assert isinstance(roll_value, int)
    if roll_value not in Roll.rolls:
        Roll.rolls[roll_value] = cls()
    else:
        raise AssertionError(f'Roll values must not overlap: {roll_value} is a duplicate')

def check_for_proper_roll(roll_value):
    """
    Looks at rolls and rare rolls to ensure roll_value is possible
    :param roll_value:
    :return:
    """
    if roll_value not in list(range(*Roll.rare_roll_range)):
        if roll_value not in list(range(*Roll.roll_range)):
            raise AssertionError(f'Out of roll range: {roll_value}')


class Roll(MyDatabase):
    """
    Base class to automatically register any new subclasses
    Contains common methods for all rolls such as adding values to userstats
    """
    rolls = {}
    rewards = []
    numerical_rewards = []
    reward_string = ''
    # user_cd = 360
    user_cd = 360
    cd_type = 'roll_user'
    roll_range = (1, 50)
    rare_roll_range = (0, 100)
    mega_rare_roll_range = (0, 1000)
    rare_wins = (69, )
    mega_rare_wins = ()
    messaging: Messaging

    @classmethod
    def define_messaging(cls, messaging):
        cls.messaging = messaging

    def __init__(self, base_path='.', dbtype='sqlite'):
        """

        :param base_path:
        :param dbtype:
        """
        super().__init__(dbtype=dbtype, dbname=f'{base_path}\\Database\\Chat.db')
        self.sounds = Sounds()

    def __init_subclass__(cls, **kwargs):
        """
        automatically registers any subclass
        :param kwargs:
        :return:
        """
        super().__init_subclass__(**kwargs)
        register(cls)

    def check_roll(self, message: Message):
        """
        check chat for !roll
        :param message:
        :return:
        """
        comment = message.comment
        if re.match('!roll$', comment, flags=re.IGNORECASE):
            Thread(target=self.do_roll, kwargs={'message': message}).start()
            # self.do_roll(message)

    def do_roll(self, message: Message):
        """
        Checks cooldown and does roll if not on cooldown
        :param message:
        :return:
        """
        session = self.get_session(self.db_engine)
        user = message.user
        current_time = time.time()
        cooldown_obj = self.get_cooldown_obj(
            message=message, cd_type=self.cd_type, cd_length=self.user_cd, session=session
        )
        diff = current_time - cooldown_obj.last_used
        if diff > self.user_cd:
            roll = self.rigged_roll()
            self.update_user_cd(cooldown_obj, current_time, session, length=self.user_cd)
            session.close()
            self.sounds.send_sound('dice.mp3', new_process=False)
            roll_response = self.determine_roll_reward(roll, message)
        else:
            roll_response = f'@{user} You got {int(self.user_cd - diff)} seconds before you can do that!'
        self.messaging.send_message(roll_response)

    def rigged_roll(self):
        """
        rolls including "rare" options
        :return: int between 1 and 100 excluding the exceptions
        """
        # return 1
        # possible_rolls = (30, 1, 5, 69, 49, 25, 10, 20)
        # possible_rolls = list(range(20,26))
        # return possible_rolls[random.randint(0,len(possible_rolls)-1)]
        # ^ for testing
        # mega_rare_roll = random.randint(*self.mega_rare_roll_range)
        # if mega_rare_roll in self.mega_rare_wins:
        #     return mega_rare_roll
        # return 4
        rare_roll = random.randint(*self.rare_roll_range)
        if rare_roll in self.rare_wins:
            return rare_roll
        roll_result = random.randint(*self.roll_range)
        return roll_result

    def determine_roll_reward(self, roll: int, message: Message) -> str:
        """
        When user uses !roll, this grabs associated function and calls it
        If no reward for number rolled, returns string to inform user
        :param roll: 1-100 value from !roll
        :param message:
        :return:
        """
        return_func = self.rolls.get(roll)
        if return_func:
            roll_response = return_func(message, roll)
        else:
            user = message.user
            roll_response = f'@{user} You rolled {roll}! YOU WIN NOTHING (!rollrewards for potential rewards)'
            self.sounds.send_sound('sad.mp3')
        return roll_response

    def give_reward(self,
                    message: Message,
                    roll_value: int,
                    roll_reward: str,
                    reward_value: int,
                    return_message=False,
                    sound='') -> str:
        """
        default give reward_value to roll_reward userstat
        :param message:
        :param roll_value: 1-100, value returned by dice roll
        :param roll_reward: string of actual reward, e.g. pushups
        :param reward_value: int to be added
        :param return_message: message to send back to user
        :return:
        """
        session = self.get_session(self.db_engine)
        owed = self.add_channel_owed(message, roll_reward, reward_value, session)
        session.close()
        user = message.user
        if return_message:
            return_message = f'@{user} You\'ve rolled a {roll_value}! ' \
                             f'Spoon owes an additional {reward_value} {roll_reward} ' \
                             f'for a total of {owed}'
        else:
            return str(owed)
        if not sound:
            self.sounds.send_sound('shit.mp3')
        elif sound != 'None':
            self.sounds.send_sound(sound)
        return return_message


class roll_1_2_3(Roll):
    """
    call to add 1 pullup to channel owner user stats
    """
    roll_value = (1, 2, 3)
    roll_reward = 'pullups'
    reward_value = 1
    numerical = True

    def __init__(self):
        super().__init__()

    def __call__(self, message: Message, roll: int)->str:
        """
        add pullups to channel owner
        :param message:
        :param roll:
        :return:
        """
        return self.give_reward(message, roll, self.roll_reward, roll)

class roll_4(Roll):
    """
    Play mike tyson fight like little bitches sound clip
    """
    roll_value = 4
    roll_reward = 'Little Bitches'
    reward_value = 'Fight'
    numerical = False

    def __init__(self):
        super().__init__()

    def __call__(self, message: Message, roll: int)->str:
        """
        send little bitches sound
        :param message:
        :param roll:
        :return:
        """
        self.sounds.send_sound('littlebitches.mp3')
        return_message = f'@{message.user} You rolled a {roll}! Its been awhile since Spoons boxing days...'
        return return_message


class roll_5_6_7(Roll):
    """
    call to add 5 pushups to channel owner user stats
    """
    roll_value = (5, 6, 7,)
    roll_reward = 'pushups'
    reward_value = 5
    numerical = True

    def __init__(self):
        super().__init__()

    def __call__(self, message: Message, roll: int)->str:
        """
        add pushups to channel owner
        :param message:
        :param roll:
        :return:
        """
        return self.give_reward(message, roll, self.roll_reward, roll)



class roll_25_35_50(Roll):
    """
    call to timeout user for 50 seconds
    """
    roll_value = (25, 35, 50)
    roll_reward = 'TIMEOUT'
    reward_value = '25 or 50 second'
    numerical = False

    def __init__(self):
        super().__init__()

    def __call__(self, message: Message, roll: int)->str:
        """
        call to timeout a user
        :param message:
        :param roll:
        :return:
        """
        user = message.user
        self.messaging.send_message(f'/timeout @{user} {roll}')
        return_message = f'@{user} Congrats you rolled {roll}. ' \
                         f'YOU\'VE WON A {roll} SECOND TIMEOUT!'
        return return_message


class roll_10_11_12_13_14(Roll):
    """
    Call to send HYDRATE message and sound
    """
    roll_value = (10, 11, 12, 13, 14)
    roll_reward = 'Hydrate'
    reward_value = 'GULP'
    numerical = False

    def __init__(self):
        super().__init__()

    def __call__(self, message: Message, roll: int)->str:
        """
        HYDRATE
        :param message:
        :param roll:
        :return:
        """
        user = message.user
        self.sounds.send_sound('drink.mp3')
        return_message = f'@{user} You rolled {roll}! HYDRATE'
        return return_message


class roll_20(Roll):
    """
    I will yell 1 word
    """
    roll_value = 20
    roll_reward = 'Yell'
    reward_value = '1 word'
    numerical = False

    def __init__(self):
        super().__init__()

    def __call__(self, message: Message, roll: int) -> str:
        user = message.user
        return_message = f'@{user} You\'ve rolled {roll} and won ONE free yell! ' \
                         f'Say in chat desired word (no tos words).'
        self.sounds.send_sound('loud_noises.mp3')
        return return_message

class roll_21(Roll):
    """
    DO THE MACARENA
    """
    roll_value = 21
    roll_reward = 'macarena'
    reward_value = 'a lil dance'
    numerical = False

    def __init__(self):
        super().__init__()

    def __call__(self, message: Message, roll: int) -> str:
        user = message.user
        return_message = f'@{user} You\'ve rolled {roll}! Ayyyyyy macarena!'
        self.sounds.send_sound('macarena.mp3')
        return return_message

class roll_30_31_32(Roll):
    roll_value = 31
    roll_reward = 'insult mode'
    reward_value = '3 minutes'
    sleep_time = 180
    numerical = False

    def __init__(self):
        super().__init__()
        self.thread: Thread = None

    def __call__(self, message: Message, roll: int) -> str:
        self.change_compliment_state(message, '0')
        return_message = self.change_back(message, roll)
        return return_message

    def change_back(self, message: Message, roll: int) -> str:
        user = message.user
        if not self.thread:
            self.thread = Thread(target=self.sleep_then_change,
                                 kwargs={'message': message, 'state_value': '1'})
            print(self.thread)
            self.thread.start()
            return_message = f'@{user} You\'ve rolled {roll}! ' \
                             f'Bot switched from compliments to insults for 3 minutes'
        elif self.thread.is_alive():
            session = self.get_session(self.db_engine)
            cooldown_obj = self.get_cooldown_obj(message, self.cd_type, session)
            self.update_user_cd(cooldown_obj, 0, session, length=self.user_cd)
            return_message = f'@{user} You\'ve rolled {roll}! ' \
                             f'Insult mode already active, you can roll again!'
            session.close()
        elif not self.thread.is_alive():
            print('isalive')
            self.thread = Thread(target=self.sleep_then_change,
                                 kwargs={'message': message, 'state_value': '1'})
            self.thread.start()
            return_message = f'@{user} You\'ve rolled {roll}! ' \
                             f'Bot switched from compliments to insults for 3 minutes'
        else:
            return_message = f'CONDITION I THOUGHT WAS IMPOSSIBLE MET CHECK YOUR SHIT (@{user} roll failed)'
        return return_message

    def sleep_then_change(self, message: Message, state_value):
        """

        :param message:
        :param state_value:
        :return:
        """
        time.sleep(self.sleep_time)
        self.change_compliment_state(message, state_value)
        self.messaging.send_message('Room back in compliment mode!')

    def change_compliment_state(self, message: Message, state_value: str):
        session = self.get_session(self.db_engine)
        state = 'sending_compliments'
        channel = message.channel
        state_obj = self.get_channel_state(channel, session, state)
        state_obj.state_value = state_value
        self.commit(session)
        session.close()

class roll_49(Roll):
    """
    Call to add 1 sprint to channel owner
    """
    roll_value = (49,)
    roll_reward = 'sprints'
    reward_value = 1
    numerical = True

    def __init__(self):
        super().__init__()

    def __call__(self, message: Message, roll: int)->str:
        """
        call to add 1 sprint to channel
        :param message:
        :param roll:
        :return:
        """
        return self.give_reward(message, roll, self.roll_reward, self.reward_value, sound='pocket_rocket.mp3')

class roll_69(Roll):
    """
    Remove sprints, pullups, pushups
    """
    roll_value = 69
    roll_reward = 'Pushups, Pullups, Sprints'
    reward_value = '-5,-5,-1'
    numerical = False

    def __init__(self):
        super().__init__()

    def __call__(self, message: Message, roll: int) -> str:
        """
        Call to turn to chat emoji mode
        :param message:
        :param roll:
        :return:
        """
        pushups = self.give_reward(message, roll, 'pushups', -5, return_message=False, sound='None')
        pullups = self.give_reward(message, roll, 'pullups', -5, return_message=False, sound='None')
        sprints = self.give_reward(message, roll, 'sprints', -1, return_message=False, sound='ty.mp3')
        return_message = 'CRITICAL ROLL 69!! Spoon now owes less pushups, pullups, and sprints.. THANK YOU! ' \
                         f'Pushups: {pushups}|Pullups: {pullups}|Sprints: {sprints}'
        return return_message


if __name__ == '__main__':
    """
    for debugging
    """
    message = "Channel: slowspoon \nUsername: slowspoon \nMessage: hello"
