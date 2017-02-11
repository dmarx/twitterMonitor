try:
    from ConfigParser import ConfigParser
except:
    from configparser import ConfigParser
import os
here = os.path.dirname(__file__)

config = ConfigParser()
config.read(os.path.join(here, 'connection.cfg'))
fpath = os.path.join(here,config.get('terms','location'))

def load_terms():
    terms = []
    with open(fpath, 'r') as f:
        for term in f:
            terms.append(term.strip())
    return terms