# Based on https://github.com/jkbrzt/chat/blob/master/app.py

import redis

r = redis.StrictRedis()
pubsub = r.pubsub()
pubsub.subscribe('tweet_monitor')
i=0
for message in pubsub.listen():
    i +=1
    print i