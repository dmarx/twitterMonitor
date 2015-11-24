"""
Spin up a connection to the twitter API and local database
"""

import ConfigParser
from pymongo import Connection
from twython import Twython, TwythonRateLimitError

config = ConfigParser.ConfigParser()
config.read('../config/connection.cfg')

# spin up twitter api
APP_KEY    = config.get('credentials','app_key')
APP_SECRET = config.get('credentials','app_secret')
OAUTH_TOKEN  = config.get('credentials','oath_token')
OAUTH_TOKEN_SECRET = config.get('credentials','oath_token_secret')

# Do I really need to associate the app with a specific twitter account?
# Is there a way to have the app without an oauth access token?
#twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
#twitter.verify_credentials()

twitter = Twython(APP_KEY, APP_SECRET, oauth_version=2)
ACCESS_TOKEN = twitter.obtain_access_token()
twitter = Twython(APP_KEY, access_token=ACCESS_TOKEN)
try:
    # spin up database
    DBNAME = config.get('database', 'name')
    COLLECTION = config.get('database', 'collection')
    conn = Connection()
    db = conn[DBNAME]
    tweets = db[COLLECTION]
except:
    print "MongoDB connection refused. Tweets will not be persisted."
    tweets = None