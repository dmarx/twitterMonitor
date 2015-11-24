# Modified from https://github.com/jkbrzt/chat/blob/master/app.py
# http://blog.miguelgrinberg.com/post/video-streaming-with-flask
# http://stackoverflow.com/questions/12232304/how-to-implement-server-push-in-flask-framework

import datetime
import flask
import redis
from flask import Response, render_template, jsonify
try:
    import ujson as json
except:
    import json
app = flask.Flask(__name__)
#app.secret_key = 'asdf'
r = redis.StrictRedis()

def event_stream():
    #with app.app_context():
    #with app.test_request_context():
        pubsub = r.pubsub()
        pubsub.subscribe('tweet_monitor')
        # TODO: handle client disconnection.
        for message in pubsub.listen():
            #print message
            if message['data'] != 1:
                print "PUBLISHING"
                d = json.loads(message['data'])
                d = d['urls']['top_by_count']
                for item in d:
                    print item
                #yield jsonify(data=d) # This should already be a JSON object
                yield "data: " + message['data']
            else:
                print "waiting for data"
                continue
        print "oh shit, exiting event loop..."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.debug = True
    app.run()