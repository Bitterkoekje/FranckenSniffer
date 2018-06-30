import os


class Whitelist:

    def __init__(self, dr: str = 'whitelist_db', filters=None, update: bool= True):
        if filters is None:
            filters = dict()

        self.__dr = os.path.join(os.path.dirname(__file__), dr)

        print(self.__dr)
        self.filters = filters

        self.names = dict()
        self.macs = dict()

        if update:
            self.update()

    def update(self):
        self.update_names()
        self.update_macs()

    def update_macs(self):
        if not self.names:
            self.update_names()

        filename = os.path.join(self.__dr, 'macs')
        with open(filename) as text:
            macs = eval(text.read())

        for mac in macs:
            if macs[mac] in self.names.keys():
                self.macs[mac] = macs[mac]

    def update_names(self):
        filename = os.path.join(self.__dr, 'names')
        with open(filename) as text:
            if self.filters:
                names = eval(text.read())
                for name in names:
                    for f in self.filters:
                        if names[name].get(f) == self.filters[f]:
                            self.names[name] = names[name]
            else:
                self.names = eval(text.read())

    def get_macs_by_id(self, id_):
        macs_by_id = []
        for mac in self.macs:
            if self.macs[mac] == int(id_):
                macs_by_id.append(mac)
        return macs_by_id
