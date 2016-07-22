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
from flask import g
from requests.exceptions import ChunkedEncodingError
import time
#from scraper.scraper import MyStreamer, tweet_cache # the cache should really be attached to the class instead of a separate object
#from scraper.datedeque import DateDeque
#from scraper.connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
import threading
import datetime as dt
import numpy as np
#from scraper import MyStreamer
import sqlite3
import ConfigParser
from urlparse import urlparse

config = ConfigParser.ConfigParser()
config.read('connection.cfg')
DB_NAME = config.get('database','name')

# For article titles. This probably belongs somewhere else
import requests
from bs4 import BeautifulSoup
from load_terms import load_terms

title_cache = {} # I should save these to the database
def get_title(url, cache=title_cache):
    if url in cache:
        return cache[url]
    response = requests.get(url)
    soup = BeautifulSoup(response.text)
    try:
        title = soup.title.text.strip()
    except:
        title = url
    cache[url] = title
    print ("[TITLE]", title)
    print ('[TITLE CACHE LENGTH]', len(cache))
    return title

terms = load_terms()

#def monitor_stream():
#    stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
#    while True:
#        try:
#            stream.statuses.filter(track=terms)
#        except ChunkedEncodingError, e:
#            print "[APP ERROR]", e
#        except Exception, e:
#            print "[APP ERROR]", e # for some reason this breaks the app. 

# Start the data monitor

#t = threading.Thread(target=monitor_stream)
#t.start()

app = flask.Flask(__name__)
app.secret_key = 'asdf'

@app.before_request
def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.Connection(DB_NAME)
    #return g.sqlite_db
   
@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def get_top(min_score, n, kind='urls'):
    top = g.sqlite_db.execute('select url, current_score from entities where type=? and current_score > ? order by current_score desc limit ?', [kind, min_score, n]).fetchall()
    return [{'url':rec[0], 'domain':urlparse(rec[0]).netloc, 'score':rec[1], 'title':get_title(rec[0])} for rec in top]

@app.route('/get_data', methods=['GET','POST'])
def get_data():
    data= get_top(min_score=1, n=20, kind='urls')
    #return flask.render_template('url_table.html', result=data)
    return flask.jsonify(result=data)
    
@app.route('/')
def index():
    return flask.render_template('index.html')

if __name__ == '__main__':
    app.debug = True
    app.run(port=11111)