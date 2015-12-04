# Let's do this: let's let the  monitor live in a separate thread in this script
# so we can directly access the cache object. Upon a request to the '/get_data'
# endpoint, directly query the cache for the most recent values. The request
# will/can include the following parameters:
#   * max number of seconds to go back 
#     --> default to 5 minutes?
#   * number of datapoints to send (which will be combined with the max time 
#       back to determine the actual time points to get data for)
#     --> default to 100?
#   * number of data items to report on
#     --> default to either 1 or 10


import flask
from requests.exceptions import ChunkedEncodingError
import time
from scraper.scraper import MyStreamer, tweet_cache # the cache should really be attached to the class instead of a separate object
from scraper.datedeque import DateDeque
from scraper.connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
import threading
import datetime as dt
import numpy as np

stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

def monitor_stream():
    global stream
    while True:
        try:
            stream.statuses.filter(track=
                ['terrorist','terrorists','attack','attacked','attacks','killed',
                'hostage','hostages','explosion','bomb','bomber','gunman',
                'gunmen','breaking','war','dead','injured','emergency', 
                'casualties','kidnapped','mob','protest','protesters',
                'shooting','gunfire','arrested','alleged','suspect','suspects',
                'suspected','assassinate','assassinated'])
            #stream.statuses.sample()
        except ChunkedEncodingError, e:
            print "[APP ERROR]", e
        except Exception, e:
            print "[APP ERROR]", e

# Start the data monitor

t = threading.Thread(target=monitor_stream)
t.start()

app = flask.Flask(__name__)
app.secret_key = 'asdf'


@app.route('/get_data')
def get_data():
    n=1000
    item = tweet_cache.media_scores.most_common(1)[0]
    print "\n\n~~ITEM"
    print item
    print "\n\n~~ITEM"
    url, score = item
    # Pass in timestamps we want scores for. Might actually make more sense to send
    # these in from the POST request. Anyway, need to pass values into the appropriate KDE
    # to retrieve associated scores.
    now = DateDeque.timestamp()
    # let's go back 5 minutes and return 100 scores
    totsec = 5*60 # 300
    delta_sec = np.linspace(0, totsec, n)
    kde = tweet_cache._kdes['media'][url]
    scores = [float(s) for s in kde.link_predict(delta_sec)]
    t=[now - dt.timedelta(seconds=d) for d in delta_sec]
    t_epoch = [(t0 - dt.datetime(year=1970, month=1, day=1)).total_seconds() for t0 in t]
    data = {'time':t_epoch, 'delta':[float(d) for d in delta_sec], 'url':url, 'score':scores}
    j = flask.jsonify(result=data)
    print j
    return j # return only single latest message
    
@app.route('/')
def index():
    return flask.render_template('index.html')

if __name__ == '__main__':
    app.debug = True
    app.run(port=11111)