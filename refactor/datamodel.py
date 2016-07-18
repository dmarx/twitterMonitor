import sqlite3
from load_terms import load_terms
import ConfigParser
import time
from contextlib import closing
import numpy as np
from kde import NegExpDecayKDE

config = ConfigParser.ConfigParser()
config.read('connection.cfg')
DB_NAME = config.get('database','name')

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
            with open('schema.sql', 'r') as f:
                c.executescript(f.read())
        c.close()
        
    def persist(self, data):
        vals = {}
        vals['user_id'] = data['user']['id_str']
        text    = data['text']
        text.replace('#','')
        tokens = text.lower().split(' ')
        vals['terms'] = [t for t in tracked_terms if t in tokens]
        vals['created_at'] =  time.time() #data['created_at']
        vals['orig_tweet_id'] = data['id']
        
        with closing(self.conn.cursor()) as c:
            
            vals['tweet_id'] = self.register_tweet(c, vals)
            self.persist_entities(c, data, vals, 'urls')
            self.persist_entities(c, data, vals, 'media')
            self.persist_terms(c, vals)
            
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
            print "succcess: persist term"
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
                print "url", url
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
                
    def update_url_score(self, c, url, new=True):
        if new:
            score = 1
        else:
            sql_get_times = """
            SELECT t.created_at
            FROM tweets t, 
                 entities e,
                 tweet_entities xref
            WHERE e.url = ?
            AND   xref.entity_id = e.id
            AND   xref.tweet_id  = t.id
            """            
            times = c.execute(sql_get_times, [url]).fetchall()
            times = np.array(times)
            
            kde=NegExpDecayKDE(halflife=300)
            kde.fit(times)
            score = kde.predict(0)
        
        sql_get_max_score = """
        SELECT max_score FROM entities WHERE url = ?
        """
        
        sql_update_score = """
        UPDATE entities SET 
            current_score = ?,
            max_score = ?
        WHERE url = ?
        """
        max_score = c.execute(sql_get_max_score, [url]).fetchall()[0][0]
        if max_score < score:
            max_score = score
        c.execute(sql_update_score, [score, max_score, url])
        
        