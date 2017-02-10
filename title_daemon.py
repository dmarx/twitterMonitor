import ConfigParser
import requests
from requests.exceptions import ChunkedEncodingError, SSLError
from bs4 import BeautifulSoup
import time
from datetime import datetime
import sqlite3
import ConfigParser
import os
from sqlite3 import OperationalError

here = os.path.dirname(__file__)
config = ConfigParser.ConfigParser()
config.read(os.path.join(here, 'connection.cfg'))

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
    print (str(datetime.now()) + " [TITLE] " + title.encode('utf-8'))
    return orig_url, title   
    
def get_titles(conn, 
                   min_score = int(config.get('app_params','min_score')), 
                   n = int(config.get('app_params','n')), 
                   kind = 'urls'):
    backoff = .1
    while True:
        try:
            top = conn.execute('select id, url, orig_url, title, current_score from entities where type=? and current_score > ? order by current_score desc limit ?', [kind, min_score, n]).fetchall()
            break
        except OperationalError, e:
            print "[DB ERROR]", e
            print "Sleeping", backoff
            time.sleep(backoff)
            backoff*=1.5
    records = []
    ix={d:i for i, d in enumerate(['id', 'url', 'orig_url', 'title', 'current_score'])}
    for rec in top:
        rec = list(rec)
        if not rec[ix['orig_url']]:
            try:
                orig_url, title = post_process_url(rec[ix['url']])
            except Exception, e:
                print '[TITLE DAEMON ERROR]', e
                continue
            #except SSLError:
            #    orig_url, title = rec[ix['url']], rec[ix['url']]
            if not title:
                #title = orig_url
                continue
            par = [orig_url, title, int(rec[ix['id']])]
            backoff = .1
            while True:
                try:
                    conn.execute('UPDATE entities SET orig_url=?, title=? WHERE id = ?', par)
                    conn.commit()
                    break
                except OperationalError, e:
                    print "[DB ERROR]", e, exception_catcher[e]
                    print "Sleeping", backoff
                    time.sleep(backoff)
                    backoff*=1.5

if __name__ == '__main__':
    DB_NAME = os.path.join(here, config.get('database','name'))
    CONN = sqlite3.Connection(DB_NAME)
    last_update = time.time()
    while True:
        delta = time.time() - last_update
        if delta < int(config.get('refresh','titles')):
            time.sleep(delta)
        get_titles(CONN)