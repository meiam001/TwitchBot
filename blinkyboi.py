# FILE DOES NOT WORK KEEPING IN CASE OF FUTURE USE

from blinkytape import BlinkyTape, serial
import time

class BlinkyBoi:
    def _define_light_commands(self):
        return ', '.join(self.bb.commands.keys())
    def __init__(self, port):
        self.bt = BlinkyTape(port)
        self.commands = {'!police': self.police,
                         '!blue': self.blue,
                         '!red': self.red,
                         '!purple': self.purple,
                         '!green': self.green}
        try:
            self.bb = BlinkyBoi('COM6')
            self.bb.default()
            self.comment_keywords['!lights'] = self._define_light_commands()
            self.lights = True
        except serial.serialutil.SerialException:
            print("No blinkylight detected")
            self.lights = False

    def check_lights(self, message: str):
        """
        :param message:
        :return:
        """
        comment = get_comment(message).lower()
        if self.lights and comment in self.bb.commands:
            try:
                p = Process(target=self.bb.commands[comment]())
                p.start()
            except:
                print("Lights DISCONNECTED")
                self.lights = False

    def police(self):
        """
        flash blue and red for a few seconds
        :return:
        """
        time_on = 10
        interval = .4
        for i in range(int(time_on / interval / 2)):
            self.bt.alternate_colors((255, 0, 0), (0, 0, 255))
            time.sleep(interval)
            self.bt.alternate_colors((0, 0, 255), (255, 0, 0))
            time.sleep(interval)
        self.default()

    def blue(self):
        self.default()

    def red(self):
        self.bt.displayColor(255, 0, 0)

    def purple(self):
        self.bt.displayColor(255, 0, 255)

    def green(self):
        self.bt.displayColor(0, 255, 0)

    def default(self):
        self.bt.displayColor(0, 0, 255)
