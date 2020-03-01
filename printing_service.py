# -*- coding: utf-8 -*-
import os
import json
from time import time
import secrets
from ini_reader import INIReader
from thermal_printer import ThermalPrint
from flask import Flask, jsonify, request, flash, redirect
from flask_cors import CORS
from werkzeug.utils import secure_filename
from waitress import serve
from io import BytesIO


# ref: https://testdriven.io/blog/developing-a-single-page-app-with-flask-and-vuejs/
# configuration
DEBUG = True
UPLOAD_FOLDER = './post_receive/'
ALLOWED_EXTENSIONS = {'txt', 'png', 'jpg'}

# instantiate the app
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config.from_object(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})


def get_new_access_token():
    app.token = {'epoch': time(), 'token': secrets.token_hex(32)}
    return app.token


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/printing', methods=['POST'])
def printing():
    settings = INIReader()
    printer = ThermalPrint(printerName=settings.get("General", "printer"),
                           img_maxWidth=int(settings.get("format", "maxwidthpixels")),
                           line_spacing=int(settings.get("format", "line_spacing")),
                           header_margin=int(settings.get("format", "header_margin")),
                           footer_margin=int(settings.get("format", "footer_margin")),
                           cutting=settings.get("format", "cutting"))
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as fin:
                bytes = BytesIO(fin.read())
            printer.load(bytes)
            printer.printing()
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({'msg': 'hello'})


if __name__ == '__main__':
    # cli - " waitress-serve --listen=*:5000 app:app "
    # app.run()  # flask dev server
    settings = INIReader()
    serve(app,
          listen=settings.get("network", "listen"),
          url_scheme='http')  # waitress production serve
