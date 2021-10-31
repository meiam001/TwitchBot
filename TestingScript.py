# from gtts import gTTS
# from playsound import playsound


# mytext = 'Welcome to geeksforgeeks!'
#
# language = 'en'
#
# myobj = gTTS(text=mytext, lang=language, slow=False)
#
# myobj.save("welcome.mp3")
#
# # Playing the converted file
import os
import re
from multiprocessing import Process
path_to_notepad = r'C:\Program Files\VideoLAN\VLC\vlc.exe'
path_to_file = 'Sounds\\watchTV.mp4'
import subprocess
subprocess.run([path_to_notepad, path_to_file, '--play-and-exit', '--qt-start-minimized'])