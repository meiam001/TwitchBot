from gtts import gTTS
# from playsound import playsound

mytext = 'testing'

language = 'en'

myobj = gTTS(text=mytext, lang=language, slow=False)

myobj.save("welcome.mp3")

# import os
# import re
# from multiprocessing import Process
# path_to_notepad = r'C:\Program Files\VideoLAN\VLC\vlc.exe'
# # path_to_file = 'Sounds\\watchTV.mp4'
# import subprocess
# subprocess.run([path_to_notepad, "welcome.mp3", '--play-and-exit', '--qt-start-minimized'])

# import requests
# my_headers = {'Authorization': f'Bearer {access_token}'}
# response = requests.get('https://api.twitch.tv/helix/users?login=slowspoon', headers=my_headers)

# import win32com.client as wincl
# speak = wincl.Dispatch("SAPI.SpVoice")
# speak.Speak("Hello World")
# from win32com import client
# from win32com.client import constants
# speaker = client.Dispatch("SAPI.SpVoice", constants.SVSFlagsAsync)
# speaker.Speak('teehee')