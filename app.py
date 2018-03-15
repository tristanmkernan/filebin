from flask import Flask, render_template, redirect, url_for, request, flash, abort, send_from_directory
from werkzeug.utils import secure_filename
from collections import namedtuple
import os
import shutil
import pathlib
import time

import utils

UPLOAD_FOLDER = '/tmp/filebin/'

app = Flask(__name__)
app.secret_key = 'i should probably change this'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_FILES_PER_UPLOAD'] = 5
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


dictionary_db = utils.DictionaryDatabase()


File = namedtuple('File', ['filename', 'size'])
Remaining = namedtuple('Remaining', ['minutes', 'seconds'])
BinMetadata = namedtuple('BinMetadata', ['num_files', 'total_size', 'remaining'])
Definition = namedtuple('Definition', ['word', 'meaning'])


def _generate_code():
    while True:
        word1 = dictionary_db.random_word()
        word2 = dictionary_db.random_word()

        code = '{}_{}'.format(word1, word2)
        path = os.path.join(app.config['UPLOAD_FOLDER'], code)

        if word1 != word2 and not os.path.exists(path):
            os.makedirs(path)

            return code


def _extract_definitions(code):
    word1, word2 = code.split('_')
    return Definition(word1, dictionary_db.define(word1)), Definition(word2, dictionary_db.define(word2))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/new', methods=['POST'])
def new():
    uploaded_files = request.files.getlist("files")

    if not uploaded_files:
        flash('Missing files!')
        return redirect(url_for('index'))

    if len(uploaded_files) > app.config['MAX_FILES_PER_UPLOAD']:
        flash('Too many files!')
        return redirect(url_for('index'))

    code = _generate_code()

    for file in uploaded_files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], code, filename))

    return redirect(url_for('filebin', code=code))


@app.route('/find')
def find():
    return redirect(url_for('filebin', code=request.args.get('code')))


@app.route('/bin/<code>')
def filebin(code):
    code = code.lower()
    path = os.path.join(app.config['UPLOAD_FOLDER'], code)

    if not os.path.exists(path):
        flash('Bin not found!')
        return abort(404)

    p = pathlib.Path(path)

    stat = p.stat()
    expiration = stat.st_mtime + (60 * 10)
    remaining_seconds = expiration - time.time()

    if remaining_seconds < 0:
        shutil.rmtree(path)
        flash('Bin not found!')
        return abort(404)

    files = []
    total_size = 0
    for child in p.iterdir():
        if child.is_file():
            full_path = child.resolve()
            filename = os.path.basename(full_path)
            raw_size = child.stat().st_size
            size = utils.sizeof_fmt(raw_size)

            total_size += raw_size

            files.append(File(filename, size))

    remaining = Remaining(int(remaining_seconds / 60), int(remaining_seconds % 60))
    meta = BinMetadata(len(files), utils.sizeof_fmt(total_size), remaining)
    definitions = _extract_definitions(code)

    return render_template('filebin.html', code=code, files=files, meta=meta, definitions=definitions)


@app.route('/bin/<code>/<filename>')
def uploaded_file(code, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], code), filename)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(413)
def upload_too_large(e):
    flash('Files too large!')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
