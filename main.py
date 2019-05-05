from flask import Flask, render_template, redirect, url_for, request, flash, \
    send_from_directory, send_file, json

from filestore import FileStore, FileStoreBaseException
from history import HistoryManager, maintain_history
from exceptions import FileBinBaseException, UploadMissingFilesException, \
    UploadTooManyFilesException, handle_exception

import utils


UPLOAD_FOLDER = '/tmp/filebin/usercontent'

app = Flask(__name__)

app.secret_key = 'i should probably change this'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_FILES_PER_UPLOAD'] = 10
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
app.config['FILESTORE_EXPIRATION_TIME_SECONDS'] = 10 * 60  # ten minutes

filestore = FileStore(app)
history = HistoryManager(filestore)


@app.template_filter('formatsize')
def size_filter(size):
    return utils.sizeof_fmt(size)


@app.template_filter('formatseconds')
def timestamp_filter(seconds):
    if seconds < 10:
        return '0{}'.format(seconds)

    return seconds


@app.route('/')
@maintain_history
def index():
    return render_template('index.html', max_files=app.config['MAX_FILES_PER_UPLOAD'],
                           max_size=utils.sizeof_fmt(app.config['MAX_CONTENT_LENGTH']))


@app.route('/about')
def about():
    return render_template('about.html')


def _new():
    uploaded_files = request.files.getlist("files")

    if not uploaded_files:
        raise UploadMissingFilesException()

    if len(uploaded_files) > app.config['MAX_FILES_PER_UPLOAD']:
        raise UploadTooManyFilesException()

    return filestore.add(uploaded_files)


@app.route('/api/new', methods=['POST'])
def new_api():
    try:
        code = _new()

        return redirect(url_for('filebin_api', code=code))
    except (FileBinBaseException, FileStoreBaseException) as e:
        return handle_exception(e)


@app.route('/new', methods=['POST'])
def new():
    try:
        code = _new()
        return redirect(url_for('filebin', code=code))
    except (FileBinBaseException, FileStoreBaseException) as e:
        return handle_exception(e)


@app.route('/find')
def find():
    return redirect(url_for('filebin', code=request.args.get('code')))


def _filebin(code):
    return filestore.access(code)


@app.route('/api/bin/<code>')
def filebin_api(code):
    try:
        files, meta = _filebin(code)

        return json.jsonify({
            'error': False,
            'files': list(map(lambda f: {'filename': f.name, 'filesize': f.size}, files)),
            'meta': {
                'expiration_timestamp_utc': meta.expiration_timestamp_utc,
                'definition': meta.definition,
                'code': meta.code,
                'total_size': meta.total_size
            },
        })
    except FileBinBaseException as e:
        return handle_exception(e)


@app.route('/bin/<code>')
@maintain_history
def filebin(code):
    try:
        files, meta = _filebin(code)

        # manage session for browser-based visitors
        history.add(meta.code)

        return render_template('filebin.html',
                               files=files,
                               meta=meta)
    except FileStoreBaseException as e:
        return handle_exception(e)


def _uploaded_file(code, filename):
    return send_from_directory(
        filestore.access_file(code, filename),
        filename,
        as_attachment=True
    )


@app.route('/api/bin/<code>/<filename>')
def uploaded_file_api(code, filename):
    try:
        return _uploaded_file(code, filename)
    except (FileBinBaseException, FileStoreBaseException) as e:
        return handle_exception(e)


@app.route('/bin/<code>/<filename>')
def uploaded_file(code, filename):
    try:
        return _uploaded_file(code, filename)
    except (FileBinBaseException, FileStoreBaseException) as e:
        return handle_exception(e)


@app.route('/archive/<code>')
def uploaded_archive(code):
    try:
        archive = filestore.access_archive(code)

        return send_file(archive,
                         mimetype='application/zip',
                         as_attachment=True,
                         attachment_filename='{}.zip'.format(code))
    except (FileBinBaseException, FileStoreBaseException) as e:
        return handle_exception(e)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(413)
def upload_too_large(e):
    flash('Files too large')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
