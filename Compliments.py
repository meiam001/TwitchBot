import random
from Parsers import get_user, get_channel
from Messaging import Messaging
from setup import Config
import requests
from threading import Thread
from Models import MyDatabase
config = Config()

class Compliments(MyDatabase):
    compliments = (
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
    )
    insult_url = 'https://insult.mattbas.org/api/insult'

    def __init__(self, messaging: Messaging):
        super().__init__(dbname=f'{config.base_path}\\Database\\Chat.db')
        self.messaging = messaging
        self.reset_state()

    def __call__(self, message):
        user = get_user(message)
        channel = get_channel(message)
        if user != channel:
            if self.sending_compliments():
                self.send_compliment(message)
            else:
                Thread(target=self.send_insult, kwargs={'message': message}).start()

    def send_compliment(self, message: str):
        """
        Say a nice thing to chat ~1% of the time
        :param message: IRC formatted message
        """
        if random.randint(0, 100) == 1:
            user = get_user(message)
            complement_index = random.randint(0, len(self.compliments) - 1)
            complement = self.compliments[complement_index].format(user)
            self.messaging.send_message(complement)

    def sending_compliments(self):
        session = self.get_session(self.db_engine)
        state_obj = self.get_channel_state(config.channel, session, 'sending_compliments')
        if state_obj.state_value == '1':
            return True
        return False

    def send_insult(self, message: str):
        """
        Say a mean thing to chat ~20% of the time
        :param message:
        :return:
        """
        if random.randint(0, 100) <= 20:
            user = get_user(message)
            insult = self.get_insult()
            insult = f'@{user} {insult}'
            self.messaging.send_message(insult)

    def get_insult(self) -> str:
        """

        :return:
        """
        return requests.get(self.insult_url).text

    def reset_state(self):
        """
        Sets compliments to '1' on startup
        :return:
        """
        session = self.get_session(self.db_engine)
        print('CHANNEL: ' + config.channel)
        state_obj = self.get_channel_state(
            channel=config.channel,
            session=session,
            state='sending_compliments'
        )
        state_obj.state_value = '1'
        self.commit(session)
        session.close()

if __name__ == '__main__':
    """
    for debugging
    """
    # compliments = Compliments()
    # message = "Channel: slowspoon \nUsername: kekles \nMessage: hello"