from TextSummarization.summarizer import normalize_and_tokenize, similarity_graph_from_term_document_matrix, summarize
import newspaper
try:
    import urlparse
except:
    from urllib.parse import urlparse
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from collections import Counter
import networkx as nx
from sklearn.metrics.pairwise import pairwise_kernels

class CorpusSummarizer(object):
    def __init__(self, db, score_threshold = .2, similarity_threshold = .2, n=20):
        self.db = db
        self.score_threshold = score_threshold
        self.similarity_threshold = similarity_threshold
        self.n = n
        self.top_article_ids = []
        self.top_article_urls = {}
        self.top_article_scores = []
        self.article_bows = {}
        self.article_summaries = {}
        self.cluslter_summaries = []
        
        #self.go()
        
    def go(self):
        self.get_top_articles()
        for id in self.top_article_ids:
            self.article_bows[id] = self.get_bow(id)
        #term_doc_matrix = DictVectorizer(self.article_bows.values())
        dv = DictVectorizer()
        tdm = dv.fit_transform(self.article_bows.values())
        tfidf = TfidfTransformer() # Should probably train transformer on a baseline news corpus
        tdm_tfidf = tfidf.fit_transform(tdm)
        clusters = self.cluster_documents(tdm_tfidf)
        # To do:
        #   1. Identify document with highest score in each cluster
        #   2. Get that documents summary, use as summary for the cluster
        for clust in clusters:
            top_article, top_score = -1, -1
            for ix in clust:
                score = self.top_article_scores[id]
                if score > top_score:
                    top_article, top_score = ix, score
            id = self.top_article_ids[ix]
            self.cluslter_summaries.append(self.article_summaries[id])
        return self.cluslter_summaries
        
    def get_top_articles(self):
        """Pull current top articles from database"""
        articles = self.db.conn.execute('select id, coalesce(orig_url, url), current_score from entities where type=? and current_score > ? order by current_score desc limit ?', ['urls', self.score_threshold, self.n]).fetchall()
        
        self.top_article_urls = {id:url for id, url, score in articles} ## This might not be appropriate python3 syntax
        self.top_article_scores = {id:score for id, url, score in articles} ## This might not be appropriate python3 syntax
        self.top_article_ids = self.top_article_urls.keys()
        
    def get_bow(self, id):
        """
        For documents that have already been processed, BOW is pulled from db.
        Otherwise, document text is pulled from GET request, BOW and summary
        are persisted to DB, and BOW is returned.
        """
        bow = self.bow_from_db(id)
        if bow is None or bow == {}:
            #url  = self.db.conn.execute("SELECT url FROM entities WHERE id = ?", [id]).fetchone()[0]
            url = self.top_article_urls[id]
            text = self.get_article_text(url)
            bow  = self.text_to_bow_dict(text)
            #summary = summarize(text) ################# get back to this
            ##### need to add to datamodel #####
            #self.db.persist_bow(id, bow) 
            #self.db.persist_summary(id, summary)
        return bow
            
    def get_article_text(self, url):
        domain = urlparse(url).netloc
        if 'twitter' in domain:
            text = self.get_twitter_text(url)
        else:
            text = self.get_nontwitter_article_text(url)
        return text

    def get_twitter_text(self, url):
        return ''
        pass
        # Get article text via twython
        
    def get_nontwitter_article_text(self, url):
        try:
            article = newspaper.Article(url, language='en')
            article.download()
            article.parse()
            text = article.text
        except Exception as e:
            print("A problem was encountered getting article text")
            print(e)
            text = ''
        return text
        
    def text_to_bow_dict(self, text):
        tokens = normalize_and_tokenize(text)
        return Counter(tokens)
    
    def bow_from_db(self, id):
        pass
        # Need to add to db
        records = self.db.conn.execute("SELECT token, cnt FROM entity_bow WHERE entity_id = ?", [id]).fetchall()
        return {token:count for token, count in records}
        
    def cluster_documents(self, term_doc_matrix, metric='cosine'):
        dx = pairwise_kernels(term_doc_matrix, metric=metric)
        dx[dx<=self.score_threshold] = 0 
        g = nx.from_numpy_matrix(dx)
        return [c for c in nx.connected_components(g) if len(c)>1]
        

if __name__ == "__main__":
    from datamodel import DbApi
    db = DbApi()
    cs = CorpusSummarizer(db)
    
    # building up CorpusSummarizer.go() piecewise
    cs.get_top_articles()
    for id in cs.top_article_ids:
        print(id)
        cs.article_bows[id] = cs.get_bow(id)