from collections import deque, OrderedDict
from datetime import datetime, timedelta
import time

#I could probably clean this up a lot with some simple decorators
class DateDeque(deque): 
    """
    Collection where each item is associated with a timestamp upon insertion.
    Following an insertion event, a test of object length, or basically any 
    attached method call really, the timestamp at the front of the queue is 
    tested against the timedelta parameters that were defined when the queue was 
    initialized. If the time difference from the curent time to the stamp is 
    greater than the delta, the item is popped. This is repeated until all tail 
    items that fail the test have been popped. 
    
    This process is accomplished via the internal "flush" method, which is 
    called as a component of nearly all method calls.
    
    The motivation behind this class is to serve as a date-constrained cache
    for webscraping, where it might be relevant to retain objects until they reach
    a certain fixed age.
    
    the remove() and count() methods will not work properly because of the coersion to tuples.
    Maybe instead of creating tuples, I should tack on a separate container to store the 
    associated timestamps. I'm concernted that tracking the pair mappings will introduce bugs.
    """
    def __init__(self, **kargs):
        self.delta = timedelta(**kargs)
    @staticmethod
    def timestamp():
        st = time.gmtime(time.time())
        return datetime(*st[:7])
    def append(self, X):
        super(DateDeque, self).append(self._date_augment(X))
        self.flush()
    def appendleft(self, X):
        super(DateDeque, self).appendleft(self._date_augment(X))
        self.flush()
    def extend(self, X):
        super(DateDeque, self).extend([self._date_augment(x) for x in X])
        self.flush()
    def extendleft(self, X):
        super(DateDeque, self).extendleft([self._date_augment(x) for x in X])
        self.flush()
    def pop(self, X):
        self.flush()
        d, v = super(DateDeque, self).pop([self._date_augment(x) for x in X])
        return v
    def popleft(self):
        self.flush()        
        d, v = super(DateDeque, self).popleft()
        return v
    def _date_augment(self, x):
        return (self.timestamp(), x)
    def flush(self):
        now = self.timestamp()
        while True:
            #if len(self) == 0: # This is circular
            if super(DateDeque, self).__len__() == 0:
                break
            d = now - self[0][0]
            if d > self.delta:
                super(DateDeque, self).popleft()
            else:
                break
    def __len__(self):
        self.flush()
        return super(DateDeque, self).__len__()
    #def next(self):
    #    return super(DateDeque, self).next()[1] # return value w/o datestamp