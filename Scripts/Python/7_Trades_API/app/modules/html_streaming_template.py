html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Fast_Trades WebSocket</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    </head>
    <body>
        <h1>WebSocket Fast Trades</h1>
        <h2>IFT API</h2>
        <div style="width:70%">
            <div>
                <canvas id="canvas" height="450" width="800"></canvas>
            </div>
        </div>
        
        <script>
        var options = {
            responsive: true,
            scaleShowGridLines: false,
            scaleLineColor: "rgba(172, 20, 90,.1)",
        }
        var lineChartData = {
            labels: [],
            datasets: [{
                label: "Trades Data",
                backgroundColor: 'rgb(172, 20, 90)',
                borderColor: 'rgb(172, 20, 90)',
                pointStrokeColor: "#ac145a",
                pointHighlightFill: "#ac145a",
                pointHighlightStroke: "rgba(172, 20, 90, 1)",
                data: []
            }],
            options: options
        }

        
        var ctx = document.getElementById("canvas");
        window.myLine = new Chart(ctx, {type: "line", data: lineChartData});
        </script>
        
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/api/streamtrades/analytics/");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                const eventData = jQuery.parseJSON(event.data)                           
                var content = document.createTextNode(eventData.Trader + ' has traded ' + eventData.Quantity + ' in ' + eventData.ISIN)
                message.appendChild(content)
                messages.appendChild(message)
                
                if(lineChartData.datasets[0].data.length > 0){
                    var cumulTrades = lineChartData.datasets[0].data[lineChartData.datasets[0].data.length - 1] + eventData.Quantity;
                    lineChartData.datasets[0].data.push(cumulTrades);
                } else {
                    lineChartData.datasets[0].data.push(eventData.Quantity);
                }                
                lineChartData.labels.push(eventData.DateTime)
                console.log(lineChartData.datasets[0].data)
                window.myLine.update();
            };
        </script>
    </body>
</html>
"""
