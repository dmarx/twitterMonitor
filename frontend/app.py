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

tracking_terms = ['terrorist','terrorists','attack','attacked','attacks',
                #'killed',
                'hostage','hostages','explosion','bomb','bomber','gunman',
                'gunmen','breaking','war',
                #'dead',
                'injured','emergency', 
                'casualties','kidnapped','mob','protest','protesters',
                'shooting','gunfire','arrested','alleged','suspect','suspects',
                'suspected','assassinate','assassinated']
tweet_cache.track_terms(tracking_terms)

def monitor_stream():
    global stream
    while True:
        try:
            stream.statuses.filter(track=tracking_terms)
        except ChunkedEncodingError, e:
            print "[APP ERROR]", e
        except Exception, e:
            print "[APP ERROR]", e # for some reason this breaks the app. 

# Start the data monitor

t = threading.Thread(target=monitor_stream)
t.start()

app = flask.Flask(__name__)
app.secret_key = 'asdf'


def process_item(item, item_type='urls', now, n=1000, totsec = 5*60):
    """Process an entry from a cache Counter object"""
    #print item
    url, score = item
    # Pass in timestamps we want scores for. Might actually make more sense to send
    # these in from the POST request. Anyway, need to pass values into the appropriate KDE
    # to retrieve associated scores.
    delta_sec = np.linspace(0, totsec, n)
    #kde = tweet_cache._kdes['media'][url]
    kde = tweet_cache._kdes[item_type][url]
    scores = [float(s) for s in kde.link_predict(delta_sec)] # Instead of calculating all these scores, I really only need the most recent score, as long as they're calculated at regular intervals.
    t=[now - dt.timedelta(seconds=d) for d in delta_sec]
    t_epoch = [(t0 - dt.datetime(year=1970, month=1, day=1)).total_seconds() for t0 in t]
    datum = {'time':t_epoch, 'delta':[float(d) for d in delta_sec], 'url':url, 'score':scores}
    # We actually want the transpose of this.
    datum2 = {'url':datum['url']}
    values = []
    for i in range(n):
        rec = {'time': datum['time'][i],
               'delta':datum['delta'][i],
               'score':datum['score'][i],
               #'url':  datum['url'],
               'i':i
            }
        values.append(rec)
    datum2['values'] = values
    return datum2

@app.route('/get_data')
def get_data():
    n=1000
    n_trackers = flask.request.args.get('n_trackers', 4, type=int) 
    #try:
    #item = tweet_cache.media_scores.most_common(1)[0]
    #items = tweet_cache.media_scores.most_common(n_trackers)
    items = tweet_cache.url_scores.most_common(n_trackers)
    now = DateDeque.timestamp()
    #data = [process_item(item, now, n) for item in items]
    data = []
    for i, item in enumerate(items):
        datum = process_item(item, 'urls', now, n)
        datum['rank'] = i + 1
        data.append(datum)
    #except Exception, e:
    #    raise e
    #    data = [{'time':[0], 'delta':[0], 'url':'NULL', 'score':[0]}]
    print "len data:", len(data)
    #if len(data) > 0 and type(data) == type([]):
    #    print "keys:", data[0].keys()
    return flask.jsonify(result=data)
    
@app.route('/')
def index():
    return flask.render_template('index.html')

if __name__ == '__main__':
    app.debug = True
    app.run(port=11111)