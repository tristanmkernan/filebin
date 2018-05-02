from flask import redirect, url_for, flash, json


def handle_exception(e, as_api=False):
    if as_api:
        return json.jsonify({
            'error': True,
            'message': e.message
        }), e.html_code

    flash(e.message)
    return redirect(url_for('index'))


class FileBinBaseException(BaseException):
    pass


class UploadMissingFilesException(FileBinBaseException):
    message = 'No files uploaded'
    html_code = 400


class UploadTooManyFilesException(FileBinBaseException):
    message = 'Too many files in upload'
    html_code = 400
