from datedeque import DateLimitedDeque
from collections import defaultdict, Counter

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
            return DateLimitedDeque(**kargs)
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
    @property
    def urls(self):
        return self._counters['urls']
    @property
    def media(self):
        return self._counters['media']
    def _internal_update(self, item, dict_type):
        url = item['expanded_url']
        self._cache[dict_type][url].append(True)
        self.urls[url] = len(self._cache[dict_type][url])
        if self._counters[dict_type][url] == 0:
            self._counters[dict_type].pop(url)
    def update(self, data):
        if data['entities'].has_key('urls'):
            for item in data['entities']['urls']:
                self._internal_update(item, 'urls')
                # url = item['expanded_url']
                # self._cache['urls'][url].append(True)
                # self.urls[url] = len(self._cache['urls'][url])
                # if self.urls[url]
        if data['entities'].has_key('media'):
            for item in data['entities']['media']:
                self._internal_update(item, 'media')
                # url = item['expanded_url']
                # self._cache['media'][url].append(True)
                # self.media[url] = len(self._cache['media'][url])
    
            