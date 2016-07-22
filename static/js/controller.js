    
    var n = 1000; // number of data points to draw
    var max_delta = 300;
    var m = 20;//5; // number of lines to draw (i.e. number of items to report on)
    var temp=[]; // array that will be used as an intermediary to pass the ajax response into the global scope
    var data=[]; // this is what the line data will ultimately be bound to.
    for(i=0;i<m;i++){
        data.push([{url:'', score:0, timestamp:0, i:0}]);
    };
    
    // To start with, lots set series color to rank.
    // as a url changes in rank though, we don't want it to change color. 
    // Fix urls to colors using a hash map that
    var color = d3.scale.category10();
    
    //var random = d3.random.normal(0, .2);
    //var data = d3.range(n).map(random);

    var margin = {top: 20, right: 20, bottom: 20, left: 40},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    var x = d3.scale.linear()
        .domain([0, max_delta])
        .range([0, width]);

    var y = d3.scale.linear()
        .domain([0, 100])
        .range([height, 0]);

    var line = d3.svg.line()
    /*
        .x(function(d, i) { return x(i); })
        .y(function(d, i) { return y(d); });
        */
        .x(function(d, i) { return x(d.delta); })
        .y(function(d, i) { return y(d.score); });

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

    var yAxis = svg.append("g")
        .attr("class", "y axis")
        .call(d3.svg.axis().scale(y).orient("left"));

    var path = svg.selectAll(".scoreline")
        .data(data)
        .enter()
        .append("g")
        .attr("clip-path", "url(#clip)")
      .append("path")
        .attr("class", "line")
        .attr("d", function(d) { return line(d.values); })
        .style("stroke", function(d) { return color(d.rank); });
        ;


    function tick() {
        var args = {n_trackers:m};
        console.log('args');
        console.log(args);
        $.getJSON($SCRIPT_ROOT + '/get_data', args)
            .success(
                  function(newdata) {
                    temp.length=0;
                    temp.push(newdata); 
                    console.log('inner exit');
                    }
                  );
        //empty the data array and populate it with the new data
        console.log('past ajax. flushing old data obj');
        data.length =0;
        console.log('assigning temp2');
        var temp2 = temp.pop();
        console.log('temp2');
        console.log(temp2);
        
        var temp3 = temp2.result;//.score
        console.log('temp3');
        console.log(temp3);
        
        for(i=0; i<temp3.length; i++){
            console.log('pushing from temp to data');
            //data.push(temp3[i]);
            data[i] = temp3[i];
        };
        
        console.log('temp3');
        console.log(temp3);
        console.log('data');
        console.log(data);
    
      // push a new data point onto the back
      //data.push(random());

      // redraw the line, and slide it to the left
      /*
      path
          .attr("d", line)
      */
      
      // rescale the y-axis
    var ymax = d3.max(data, function(d) { 
        return d3.max(d.values, function(d){ return d.score; }); 
        });
    y.domain([0, ymax+1]);
    yAxis.call(d3.svg.axis().scale(y).orient("left"));
      
     var path = svg.selectAll(".scoreline");
     path.remove();
     var path = svg.selectAll(".scoreline")
        .data(data)
        .enter()
        .append("g")
        .attr("class", "scoreline")
        .attr("clip-path", "url(#clip)")
      .append("path")
        .attr("class", "line")
        .attr("d", function(d) { return line(d.values); })
        .style("stroke", function(d) { return color(d.rank); })
        ;

    console.log('end tick');
    
    write_table_d3()
    };
  
function write_table_d3() {
    d3.selectAll("tbody#url-table>tr").remove();
    var tbody = d3.select('tbody');
    var rows = tbody.selectAll("tr")
        .data(data)
        .enter()
        .append("tr")
        .attr('class', 'foobar')
        ;
        
    var cells = rows.selectAll("td")
        .data(function(row) {
            return [
            {column:'rank', value:row.rank}, 
            //{column:'score', value:row.values[0].score},
            //{column:'url', url:row.url, title:row.title}
            {column:'score', value:row.score}, 
            {column:'url', url:row.url, title:row.url}, 
            ];
            })
        .enter()
        .append("td")
        .attr('class', 'foobar2')
        .html(function(d) { 
            if(d.column == 'url'){
                return '<a href="' +d.url+ '">' +d.title+ '</a>'
            } else {
                return d.value;
            }
        })
        ;
};