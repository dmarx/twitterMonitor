import ConfigParser

config = ConfigParser.ConfigParser()
config.read('connection.cfg')
fpath = config.get('terms','location')

def load_terms():
    terms = []
    with open(fpath, 'r') as f:
        for term in f:
            terms.append(term)
    return terms