# Let's do this: let's let the  monitor live in a separate thread in this script
# so we can directly access the cache object. Upon a request to the '/get_data'
# endpoint, directly query the cache for the most recent values. The request
# will/can include the following parameters:
#   * max number of seconds to go back 
#     --> default to 5 minutes?
#   * number of datapoints to send (which will be combined with the max time 
#       back to determine the actual time points to get data for)
#     --> default to 100?
#   * number of data items to report on
#     --> default to either 1 or 10


import flask
from requests.exceptions import ChunkedEncodingError
import time
from scraper.scraper import MyStreamer, tweet_cache # the cache should really be attached to the class instead of a separate object
from scraper.datedeque import DateDeque
from scraper.connect import twitter, tweets, APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET
import threading
import datetime as dt
import numpy as np

stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

def monitor_stream():
    global stream
    while True:
        try:
            stream.statuses.filter(track=
                ['terrorist','terrorists','attack','attacked','attacks','killed',
                'hostage','hostages','explosion','bomb','bomber','gunman',
                'gunmen','breaking','war','dead','injured','emergency', 
                'casualties','kidnapped','mob','protest','protesters',
                'shooting','gunfire','arrested','alleged','suspect','suspects',
                'suspected','assassinate','assassinated'])
            #stream.statuses.sample()
        except ChunkedEncodingError, e:
            print "[ERROR]", e
        #except Exception, e:
        #    print "[ERROR]", e

# Start the data monitor

t = threading.Thread(target=monitor_stream)
t.start()

app = flask.Flask(__name__)
app.secret_key = 'asdf'


@app.route('/get_data')
def get_data():
    url, score = tweet_cache.media_scores.most_common(1)
    # Pass in timestamps we want scores for. Might actually make more sense to send
    # these in from the POST request. Anyway, need to pass values into the appropriate KDE
    # to retrieve associated scores.
    now = DateDeque.timestamp()
    # let's go back 5 minutes and return 100 scores
    totsec = 5*60
    delta_sec = np.linspace(0, totsec)
    kde = tweet_cache._kdes['media'][url]
    scores = kde.link_predict(delta_sec)
    t=[now - d for d in delta_sec]
    t_epoch = [(t - dt.datetime(year=1970, month=1, day=1)).total_seconds()]
    result = {'time':t_epoch, 'delta':delta_sec, 'url':url, 'score':scores}
    return jsonify(result=None) # return only single latest message
    
@app.route('/')
def home():
    return """
<!DOCTYPE html>
<meta charset="utf-8">
<style>

svg {
  font: 10px sans-serif;
}

.line {
  fill: none;
  stroke: #000;
  stroke-width: 1.5px;
}

.axis path,
.axis line {
  fill: none;
  stroke: #000;
  shape-rendering: crispEdges;
}

</style>
<body>
<script src="//d3js.org/d3.v3.min.js"></script>
<script>

    var n = 40,
        random = d3.random.normal(0, .2),
        data = d3.range(n).map(random);

    var margin = {top: 20, right: 20, bottom: 20, left: 40},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    var x = d3.scale.linear()
        .domain([0, n - 1])
        .range([0, width]);

    var y = d3.scale.linear()
        .domain([-1, 1])
        .range([height, 0]);

    var line = d3.svg.line()
        .x(function(d, i) { return x(i); })
        .y(function(d, i) { return y(d); });

    var svg = d3.select("body").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    svg.append("defs").append("clipPath")
        .attr("id", "clip")
      .append("rect")
        .attr("width", width)
        .attr("height", height);

    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + y(0) + ")")
        .call(d3.svg.axis().scale(x).orient("bottom"));

    svg.append("g")
        .attr("class", "y axis")
        .call(d3.svg.axis().scale(y).orient("left"));

    var path = svg.append("g")
        .attr("clip-path", "url(#clip)")
      .append("path")
        .datum(data)
        .attr("class", "line")
        .attr("d", line);

    tick();

    function tick() {

      // push a new data point onto the back
      data.push(random());

      // redraw the line, and slide it to the left
      path
          .attr("d", line)
          .attr("transform", null)
        .transition()
          .duration(500)
          .ease("linear")
          .attr("transform", "translate(" + x(-1) + ",0)")
          .each("end", tick);

      // pop the old data point off the front
      data.shift();

    }
    """

if __name__ == '__main__':
    app.debug = True
    app.run(port=11111)