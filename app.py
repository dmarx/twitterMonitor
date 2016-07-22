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
import datetime as dt
import numpy as np
#from scraper import MyStreamer
import sqlite3
import ConfigParser
from urlparse import urlparse
import requests
from bs4 import BeautifulSoup
from load_terms import load_terms
import os
here = os.path.dirname(__file__)

config = ConfigParser.ConfigParser()
config.read(os.path.join(here, 'connection.cfg'))
DB_NAME = os.path.join(here, config.get('database','name'))

terms = load_terms()

RECORDS_CACHE = (None, 0)

def post_process_url(url):
    """
    Gets the title element from a url
    """
    response = requests.get(url)
    orig_url = response.url
    soup = BeautifulSoup(response.text, "html.parser")
    try:
        title = soup.title.text.strip()
    except:
        title = url
    print ("[TITLE]", title)
    return orig_url, title    

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
    ix={d:i for i, d in enumerate(['id', 'url', 'orig_url', 'title', 'current_score'])}
    global RECORDS_CACHE
    cached_rec, cached_time = RECORDS_CACHE
    now = time.time()
    if now - cached_time < 1:
        records = cached_rec
    else:
        top = g.sqlite_db.execute('select id, url, orig_url, title, current_score from entities where type=? and current_score > ? order by current_score desc limit ?', [kind, min_score, n]).fetchall()
        records = []
        for rec in top:
            rec = list(rec)
            if not rec[ix['orig_url']]:
                orig_url, title = post_process_url(rec[ix['url']])
                if not title:
                    title = orig_url
                par = [orig_url, title, int(rec[ix['id']])]
                c = g.sqlite_db.cursor()
                c.execute('UPDATE entities SET orig_url=?, title=? WHERE id = ?', par)
                g.sqlite_db.commit()
                rec[ix['orig_url']] = orig_url
                rec[ix['title']] = title
            records.append(rec)
        RECORDS_CACHE = (records, now)
    return [{'url':rec[ix['orig_url']], 'domain':urlparse(rec[ix['orig_url']]).netloc, 'score':rec[ix['current_score']], 'title':rec[ix['title']]} for rec in records]

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
