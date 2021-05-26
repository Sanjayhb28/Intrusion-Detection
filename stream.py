
from flask import Flask, render_template, Response, request
import time
import threading
import os
import cv2
import numpy as np
import ctypes
import sys

def stream(framelist,tunnel):

    # App Globals (do not edit)
    app = Flask(__name__)
    # Initialize our ngrok settings into Flask
    app.config.from_mapping(
        BASE_URL="http://localhost:5000",
        USE_NGROK="True",
        ENV="development"
    )

    if app.config.get("ENV") == "development" and app.config["USE_NGROK"]:
        # pyngrok will only be installed, and should only ever be initialized, in a dev environment
        from pyngrok import ngrok,conf
        conf.get_default.region="in"
        # Get the dev server port (defaults to 5000 for Flask, can be overridden with `--port`
        # when starting the server
        port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 5000

        # Open a ngrok tunnel to the dev server
        public_url = ngrok.connect(port).public_url
        print(" * ngrok tunnel \"{}\" -> \"http://127.0.0.1:{}\"".format(public_url, port))

        # # Update any base URLs or webhooks to use the public ngrok URL
        #app.config["BASE_URL"] = public_url

        tunnel=public_url

    width  = cv2.VideoCapture(0).get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
    height = cv2.VideoCapture(0).get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`
    shape=(480,640,3)
    vid=cv2.VideoCapture(0)

    @app.route('/')
    def index():
        return render_template('index.html') #you can customze index.html here

    def gen(camera):
        #get camera frame
        while True:
            try:
                _,frame=vid.read()
            except:
                b=np.frombuffer(framelist,dtype=ctypes.c_uint8)
                frame=b.reshape(shape)
            _,frame=cv2.imencode(".jpg",frame)
            frame=frame.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    @app.route('/video_feed')
    def video_feed():
        return Response(gen(framelist),mimetype='multipart/x-mixed-replace; boundary=frame')

    app.run(debug=False)
s="asas"
stream(1,s)