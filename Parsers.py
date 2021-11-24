import re

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