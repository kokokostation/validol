import pickle


class Item:
    def __init__(self, name):
        self.name = name


class Structure:
    def __init__(self, file_name):
        self.file_name = file_name

    def write(self, item):
        with open(self.file_name, "ab") as file:
            pickle.dump(item, file)

    def read(self):
        with open(self.file_name, "rb") as file:
            result = []
            try:
                while True:
                    result.append(pickle.load(file))
            except EOFError:
                return result

    def remove_by_pred(self, pred):
        items = self.read()

        with open(self.file_name, "wb") as file:
            for item in items:
                if not pred(item):
                    pickle.dump(item, file)

    def remove_by_name(self, name):
        self.remove_by_pred(lambda item: item.name == name)