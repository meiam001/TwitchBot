import subprocess
from multiprocessing import Process
from setup import Config

config = Config()
path_to_vlc = r'C:\Program Files\VideoLAN\VLC\vlc.exe'

class Sounds:
    default_sound = ''
    sounds = {'!ty': 'ty.mp3',
                   '!distracting': 'distracting.mp3',
                   '!laid': 'laid.mp3',
                   '!9001': '9001.mp3',
                   '!vomit': 'vomit.mp3',
                   '!shotsfired': 'shots.mp3',
                   '!stopwhining': 'stop_whining.mp3',
                   '!daddy': 'daddy.mp3',
                   '!abcdefu': 'abcdefu.mp3',
                   '!baka': 'baka.mp3',
                   '!nani?!': 'nani.mp3',
                   '!haha': 'haha.mp3',
                   '!egirl': 'egirl.mp3',
                   '!aaaaaaaaaaaaaaaaaaaaa aaaaaaaaaaaaa': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.mp3'
                   }
    base_path = config.base_path

    def __init__(self):
        """
        Add the file name from the Sounds folder along with desired command here for more sounds
        """

    def __iter__(self):
        return iter(self.sounds.keys())

    def __getitem__(self, item):
        return self.sounds[item]

    def __contains__(self, item):
        if item in self.sounds:
            return True
        return False

    @staticmethod
    def get_speed_multiplier(text: str, max_len=500) -> float:
        """
        Play tts faster for longer messages
        This gets the multiplier
        :param text: Text to be sent to TTS, max len 500 for twitch
        :param max_len:
        :return:
        """
        text_len = len(text)
        match text_len:
            case text_len if text_len < max_len*.2:
                return 1.0
            case text_len if text_len < max_len*.3:
                return 1.2
            case text_len if text_len < max_len*.4:
                return 1.3
            case text_len if text_len < max_len*.6:
                return 1.5
            case text_len if text_len < max_len*.8:
                return 1.7
            case _:
                return 2.5

    def send_sound(self, sound_filename: str, new_process=True, *flags):
        """
        :param sound_filename: sound filename
        :param new_process: determines if a new process is started or if current process
            waits for sound to complete
        :param flags: VLC flags
        :return:
        """
        file_path = f'{self.base_path}\Sounds\{sound_filename}'
        flags = list(flags)
        if new_process:
            sp = Process(target=subprocess.run, args=(
                [path_to_vlc, file_path, '--play-and-exit', '--qt-start-minimized'] + flags,
                )
            )
            sp.start()
            return sp
        subprocess.run([path_to_vlc, file_path, '--play-and-exit', '--qt-start-minimized'] + flags)
