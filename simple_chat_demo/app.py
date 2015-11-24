#!/usr/bin/env python
import datetime
import flask
import redis

app = flask.Flask(__name__)
app.secret_key = 'asdf'
red = redis.StrictRedis()

def event_stream():
    pubsub = red.pubsub()
    pubsub.subscribe('tweet_monitor')
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        #print message
        if type(message) == type({}):
            print "publishing"
            yield 'data: %s\n\n' % message['data']
        else:
            print type(message)

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
            var data;
            var obj;
            var focus;
            function sse() {
                var source = new EventSource('/stream');
                var out = document.getElementById('out');
                source.onmessage = function(e) {
                    console.log("received");
                    // XSS in chat is fun
                    data = e.data;
                    //out.innerHTML = data + '\\n' + out.innerHTML;
                    obj = JSON.parse(data);
                    focus = obj['urls']['top_by_count'];
                    //console.log(focus[0]['url']);
                    console.log("doing the thing");
                    
                    out.innerHTML = ''; // truncate existing text
                    for(i=0;i<focus.length;i++){
                        var insert_text = focus[i]['rank'] +"\t|\t"+ 
                                         focus[i]['score'] +"\t|\t"+ 
                                         '<a href="' + focus[i]['url'] + '">' + focus[i]['url'] +"</a>"+ '\\n';
                        console.log(insert_text);
                        out.innerHTML =  out.innerHTML + insert_text;
                    };
                };
            }
            sse();
        </script>
    """

if __name__ == '__main__':
    app.debug = True
    app.run(port=12345)