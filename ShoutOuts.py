from Sounds import Sounds
from Messaging import Messaging, Message

class ShoutOuts:

    def __init__(self, shoutout_text, sound='defaultshoutout.mp3'):
        self.shoutout_text = shoutout_text
        self.sounds = Sounds()
        twitch_url = 'https://twitch.tv/'
        self.check_out = f'Check them out at {twitch_url}'
        self.sound = sound
        self.seen_today = 0

    def __call__(self, message: Message, messaging: Messaging):
        """
        Certain users frequent my chat, this gives them a shoutout with an audio cue!
        :param message:
        :return:
        """
        user = message.user
        response = ''
        if user.lower() in streamer_shoutouts and streamer_shoutouts[user.lower()].seen_today == 0:
            streamer: ShoutOuts = streamer_shoutouts[user.lower()]
            streamer.seen_today = 1
            response = f'@{user} ' + streamer.shoutout_text + f' {self.check_out}{user}.'
            if streamer.sound:
                self.sounds.send_sound(streamer.sound)
        elif user.lower() in chat_shoutouts and chat_shoutouts[user.lower()].seen_today == 0:
            chatter: ShoutOuts = chat_shoutouts[user]
            chatter.seen_today = 1
            response = chatter.shoutout_text.format(user)
            if chatter.sound:
                self.sounds.send_sound(chatter.sound)
        if response:
            messaging.send_message(response)


streamer_shoutouts = {
    'BrianKellison'.lower():
        ShoutOuts('He might be ugly but at least he\'s boring!'),
    'DJLemma'.lower():
        ShoutOuts('Hes from NYC but we don\'t hold that against him!'),
    'GrubbyAlien'.lower():
        ShoutOuts('Fuckin hate this guy but I guess he\'s entertaining.'),
    'AlanLowe'.lower():
        ShoutOuts('From Canyon Esports Beta Team!'),
    'ewan_mackie':
        ShoutOuts('Giraffe'),
    'Andrade_ZWIFTing'.lower():
        ShoutOuts('Ya boy with fuck cancer and the best pain face in the game!'),
    'wattswheelhouse':
        ShoutOuts('If you want to see a real sprinter here\'s your man!',
                  sound='ekeseplosion.mp3'),
    'ToastedJoost'.lower():
        ShoutOuts('A living sex symbol!'),
    'ouranhshc':
        ShoutOuts('It\'s ya boy!'),
    'K3ndizle'.lower():
        ShoutOuts('Some say he\'s the biggest BBC in all of cycling!'),
    'beatsgameslife':
        ShoutOuts('Dude gets fitter every time he streams!'),
    'DaveGarge'.lower():
        ShoutOuts('Cyclist with a cause, helping underserved communities get on the saddle!',
                  sound='trousers.mp3'),
    'PiMPleff'.lower():
        ShoutOuts('The speed skating cyclist musician y\'all already know who it is.',
                  sound='pimp.mp3'),
    'pedalgames':
        ShoutOuts('I once saw this man casually chat while doing a 33 minute alpe.',
                  sound='droctagonapus.mp3'),
    'LepageMaster'.lower():
        ShoutOuts('Hillbilly extrordinare!',
                  sound='policeprincess.mp3'),
    'hardclaws':
        ShoutOuts('It\'s that thunder from down under.',
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
        ShoutOuts('Definitely not a pussy!',
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
                  sound='heygirl.mp3'),
    # 'slowspoon':
    #     ShoutOuts('oh lol!', sound='smoke.mp3')
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
