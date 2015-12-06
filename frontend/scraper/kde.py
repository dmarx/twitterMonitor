"""
Generic kernel density estimation class, along with demo gamma and exponential 
estimators to demonstrate inheritance. Default kernel is gaussian.
"""
from __future__ import division
import numpy as np
import scipy.stats as stats

g=stats.gamma(a=10,scale=.5)

def exp_decay1(t, x0=1, decay_const=None, expected_lifetime=None, halflife=None):
    """
    A simple exponential decay function. One (and only one) of decay_const, 
    expected_lifetime, or halflife must be set to a positive value.
    """
    assert sum(var is not None for var in 
        (decay_const, expected_lifetime, halflife)) == 1
    if expected_lifetime:
        decay_const = 1/expected_lifetime
    if halflife:
        decay_const = np.log(2)/halflife
    outv =  x0 * np.exp(-t * decay_const)
    if not isinstance(t, np.ndarray):
        if t<0:
            outv = 0
    else:
        outv[t<0] = 0
    return outv
    
# smoothed version
def exp_decay(t, x0=1, decay_const=None, expected_lifetime=None, halflife=None):
        return g.cdf(t) * exp_decay1(t, x0, decay_const, expected_lifetime, halflife)

    
class KDE1d(object):
    def __init__(self, kernel=stats.norm.pdf, bw=1, normalized=True, **kargs):
        """
        kernel: a function that can take a np.ndarray as input
        bw: kernel bandwidth
        **kargs: additional arguments to be passed into the kernel function 
            (e.g. scale/location)
        """
        self.kernel = kernel
        self.bw = bw
        self.loci = np.array([], ndmin=2)
        self._kargs = kargs
        self.normalized = normalized
    def fit(self, x, update=False):
        if len(x.shape)==1:
            y = x[:,np.newaxis]
        elif len(x.shape) ==2:
            y=x
        else:
            y=x.ravel()
        
        if update:
            if hasattr(self,'loci'):
                self.loci = np.concatenate(self.loci, y)
        else:
            self.loci = y
    def predict(self, x):
        x = np.asarray(x)
        mat = np.zeros(shape=[len(self.loci), len(x)]) + x
        est = self.kernel((mat-self.loci)/self.bw, **self._kargs)
        if self.normalized:
            retval = est.mean(axis=0)
        else:
            retval = est.sum(axis=0)
        return retval
        
class KDEDatetimeMixin(object):
    @staticmethod
    def timestamp():
        st = time.gmtime(time.time())
        return datetime(*st[:7])
    # def track_datetime(self, x):
        # """Register an external object containing datetimes to track"""
        # self._linked_dt = x
    # @property
    # def seconds_elapsed(self):
        # now = self.timestamp()
        # return np.asarray([(now - x).total_seconds for x in self.linked_dt])
    # def track_predict(self):
        # self.fit(self.seconds_elapsed, update=False)
        # return self.predict(0)
        
class KDETrackingMixin(object):
    def link_container(self, x):
        """Register a container whose values we'll track by referencing the object with each predict call."""
        self._linked_loci = x
    def link_predict(self, x=None):
        #del self.loci
        #self.fit(np.asarray(self._linked_loci()))
        self.fit()
        if x is None:
            x = np.zeros(1) #self.loci[0]
        return self.predict(x)
    def fit(self):
        if hasattr(self, 'loci'):
            del self.loci # this is nasty, and also may not do anything.
        super(KDETrackingMixin, self).fit(np.asarray(self._linked_loci()))
    
# reverse the propogation direction of the parent class's kernel
class NegKDEMixin(object):
    def __init__(self, **kargs):
        super(NegKDEMixin, self).__init__(**kargs)
        oldkernel = self.kernel
        self.kernel = lambda x,**x_kargs: oldkernel(-1*x, **x_kargs)
        
        
        
class ExpDecayKDE(KDE1d):
    def __init__(self, **kargs):
        super(ExpDecayKDE, self).__init__(kernel=exp_decay, normalized=False, **kargs)
        
class ExponentialKDE(KDE1d):
    def __init__(self, **kargs):
        super(ExponentialKDE, self).__init__(kernel=stats.expon.pdf, **kargs)
        
class GammaKDE(KDE1d):
    def __init__(self, **kargs):
        super(GammaKDE, self).__init__(kernel=stats.gamma.pdf, **kargs)
        
        
        
class ExpDecayKDELinked(KDETrackingMixin, ExpDecayKDE):
    pass
        
class ExponentialKDELinked(KDETrackingMixin, ExponentialKDE):
    pass
        
class GammaKDELinked(KDETrackingMixin, GammaKDE):
    pass
        
        
        
class NegExpDecayKDELinked(NegKDEMixin, ExpDecayKDELinked):
    pass
        
class NegExponentialKDELinked(NegKDEMixin, ExponentialKDELinked):
    pass
        
class NegGammaKDELinked(NegKDEMixin, GammaKDELinked):
    pass
        
        
        
class ExponentialKDELinkedDates(ExponentialKDE, KDEDatetimeMixin):
    pass
    
class GammaKDELinkedDates(GammaKDE, KDEDatetimeMixin):
    pass
