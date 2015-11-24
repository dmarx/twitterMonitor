# Based on https://github.com/jkbrzt/chat/blob/master/app.py

import redis
try:
    import ujson as json
except:
    import json
r = redis.StrictRedis()
pubsub = r.pubsub()
pubsub.subscribe('tweet_monitor')
i=0
for message in pubsub.listen():
    i +=1
    #print i
    print message['data']
    print type(message['data'])
    if message['data'] != 1:
        d = json.loads(message['data'])
        print type(d)
        print d
        break