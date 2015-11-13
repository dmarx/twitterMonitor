from collections import deque, OrderedDict
from datetime import datetime, timedelta
import time

class DateCacheMixin(object):
    def __init__(self, **kargs):
        self.delta = timedelta(**kargs)
    @staticmethod
    def timestamp():
        st = time.gmtime(time.time())
        return datetime(*st[:7])
    def _date_augment(self, x):
        return (self.timestamp(), x)
    def _get_last(self):
        return self[0]
    def _flushpopleft(self):
        v = self[0]
        self = self[1:]
        return v
    def _recover_value(self, x):
        return x[1]
    def _recover_date(self, x):
        return x[0]
    def _flush(self):
        now = self.timestamp()
        while True:
            # This should never be an issue, but adding it in just to be safe. 
            # The size of the queue should always be at least 1 after the first
            # call to self.extend() since the element(s) we're adding 
            if len(self) == 0:
                break
            d = self._recover_date(self._get_last())
            difference = now - d
            if difference > self.delta:
                self._flushpopleft()
            else:
                break                
    def __repr__(self):
        self._flush()
        return super(type(self), self).__repr__()
    def __str__(self):
        self._flush()
        return super(type(self), self).__str__()
    
#I could probably clean this up a lot with some simple decorators
class DateDeque(deque, DateCacheMixin): 
    """
    Collection where each item is associated with a timestamp upon insertion.
    Following an insertion event, the timestamp at the front of the queue is 
    tested against the timedelta parameters that were defined with the queue was 
    initialized. If the time difference from the curent time to the stamp
    is greater than the delta, the item is popped. This is repeated until
    all tail items that fail the test have been popped.
    
    The motivation behind this class is to serve as a date-constrained cache
    for webscraping, where it might be relevant to retain objects until they reach
    a certain fixed age.
    
    the remove() and count() methods will not work properly because of the coersion to tuples.
    Maybe instead of creating tuples, I should tack on a separate container to store the 
    associated timestamps. I'm concernted that tracking the pair mappings will introduce bugs.
    """
    def append(self, X):
        super(DateDeque, self).append(self._date_augment(X))
        self._flush()
    def appendleft(self, X):
        super(DateDeque, self).appendleft(self._date_augment(X))
        self._flush()
    def extend(self, X):
        super(DateDeque, self).extend([self._date_augment(x) for x in X])
        self._flush()
    def extendleft(self, X):
        super(DateDeque, self).extendleft([self._date_augment(x) for x in X])
        self._flush()
    def pop(self):
        self._flush()
        d, v = super(DateDeque, self).pop()
        return v
    def popleft(self): 
        self._flush()
        d, v = super(DateDeque, self).popleft()
        return v
    def _flushpopleft(self): # override
        return super(DateDeque, self).popleft()
        
##################################################################

class DateLimitedOrderedDict(OrderedDict, DateCacheMixin):
    def __init__(self, **kargs):
        DateCacheMixin.__init__(self, **kargs)
        super(DateLimitedOrderedDict, self).__init__() # Required to initialize self._OrderedDict__root
    # NB: Can't override __getitem__ because itervalues, which is being called in _get_last, utilizes the __getitem__
    # method, so santizing the return value here passes an integer to _recover_date, breaking the class.
    def get(self, k):
        self._flush()
        return self._recover_value(self[k])
    def __setitem__(self, k, v):
        super(DateLimitedOrderedDict, self).__setitem__(key=k, value=self._date_augment(v))
        self._flush()
    def _flushpopleft(self):
        return super(DateLimitedOrderedDict, self).popitem(last=False)
    def _get_last(self): 
        return self.itervalues().next()
    def __str__(self):
       return DateCacheMixin.__str__(self)
    def __repr__(self):
       return DateCacheMixin.__repr__(self)