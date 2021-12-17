import random
from Parsers import get_user, get_channel
from Messaging import Messaging
from setup import Config
import requests
from threading import Thread
from Models import MyDatabase
config = Config()


class Compliments(MyDatabase):
    """
    Class that handles randomly responding to users with a compliment or insult

    """
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
    insult_url = 'https://evilinsult.com/generate_insult.php?lang=en'
    compliment_url = 'https://complimentr.com/api'

    def __init__(self, messaging: Messaging):
        super().__init__(dbname=f'{config.base_path}\\Database\\Chat.db')
        self.messaging = messaging
        self.reset_state()

    def __call__(self, message):
        """
        Call to randomly send compliment
        :param message:
        :return:
        """
        user = get_user(message)
        channel = get_channel(message)
        if user != channel:
            if self.sending_compliments():
                Thread(target=self.send_compliment, kwargs={'message': message}).start()
            else:
                Thread(target=self.send_insult, kwargs={'message': message}).start()

    def send_compliment(self, message: str):
        """
        Say a nice thing to chat ~1% of the time
        :param message: IRC formatted message
        """
        if random.randint(0, 100) == 1:
            user = get_user(message)
            compliment = self.get_compliment(user)
            self.messaging.send_message(compliment)

    def sending_compliments(self) -> bool:
        """
        Check compliment state to see if sending compliments or insults
        :return:
        """
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
        Get an insult from the insult api at insult_url
        Very uncreative insult if query fails
        :return: An insult in string format
        """
        insult_response = requests.get(self.insult_url)
        if insult_response.status_code == 200:
            return insult_response.text
        else:
            return 'Fuck you'

    def get_compliment(self, user):
        """
        Get a compliment from a compliment api at compliment_url
        If request fails get from preset list
        :param user: user string
        :return:
        """
        compliment_response = requests.get(self.compliment_url)
        if compliment_response.status_code==200:
            compliment = user + ' ' + compliment_response.json()['compliment']
        else:
            compliment_index = random.randint(0, len(self.compliments) - 1)
            compliment = self.compliments[compliment_index].format(user)
        return compliment

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