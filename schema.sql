CREATE TABLE tweets
    (id         INTEGER PRIMARY KEY AUTOINCREMENT,
     orig_tweet_id   NUMBER UNIQUE,
     user_id    NUMBER,
     created_at NUMBER
     );

CREATE TABLE entities
    (id               INTEGER PRIMARY KEY AUTOINCREMENT,
     type             TEXT, -- one of 'url' or 'media'
     url              TEXT UNIQUE, -- what if a particular URL gets used as both a URL and MEDIA? Use which ever shows first?
     orig_url         TEXT, -- un-minimized url
     title            TEXT,
     first_occurrence INTEGER, -- epoch date
     last_occurrence  INTEGER, -- epoch date
     current_score    NUMBER,
     max_score        NUMBER
     );
     
CREATE TABLE tweet_entities
    (id        INTEGER PRIMARY KEY AUTOINCREMENT,
     tweet_id  NUMBER,
     entity_id NUMBER,
     FOREIGN KEY(tweet_id)  REFERENCES tweet(id),
     FOREIGN KEY(entity_id) REFERENCES entities(id)
     );
     
CREATE TABLE tweet_terms
    (id       INTEGER PRIMARY KEY AUTOINCREMENT,
     tweet_id NUMBER,
     term     TEXT,
     FOREIGN KEY(tweet_id)  REFERENCES tweet(id)
    );
    
CREATE TABLE entity_bow
    (id        INTEGER PRIMARY KEY AUTOINCREMENT,
     entity_id INTEGER,
     token     TEXT,
     cnt       INTEGER,
     FOREIGN KEY(entity_id) REFERENCES entities(id)
    );