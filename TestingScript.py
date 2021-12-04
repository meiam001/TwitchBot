import pyttsx3
import subprocess
text = """testing a longer thingy and now i'm going even longer just to yes a roo"""
path_to_vlc = r'C:\Program Files\VideoLAN\VLC\vlc.exe'
engine = pyttsx3.init()
engine.setProperty('volume', 1)
fn1 = 'filee.mp3'
engine.save_to_file(text, fn1)
engine.runAndWait()
subprocess.run([path_to_vlc, fn1])

# subprocess.run([path_to_vlc, 'file.mp3', '--play-and-exit', '--qt-start-minimized'])

