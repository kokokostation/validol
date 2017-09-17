import os


class FsCache:
    def __init__(self, directory, mapping):
        self.directory = directory
        self.mapping = mapping

    def get(self, date, getter):
        date_map = {self.mapping(file): file for file in os.listdir(self.directory)}

        if date in date_map.keys():
            with open(os.path.join(self.directory, date_map[date]), 'rb') as file:
                return file.read()
        else:
            filename, content = getter()

            with open(os.path.join(self.directory, filename), 'wb') as file:
                file.write(content)

            return content
