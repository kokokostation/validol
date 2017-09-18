import os


class FsCache:
    def __init__(self, directory):
        self.directory = directory

    def read_file(self, file):
        if file in self.get_filenames():
            with open(os.path.join(self.directory, file), 'rb') as file:
                return file.read()
        else:
            return None

    def write_file(self, file, content):
        with open(os.path.join(self.directory, file), 'wb') as file:
            file.write(content)

    def one(self):
        files = self.get_filenames()

        if files:
            return self.read_file(files[0])
        else:
            return None

    def available(self):
        return self.directory != ''

    def delete(self, file):
        if file in self.get_filenames():
            os.remove(os.path.join(self.directory, file))

    def get_filenames(self):
        if self.available():
            return os.listdir(self.directory)
        else:
            return []
