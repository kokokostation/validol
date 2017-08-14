class AtomBase:
    def __init__(self, name, params):
        self.name = name
        self.params = params

    @property
    def full_name(self):
        return "{name}({params})".format(name=self.name, params=', '.join(self.params))

    def __str__(self):
        return "{name}({params})".format(name=self.name, params=', '.join(self.params))