import pyttsx3
from gtts import gTTS
import subprocess
import time
text = """testing a longer thingy """
engine = pyttsx3.init()
st1 = time.time()
fn1 = 'filee.mp3'
engine.save_to_file(text, fn1)
et1 = time.time()
start_time2 = time.time()
tts = gTTS(text=text, lang='en')
tts.save('file.mp3')
end_time2 = time.time()

print(f'microsoft time: {et1-st1}|google time:{end_time2-start_time2}')
engine.runAndWait()
engine.getProperty('rate')
path_to_vlc = r'C:\Program Files\VideoLAN\VLC\vlc.exe'
# subprocess.run([path_to_vlc, fn1,  '--qt-start-minimized'])
# subprocess.run([path_to_vlc, 'file.mp3', '--play-and-exit', '--qt-start-minimized'])

