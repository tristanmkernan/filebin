from collections import namedtuple
from dictionarydatabase import Dictionary
from io import BytesIO
from werkzeug.utils import secure_filename
import zipfile

import os
import pathlib
import shutil
import time

File = namedtuple('File', ['name', 'size'])
Metadata = namedtuple(
    'Metadata',
    ['code', 'definition', 'expiration_timestamp_utc', 'total_size']
)
FileBin = namedtuple('FileBin', ['files', 'meta'])


class FileStoreBaseException(BaseException):
    pass


class FileStoreNotFoundException(FileStoreBaseException):
    message = 'Bin not found'
    html_code = 404


class FileStoreInvalidCodeException(FileStoreBaseException):
    message = 'Invalid or malformed code'
    html_code = 400


def purge_expired(func):
    """
    decorator to delete expired folders before function is run
    """

    def _purge_expired(self, *args, **kwargs):
        """
        remove all expired folders (and their contents) in the upload folder
        """
        upload_path = pathlib.Path(self.upload_path)

        for child in upload_path.iterdir():
            if child.is_dir():
                stat = child.stat()
                expiration = stat.st_mtime + self.expiration_time_seconds
                remaining_seconds = expiration - time.time()

                if remaining_seconds < 0:
                    shutil.rmtree(child)

        return func(self, *args, **kwargs)

    return _purge_expired


def validate_code(func):
    """
    decorator to validate the code before function is run
    """

    def _validate_code(self, code, *args, **kwargs):
        code = code.lower()

        if all(c.isalpha() for c in code):
            return func(self, code, *args, **kwargs)

        raise FileStoreInvalidCodeException()

    return _validate_code


class FileStore(object):

    def __init__(self, app):
        self.upload_path = app.config['UPLOAD_FOLDER']

        if not os.path.exists(self.upload_path):
            os.makedirs(self.upload_path)

        self.expiration_time_seconds = app.config['FILESTORE_EXPIRATION_TIME_SECONDS']
        self.dictionary = Dictionary()

    def generate_code(self):
        with os.scandir(self.upload_path) as it:
            exclude = set(entry.name for entry in it if entry.is_dir())

            return self.dictionary.random_word(exclude)

        raise FileStoreInvalidCodeException()

    @purge_expired
    def add(self, files):
        """
        saves input files and returns their access code
        """

        code = self.generate_code()
        directory = os.path.join(self.upload_path, code)

        os.makedirs(directory)

        for file in files:
            filename = secure_filename(file.filename)
            file.save(os.path.join(directory, filename))

        return code

    @purge_expired
    @validate_code
    def access(self, code):
        """
        return a bin object if code maps to files on disk
        """

        path = os.path.join(self.upload_path, code)

        if not os.path.exists(path):
            raise FileStoreNotFoundException()

        path = pathlib.Path(path)

        stat = path.stat()
        expiration_timestamp_utc = stat.st_mtime + \
            self.expiration_time_seconds

        files = []
        total_size = 0
        for child in path.iterdir():
            if child.is_file():
                full_path = child.resolve()
                name = os.path.basename(full_path)
                size = child.stat().st_size

                total_size += size

                files.append(File(name, size))

        meta = Metadata(code,
                        self.dictionary.define(code),
                        expiration_timestamp_utc,
                        total_size)

        return FileBin(files, meta)

    @purge_expired
    @validate_code
    def access_file(self, code, filename):
        """
        return the file directory path if available
        """

        path = os.path.join(self.upload_path, code)

        if not os.path.exists(path):
            raise FileStoreNotFoundException()

        return path

    @purge_expired
    @validate_code
    def access_archive(self, code):
        """
        return a byte_io object containing the zip file
        """

        path = os.path.join(self.upload_path, code)

        if not os.path.exists(path):
            raise FileStoreNotFoundException()

        # thanks to https://fadeit.dk/blog/2015/04/30/python3-flask-pil-in-memory-image/
        # for the in-memory strategy

        byte_io = BytesIO()

        with zipfile.ZipFile(byte_io, 'w') as archive:
            for child in pathlib.Path(path).iterdir():
                if child.is_file():
                    full_path = child.resolve()
                    filename = os.path.basename(full_path)
                    archive.write(full_path, filename)

        byte_io.seek(0)

        return byte_io
