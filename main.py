from flask import Flask, render_template, redirect, url_for, request, flash, \
    abort, send_from_directory, send_file
from werkzeug.utils import secure_filename
from collections import namedtuple
from io import BytesIO
import os
import shutil
import pathlib
import time
import utils
import zipfile

UPLOAD_FOLDER = '/tmp/filebin/usercontent'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = 'i should probably change this'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_FILES_PER_UPLOAD'] = 10
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

dictionary_db = utils.DictionaryDatabase()

File = namedtuple('File', ['filename', 'size'])
Remaining = namedtuple('Remaining', ['minutes', 'seconds'])
BinMetadata = namedtuple(
    'BinMetadata', ['num_files', 'total_size', 'remaining'])
Definition = namedtuple('Definition', ['word', 'meaning'])


def _generate_code():
    # create set of existing codes
    upload_path = pathlib.Path(app.config['UPLOAD_FOLDER'])

    exclude = set()
    for child in upload_path.iterdir():
        if child.is_dir():
            full_path = child.resolve()
            filename = os.path.basename(full_path)
            exclude.add(filename)

    return dictionary_db.random_word(exclude)


def _extract_definition(word):
    return Definition(word, dictionary_db.define(word))


def _purge_expired_uploads():
    # remove old files
    upload_path = pathlib.Path(app.config['UPLOAD_FOLDER'])

    for child in upload_path.iterdir():
        if child.is_dir():
            stat = child.stat()
            expiration = stat.st_mtime + (60 * 10)
            remaining_seconds = expiration - time.time()

            if remaining_seconds < 0:
                shutil.rmtree(child)


@app.template_filter('formatseconds')
def timestamp_filter(seconds):
    if seconds < 10:
        return '0{}'.format(seconds)

    return seconds


@app.route('/')
def index():
    return render_template('index.html', max_files=app.config['MAX_FILES_PER_UPLOAD'],
                           max_size=utils.sizeof_fmt(app.config['MAX_CONTENT_LENGTH']))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/new', methods=['POST'])
def new():
    _purge_expired_uploads()

    uploaded_files = request.files.getlist("files")

    if not uploaded_files:
        flash('Missing files!')
        return redirect(url_for('index'))

    if len(uploaded_files) > app.config['MAX_FILES_PER_UPLOAD']:
        flash('Too many files!')
        return redirect(url_for('index'))

    code = _generate_code()
    directory = os.path.join(app.config['UPLOAD_FOLDER'], code)
    os.makedirs(directory)

    for file in uploaded_files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(directory, filename))

    return redirect(url_for('filebin', code=code))


@app.route('/find')
def find():
    return redirect(url_for('filebin', code=request.args.get('code')))


@app.route('/bin/<code>')
def filebin(code):
    _purge_expired_uploads()

    code = code.lower()
    path = os.path.join(app.config['UPLOAD_FOLDER'], code)

    if not os.path.exists(path):
        flash('Bin not found!')
        return abort(404)

    p = pathlib.Path(path)

    stat = p.stat()
    expiration = stat.st_mtime + (60 * 10)
    remaining_seconds = expiration - time.time()

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

    remaining = Remaining(int(remaining_seconds / 60),
                          int(remaining_seconds % 60))
    meta = BinMetadata(len(files), utils.sizeof_fmt(total_size), remaining)
    definition = _extract_definition(code)

    return render_template('filebin.html', code=code, files=files, meta=meta, definition=definition)


@app.route('/bin/<code>/<filename>')
def uploaded_file(code, filename):
    _purge_expired_uploads()

    code = code.lower()
    path = os.path.join(app.config['UPLOAD_FOLDER'], code)

    if not os.path.exists(path):
        flash('Bin not found!')
        return abort(404)

    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], code), filename, as_attachment=True)


@app.route('/archive/<code>')
def uploaded_archive(code):
    _purge_expired_uploads()

    code = code.lower()
    path = os.path.join(app.config['UPLOAD_FOLDER'], code)

    if not os.path.exists(path):
        flash('Bin not found!')
        return abort(404)

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

    return send_file(byte_io,
                     mimetype='application/zip',
                     as_attachment=True,
                     attachment_filename='{}.zip'.format(code))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(413)
def upload_too_large(e):
    flash('Files too large!')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
