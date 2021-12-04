import re


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

    @staticmethod
    def f_to_c(f: float) -> float:
        """
        converts Fahrenheit to Celsius
        :param f: Fahrenheit
        :return: Celsius
        """
        return round((f - 32) * (5 / 9), 1)

    @staticmethod
    def c_to_f(c: float) -> float:
        """
        converts celsius to fahrenheit
        :param c: Celsius
        :return: Fahrenheit
        """
        return round((c * 1.8) + 32, 1)

    @staticmethod
    def mi_to_km(mi: float) -> float:
        """
        :param mi:
        :return:
        """
        return round(mi * 1.60934, 1)

    @staticmethod
    def km_to_mi(km: float) -> float:
        """
        :return:
        """
        return round(1.60934 / km, 1)

    @staticmethod
    def kg_to_pounds(kg: float) -> float:
        """
        :param kg:
        :return:
        """
        return round(2.20462262185 * kg, 1)

    @staticmethod
    def pounds_to_kg(pounds: float) -> float:
        """
        :param pounds:
        :return:
        """
        return round(pounds / 2.20462262185, 1)

    @staticmethod
    def get_to_convert(comment: str) -> float:
        to_convert = comment[len('!convert'):].strip().lower()
        to_convert = re.match('-?\d+(\.\d+)?', to_convert)
        if to_convert:
            return float(to_convert[0])

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

def is_valid_comment(message: str) -> bool:
    """

    :param message:
    :return:
    """
    user = get_user(message)
    comment = get_comment(message)
    channel = get_channel(message)
    if user and comment and channel:
        return True
    return False

def count_words(comment_list: list, word_list: list) -> int:
    """

    :param comment_list:
    :param word_list:
    :return:
    """
    words_regex = '|'.join(word_list)
    comment_string = '\n'.join([x.comment for x in comment_list])
    times_sworn = len(re.findall(words_regex, comment_string, flags=re.IGNORECASE))
    return times_sworn