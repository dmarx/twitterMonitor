from code.connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
from code.utilities import store_tweets, handle_rate_limiting
from twython import TwythonStreamer

# Looks like the TwythonStreamer class handles rate limiting for me!
tweet=None
N=0
class MyStreamer(TwythonStreamer):
    def on_success(self, data):
        global N
        #if 'text' in data:
        #    N+=1
        #    print N, data['text'].encode('utf-8')
        succ=False
        if 'media' in data['entities']:
            for m in data['entities']['media']:
                if not succ:
                    tweet = data
                    N+=1
                    succ=True
                    print
                print N, "MEDIA", m['expanded_url']
        if 'urls' in data['entities']:
            for u in data['entities']['urls']:
                if not succ:
                    tweet = data
                    N+=1
                    succ=True
                    print
                print N, "URL", u['expanded_url']
                
    def on_error(self, status_code, data):
        print status_code

if __name__ == "__main__":
    stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    stream.statuses.filter(track='YesSheCan')
