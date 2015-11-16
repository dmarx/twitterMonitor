from datedeque_rough import DateDeque
from collections import defaultdict, Counter
from urlparse import urlparse

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
    @property
    def urls(self):
        return self._counters['urls']
    @property
    def media(self):
        return self._counters['media']
    @property
    def url_users(self):
        #return Counter( ( k, len(set(v)) ) for k,v in self._cache['urls'])
        cnt = Counter()
        for k,v in self._cache['urls'].iteritems():
            cnt[k] = len(set(entry[1] for entry in v))
        return cnt
    @property
    def media_users(self):
        #return Counter( ( k, len(set(v)) ) for k,v in self._cache['media'])
        cnt = Counter()
        for k,v in self._cache['media'].iteritems():
            cnt[k] = len(set(entry[1] for entry in v))
        return cnt
    def _internal_update(self, item, dict_type, user_id, data):
        url = item['expanded_url']
        # ignore any urls that are links to a landing page i.e. don't look like 
        # they link to a file or article.
        if urlparse(url).path in('','/'):
            return
        if not self._stored:
            self.datastore.insert(data)
        #self._cache[dict_type][url].append(True)
        self._cache[dict_type][url].append(user_id)
        self._counters[dict_type][url] = len(self._cache[dict_type][url])
        self._refresh_all()
    def _refresh_all(self):
        for type, cache in self._cache.iteritems():
            for k, v in cache.iteritems():
                self._counters[type][k] = len(v) # Presumes that calling len will induce expiration/flush.
                if self._counters[type][k] == 0:
                    self._counters[type].pop(k)
    def update(self, data):
        if any(k in data['entities'].keys() for k in ('urls', 'media')):
            self._stored = False
            user_id = data['user']['id_str']
            if data['entities'].has_key('urls'):
                for item in data['entities']['urls']:
                    self._internal_update(item, 'urls', user_id, data)
                    # url = item['expanded_url']
                    # self._cache['urls'][url].append(True)
                    # self.urls[url] = len(self._cache['urls'][url])
                    # if self.urls[url]
            if data['entities'].has_key('media'):
                for item in data['entities']['media']:
                    self._internal_update(item, 'media', user_id, data)
                    # url = item['expanded_url']
                    # self._cache['media'][url].append(True)
                    # self.media[url] = len(self._cache['media'][url])
    def register_datastore(self, datastore):
        """
        Datastore must have an "insert" method and accept arbitrary tweet 
        objects as inputs. Simplest usage is to pass in a mongodb collection
        """
        self.datastore = datastore
    def __len__(self):
        self._refresh_all()
        return sum(len(v) for v in self._counters.values())
            