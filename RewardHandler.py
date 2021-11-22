from Models import Channels, MyDatabase, ActiveUsers
from Parsers import get_channel, get_comment, get_user, parse_message, count_words, is_valid_comment
import re
class RewardHandler(MyDatabase):

    def __init__(self, base_path: str, channel: str, session):
        self.session = session
        self.base_path = base_path
        self.channel = channel

    def main(self, message: str):
        user = get_user(message)
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