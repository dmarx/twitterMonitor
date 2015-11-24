import time
import datetime

def store_tweets(tweets_to_save, collection):
    """
    Simple wrapper to facilitate persisting tweets. Right now, the only
    pre-processing accomplished is coercing 'created_at' attribute to datetime.
    """
    for tw in tweets_to_save:
        tw['created_at'] = datetime.datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
    collection.insert(tweets_to_save)

def handle_rate_limiting(twitter):
    app_status = {'remaining':1} # prepopulating this to make the first 'if' check fail
    while True:
        wait = 0
        if app_status['remaining'] > 0:
            status = twitter.get_application_rate_limit_status(resources = ['statuses', 'application'])
            app_status = status['resources']['application']['/application/rate_limit_status']
            home_status = status['resources']['statuses']['/statuses/home_timeline']
            if home_status['remaining'] == 0:
                wait = max(home_status['reset'] - time.time(), 0) + 1 # addding 1 second pad
                time.sleep(wait)
            else:
                return
        else :
            wait = max(app_status['reset'] - time.time(), 0) + 10
            time.sleep(wait)