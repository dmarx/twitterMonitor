import sqlite3
from load_terms import load_terms
import ConfigParser
import time
from datetime import datetime
from contextlib import closing
import numpy as np
from kde import exp_decay
from urlparse import urlparse
import string
import os
here = os.path.dirname(__file__)

config = ConfigParser.ConfigParser()
config.read(os.path.join(here, 'connection.cfg'))
DB_NAME = os.path.join(here, config.get('database','name'))

tracked_terms = load_terms()

class DbApi(object):
    def __init__(self, db_name=DB_NAME, conn=None):
        if not conn:
            conn = sqlite3.Connection(db_name)
        self.conn = conn
        c = conn.cursor()
        try:
            c.execute('SELECT 1 FROM ENTITIES')
        except:
            with open(os.path.join(here,'schema.sql'), 'r') as f:
                c.executescript(f.read())
            self.conn.create_function("decay", 1, lambda x: exp_decay(x, halflife=300))
        c.close()
        self.last_flushed = 0
        self.flush_interval = 300 # clear out old data every five minutes
        self.last_scored = 0
        self.score_interval = 1
        self.data = None
        
    def persist(self, data):
        self.data = data
        vals = {}
        vals['user_id'] = data['user']['id_str']
        text    = data['text']
        if 'retweeted_status' in data:
            text += " " + data['retweeted_status']['text']
        #if data['is_quote_status']:
        if 'quoted_status' in data:
            text += " " + data['quoted_status']['text']
        text.replace('#','')
        exclude = set(string.punctuation)
        ### Instead of deleting punctuation, let's replace with spaces to protect possessives/contractions/etc
        text = ''.join(ch if ch not in exclude else ' ' for ch in text) 
        tokens = text.lower().split(' ')
        vals['terms'] = [t for t in tracked_terms if t in tokens]
        vals['created_at'] =  time.time() #data['created_at']
        vals['orig_tweet_id'] = data['id']
        
        with closing(self.conn.cursor()) as c:
            try:
                vals['tweet_id'] = self.register_tweet(c, vals)
                self.persist_entities(c, data, vals, 'urls')
                self.persist_entities(c, data, vals, 'media')
                self.persist_terms(c, vals)
            except sqlite3.IntegrityError, e:
                print e
                self.conn.rollback()
                return
            
            self.update_scores(c)
            self.conn.commit()
            
            self.flush_old_data(c)
            self.conn.commit()
            
        #c.close()
        
    def register_tweet(self, c, vals):
        sql = """
        INSERT INTO tweets (orig_tweet_id, user_id, created_at) VALUES (?,?,?)
        """
        par = (vals['orig_tweet_id'], int(vals['user_id']), vals['created_at'])
        #print "par", par
        c.execute(sql, par)
        #print "succcess: register tweet"
        id = c.lastrowid
        #print "rowid", id
        return id
    
    def persist_terms(self, c, vals):
        sql = """
        INSERT INTO tweet_terms (tweet_id, term) VALUES (?,?)
        """
        id = vals['tweet_id']
        for term in vals['terms']:
            par = (id, term)
            c.execute(sql, par)
            #print "succcess: persist term"
    def persist_entities(self, c, data, vals, kind):    
        sql_entity_id = """
        SELECT id
        FROM ENTITIES 
        WHERE url = ?
        """
        
        sql_entity_update_last = """
        UPDATE ENTITIES SET last_occurrence = ? WHERE url = ?
        """
        
        sql_entities_insert = """
        INSERT INTO entities (type, url, first_occurrence, last_occurrence) VALUES (?,?,?,?)
        """
        
        sql_entity_tweet_xref = """
        INSERT INTO tweet_entities (tweet_id, entity_id) VALUES (?,?)
        """
        
        tweet_id = vals['tweet_id']
        if data['entities'].has_key(kind):
            for url1 in data['entities'][kind]:
                #print "url1", url1
                url = url1['expanded_url']
                if not url:
                    continue
                if urlparse(url).netloc.lower() == 'twitter.com':
                    url = url.lower() # standardize twitter urls.
                print (str(datetime.now()) + " [URL] " + url.encode('utf-8'))
                #try:
                #    print "url", url
                #except UnicodeEncodeError:
                #    print "[Error] UnicodeEncodeError"
                test = c.execute(sql_entity_id, [url]).fetchall()
                if len(test) > 0:
                    #print "WE'RE IN!"
                    entity_id = test[0][0]
                    #print entity_id
                    #raise Exception("break!")
                    c.execute(sql_entity_update_last, [vals['created_at'], url])
                else:
                    
                    c.execute(sql_entities_insert, [kind, url, vals['created_at'], vals['created_at']])
                    entity_id = c.lastrowid
                c.execute(sql_entity_tweet_xref, [tweet_id, entity_id])
                

    def update_scores(self, c):
        now = time.time()
        if now - self.last_scored < self.score_interval:
            return
        
        self.conn.create_function("decay", 1, lambda x: exp_decay(x, halflife=300))
        
        sql_update_current_scores = """
        UPDATE entities
        SET current_score = (
            SELECT sum(decay(? - created_at))
            FROM tweets t,
                 tweet_entities x
            WHERE x.entity_id = entities.id
            AND   x.tweet_id = t.id
            GROUP BY entity_id
        )
        WHERE current_score > 1
        OR ?-last_occurrence < 60 -- ignore items we haven't seen in the last minute.
        """
        
        sql_update_max_scores = """
        UPDATE entities
        SET max_score = current_score
        WHERE current_score > max_score
        """
        
        c.execute(sql_update_current_scores, [now, now])
        c.execute(sql_update_max_scores)
        
        self.last_scored = now
        
    def flush_old_data(self, c):
        now = time.time()
        if now - self.last_flushed < self.flush_interval:
            return
        
        sql_delete_old_tweets = """
        DELETE FROM tweets
        WHERE ?-created_at > 3600
        """
        
        sql_delete_orphan_rel_terms = """
        DELETE FROM tweet_terms
        WHERE NOT EXISTS (
            SELECT 1 FROM tweets t
            WHERE t.id = tweet_terms.tweet_id
        )
        """
        
        sql_delete_orphan_rel_entities = """
        DELETE FROM tweet_entities
        WHERE NOT EXISTS (
            SELECT 1 FROM tweets t
            WHERE t.id = tweet_entities.tweet_id
        )
        """
        
        sql_delete_orphan_entities = """
        DELETE FROM entities
        WHERE NOT EXISTS (
            SELECT 1 FROM tweet_entities te
            WHERE entities.id = te.entity_id
        )
        """
        
        c.execute(sql_delete_old_tweets, [now])
        c.execute(sql_delete_orphan_rel_terms)
        c.execute(sql_delete_orphan_rel_entities)
        c.execute(sql_delete_orphan_entities)
        
        self.last_flushed = now
        
    # def update_url_score(self, c, url, new=True):
        # if new:
            # score = 1
        # else:
            # sql_get_times = """
            # SELECT t.created_at
            # FROM tweets t, 
                 # entities e,
                 # tweet_entities xref
            # WHERE e.url = ?
            # AND   xref.entity_id = e.id
            # AND   xref.tweet_id  = t.id
            # """            
            # times = c.execute(sql_get_times, [url]).fetchall()
            # times = np.array(times)
            
            # kde=NegExpDecayKDE(halflife=300)
            # kde.fit(times)
            # score = kde.predict(0)
        
        # sql_get_max_score = """
        # SELECT max_score FROM entities WHERE url = ?
        # """
        
        # sql_update_score = """
        # UPDATE entities SET 
            # current_score = ?,
            # max_score = ?
        # WHERE url = ?
        # """
        # max_score = c.execute(sql_get_max_score, [url]).fetchall()[0][0]
        # if max_score < score:
            # max_score = score
        # c.execute(sql_update_score, [score, max_score, url])
        