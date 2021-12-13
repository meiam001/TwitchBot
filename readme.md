It's a Twitch Chat bot!

I use it so I can fine-tune my chat bot the way I like without having to rely on preboxed solutions.

There are two main "Reactive" processes, responding based on chat commands. \
TwitchBot in main.py and TTSProcess in TTS.py.

There is one "Passive" process, ActiveUserProcess in main.py.

<h1><u>TwitchBot</u></h1>
Connects to twitch IRC and reacts to certain text based commands. 
Currently has the following features

* Responds to many keywords to inform users types of commands
* Gives automatic "shoutouts" to known streamers
* Randomly sends users a complement from a list
* Plays sounds from sound commands
* Rolls a dice and gives users pre-defined rewards
* Filters bot spam
* Removes rewards based on channel owner commands, for example you
can remove 10 pushups given to users as a roll reward when complete

<h1><u>TTSProcess</u></h1>
Process that handles all user text to speech from
the !tts (comment) command. Text to speech plays on stream

<h1><u>ActiveUserProcess</u></h1>
Tracks users currently watching. Has the following features

* Gives users channel points at every time interval
* Sends a helpful message informing users of commands every x time intervals

Will absolutely not run on your machine, just a for funsies project for my own use.