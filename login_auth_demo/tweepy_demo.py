# Following tutorial at https://pythonhosted.org/tweepy/auth_tutorial.html
import ConfigParser
import tweepy

config = ConfigParser.ConfigParser()
config.read('../config/connection.cfg')

# spin up twitter api
APP_KEY    = config.get('credentials','app_key')
APP_SECRET = config.get('credentials','app_secret')

callback_url = 'http://127.0.0.1:1111/twitter_login_auth'
#auth = tweepy.OAuthHandler(APP_KEY, APP_SECRET, callback_url)
auth = tweepy.OAuthHandler(APP_KEY, APP_SECRET)

# Direct user to this URL to login
redirect_url = auth.get_authorization_url()
# https://api.twitter.com/oauth/authorize?oauth_token=V6aZvQAAAAAAWuvuAAABUXj-BiU


# Store request token in session. We will need it in the callback URL request.
# session.set('request_token', (auth.request_token.key, auth.request_token.secret))

# Get pin. Example pin: 8022294
verifier = '9223013'
token = auth.get_access_token(verifier)
key, secret = token
auth.set_access_token(key, secret)

api = tweepy.API(auth)