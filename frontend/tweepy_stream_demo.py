import tweepy

data=''

class MyStreamer(tweepy.StreamListener):
    def on_status(slef, status):
        global data
        data = status
        raise Exception
        
if __name__ is '__main__':
    import ConfigParser

    config = ConfigParser.ConfigParser()
    config.read('../config/connection.cfg')

    # spin up twitter api
    APP_KEY    = config.get('credentials','app_key')
    APP_SECRET = config.get('credentials','app_secret')
    OAUTH_TOKEN  = config.get('credentials','oath_token')
    OAUTH_TOKEN_SECRET = config.get('credentials','oath_token_secret')
    
    auth = tweepy.OAuthHandler(APP_KEY, APP_SECRET)
    auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    api = tweepy.API(auth)
    Listener = MyStreamer()
    stream = tweepy.Stream(auth=api.auth, listener=Listener)
    
    stream.filter(track=['python'])