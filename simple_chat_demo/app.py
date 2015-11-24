#!/usr/bin/env python
import datetime
import flask
import redis

app = flask.Flask(__name__)
app.secret_key = 'asdf'
red = redis.StrictRedis()

def event_stream():
    pubsub = red.pubsub()
    #pubsub.subscribe('chat')
    pubsub.subscribe('tweet_monitor')
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        print message
        yield 'data: %s\n\n' % message['data']

@app.route('/post', methods=['POST'])
def post():
    message = flask.request.form['message']
    now = datetime.datetime.now().replace(microsecond=0).time()
    msg = 'chat', u'[%s] : %s' % (now.isoformat(), message)
    print msg
    red.publish(msg)
    return flask.Response(status=204)

@app.route('/stream')
def stream():
    return flask.Response(event_stream(),
                          mimetype="text/event-stream")

@app.route('/')
def home():
    return """
        <!doctype html>
        <title>Twitter Monitor</title>
        <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
        <pre id="out"></pre>
        <script>
            function sse() {
                var source = new EventSource('/stream');
                var out = document.getElementById('out');
                source.onmessage = function(e) {
                    // XSS in chat is fun
                    out.innerHTML =  e.data + '\\n' + out.innerHTML;
                };
            }
            sse();
        </script>
    """

if __name__ == '__main__':
    app.debug = True
    app.run(port=12345)