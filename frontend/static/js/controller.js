    
    var n = 1000; 
    var data=[[0][0]];
    var temp=[];

    var random = d3.random.normal(0, .2);
    //var data = d3.range(n).map(random);

    var margin = {top: 20, right: 20, bottom: 20, left: 40},
        width = 960 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

    var x = d3.scale.linear()
        .domain([0, n - 1])
        .range([0, width]);

    var y = d3.scale.linear()
        .domain([-1, 100])
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

    var path = svg.selectAll(".scoreline")
        .data(data)
        .enter()
        .append("g")
        .attr("clip-path", "url(#clip)")
      .append("path")
        .attr("class", "line")
        .attr("d", line);


    function tick() {
        
        $.getJSON($SCRIPT_ROOT + '/get_data', {},  
                  function(newdata) {
                    temp.length=0;
                    console.log('temp flushed');
                    console.log(temp);
                    console.log('newdata');
                    console.log(newdata);
                    console.log('wtf');
                    temp.push(newdata); 
                    console.log('inner temp');
                    console.log(temp);
                    console.log('inner exit');
                    }
                  );
        //empty the data array and populate it with the new data
        data.length =0;
        var temp2 = temp.pop();
        console.log('temp2');
        console.log(temp2);
        
        var temp3 = temp2.result//.score
        console.log('temp3');
        console.log(temp3);
        
        for(i=0; i<temp3.length; i++){
            console.log('pushing from temp to data');
            //data.push(temp3[i]);
            data[i] = temp3[i].score;
        };
        
        console.log('temp');
        console.log(temp);
        console.log('data');
        console.log(data);
    
      // push a new data point onto the back
      //data.push(random());

      // redraw the line, and slide it to the left
      /*
      path
          .attr("d", line)
      */
     var path = svg.selectAll(".scoreline");
     path.remove();
     var path = svg.selectAll(".scoreline")
        .data(data)
        .enter()
        .append("g")
        .attr("clip-path", "url(#clip)")
      .append("path")
        .attr("class", "line")
        .attr("d", line);
      
          ;

      // pop the old data point off the front
      //data.shift();
    console.log('end tick');
    };
    
//tick();
setInterval('tick()', 100); // tick every tenth of a second.
