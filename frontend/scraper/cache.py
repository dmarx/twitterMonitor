from datedeque import DateDeque
from collections import defaultdict, Counter
from urlparse import urlparse
try:
    import ujson as json
except:
    import json
import numpy as np
import threading
    
#For exponential kde, scale=500 seems to work ok (this is just under 10 minutes, which I believe gives about an 18 minute halflife)
from kde import NegGammaKDELinked, NegExponentialKDELinked, NegExpDecayKDELinked
    
class TweetCache(object):
    def __init__(self, **kargs):
        """
        Initialize with input appropriate to a datetime.timedelta object, 
        e.g. to cause entries to expire after one hour:
            cache = TweetCache(minutes=60)
            
        Most frequent URLs and media (images, vines, videos...) can be extracted
        using Counter attributes:
            cache.urls.most_common(10)
            cache.media.most_common(10)
        """
        def subcache():
            return DateDeque(**kargs)
        self._cache = {}
        # Containers for events
        self._cache['urls']  = defaultdict(subcache)
        self._cache['media'] = defaultdict(subcache)
        # Counters for containers
        #self.urls   = Counter()
        #self.media = Counter()
        self._counters = {}
        self._counters['urls'] = Counter()
        self._counters['media'] = Counter()
        #self._unq_users
        #self._unq_users['urls']  = defaultdict(set)
        #self._unq_users['media'] = defaultdict(set)
        self._kdes = {'urls':{}, 'media':{}} # kernel density estimators that will be linked to DateDeque timestamps
        self.lock = threading.RLock()
    @property
    def urls(self):
        return self._counters['urls']
    @property
    def media(self):
        return self._counters['media']
    @property
    def url_users(self):
        with self.lock:
            #return Counter( ( k, len(set(v)) ) for k,v in self._cache['urls'])
            cnt = Counter()
            for k,v in self._cache['urls'].iteritems():
                cnt[k] = len(set(entry[1] for entry in v))
            return cnt
    @property
    def media_users(self):
        with self.lock:
            #return Counter( ( k, len(set(v)) ) for k,v in self._cache['media'])
            cnt = Counter()
            for k,v in self._cache['media'].iteritems():
                cnt[k] = len(set(entry[1] for entry in v))
            return cnt
    @property
    def url_scores(self):
        with self.lock:
            #return Counter(dict( (k, np.log(v.link_predict()[0])) for k,v in self._kdes['urls'].iteritems() ))
            return Counter(dict( (k, v.link_predict()[0]) for k,v in self._kdes['urls'].iteritems() ))
    @property
    def media_scores(self):
        with self.lock:
            #return Counter(dict( (k, np.log(v.link_predict()[0])) for k,v in self._kdes['media'].iteritems() ))
            return Counter(dict( (k, v.link_predict()[0]) for k,v in self._kdes['media'].iteritems() ))
    def _internal_update(self, item, dict_type, user_id, data):
        with self.lock:
            url = item['expanded_url']
            # ignore any urls that are links to a landing page i.e. don't look like 
            # they link to a file or article.
            if urlparse(url).path in('','/'):
                return
            if not self._stored and hasattr(self, 'datastore'):
                if self.datastore:
                    self.datastore.insert(data)
            
            #self._cache[dict_type][url].append(True)
            self._cache[dict_type][url].append(user_id)
            self._counters[dict_type][url] = len(self._cache[dict_type][url])
            if not self._kdes[dict_type].has_key(url): 
                #estimator = NegExponentialKDELinked(scale=1/50.)
                estimator = NegExpDecayKDELinked(halflife=300)
                estimator.link_container(self._cache[dict_type][url].TTL)
                self._kdes[dict_type][url] = estimator
            self._refresh_all()
            #self.publish()
    def _refresh_all(self):
        for dict_type, cache in self._cache.iteritems():
            for k, v in cache.iteritems():
                self._counters[dict_type][k] = len(v) # Presumes that calling len will induce expiration/flush.
                if self._counters[dict_type][k] == 0:
                    self._counters[dict_type].pop(k)
                    self._kdes[dict_type].pop(k)
    def update(self, data):
        #if any(k in data['entities'].keys() for k in ('urls', 'media')):
        if any(k in data.entities.keys() for k in ('urls', 'media')):
            self._stored = False
            user_id = data.user.id_str
            if data.entities.has_key('urls'):
                for item in data.entities['urls']:
                    self._internal_update(item, 'urls', user_id, data)
                    # url = item['expanded_url']
                    # self._cache['urls'][url].append(True)
                    # self.urls[url] = len(self._cache['urls'][url])
                    # if self.urls[url]
            if data.entities.has_key('media'):
                for item in data.entities['media']:
                    self._internal_update(item, 'media', user_id, data)
                    # url = item['expanded_url']
                    # self._cache['media'][url].append(True)
                    # self.media[url] = len(self._cache['media'][url])
    def register_datastore(self, datastore):
        """
        Datastore must have an "insert" method and accept arbitrary tweet 
        objects as inputs. Simplest usage is to pass in a mongodb collection.
        
        Unregister by registering the None object as the datastore.
        """
        self.datastore = datastore
    def publish(self, msg):
        pass
        # If active, we'll define this when we call self.register_pubsub
    def register_pubsub(self, pubsub, channel):
        """
        Register a publish/subscribe system for message passing. In particular,
        for communicating specific statistics from within the cache to a 
        real-time analytics front-end.
        
        It's expected that the pubsub will have a publish attribute that works 
        similar to redis, i.e.
        
            pubsub.publish(channel_name, message)
        
        expected recipe:
            import redis
            r = redis.StrictRedis()
            cache = TweetCache(minutes=60)
            cache.register_pubsub(red, 'cache')
        """
        self._pubsub = pubsub
        self._pubsub_channel = channel
        self._last_msg = None
        def publish():
            """
            Publish data via the registered pubsub on the {} channel
            """.format(self._pubsub_channel)
            if hasattr(self, '_pubsub'):
                if self._pubsub:
                    msg = self._message
                    # Only publish a message if there's been a change to the data
                    # being transmitted.
                    if msg != self._last_msg:
                        self._last_msg = msg
                        #self.publish(msg)
                        self._pubsub.publish(self._pubsub_channel, msg)
        self.publish = publish
    @property
    def _message(self):
        total_urls  = sum(self.urls.values())
        total_media = sum(self.media.values())
        # We'll represent scores as XX.XX %. To handle floating point issues, 
        # multiply the decimal representation by 1e4, truncate as an integer, 
        # and pass the integer in the message.
        msg = {
            'urls':{
                'top_by_count':[{'url':url_cnt[0], 'rank':i+1, 'score':int(10000*url_cnt[1]/total_urls)} 
                    for i, url_cnt in enumerate(self.urls.most_common(10))],
                'top_by_users':[{'url':url_cnt[0], 'rank':i+1, 'score':int(1000*url_cnt[1]/total_urls)}
                    for i, url_cnt in enumerate(self.url_users.most_common(10))]
                #'unique':len(self.urls),
                #'n_users':len(self.url_users)
            },
            'media':{
                #'top_by_count':[url for url, _ in self.media.most_common(10)],
                #'top_by_users':[url for url, _ in self.media_users.most_common(10)],
                'top_by_count':[{'url':url_cnt[0], 'rank':i+1, 'score':int(10000*url_cnt[1]/total_media)} 
                    for i, url_cnt in enumerate(self.media.most_common(10))],
                'top_by_users':[{'url':url_cnt[0], 'rank':i+1, 'score':int(10000*url_cnt[1]/total_media)} 
                    for i, url_cnt in enumerate(self.media_users.most_common(10))]
                #'unique':len(self.media),
                #'n_users':len(self.media_users)
            }
        }
        return json.dumps(msg)
    def __len__(self):
        self._refresh_all()
        return sum(len(v) for v in self._counters.values())
            