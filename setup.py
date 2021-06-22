

class Config:
    def __init__(self):
        self.token = ''
        self.server = ''
        self.port = 0
        self.nick = ''
        self.channel = ''
        self.base_path = ''
        self.dbtype = ''
        with open('.config', 'r') as f:
            config = f.read().split('\n')
            for attribute in config:
                attr_value = attribute.split('=')
                attr = attr_value[0]
                value = attr_value[1]
                setattr(self, attr, value)
        self.port = int(self.port)

if __name__ == '__main__':
    x = Config()