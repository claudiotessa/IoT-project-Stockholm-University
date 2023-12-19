
const http = require('http')

var lastWattage =
[{
  "id": 1,
  "date": null,
  "wattage": 1.2,
}, {
  "id": 2,
  "date": null,
  "wattage": 1.4,
}]
const datarecieve = http.createServer(function(request, response) {
  console.dir(request.param)

    if (request.method == 'POST') {
        console.log('POST')
        var body = ''
        request.on('data', function(data) {
        body += data
        console.log('Partial body: ' + body)
        })
        request.on('end', function() {
        console.log('Body: ' + body)
        if(typeof body === 'string' || body instanceof String)
          body=JSON.parse(body)

        lastWattage=body
        
        response.writeHead(200, {'Content-Type': 'text/html'})
        response.end('post received')
        })
    }
});

const datasend = http.createServer(function(request, response) {
  console.dir(request.param)

  if (request.method == 'POST') {
    console.log('POST');
    var body = '';
    request.on('data', function(data) {
      body += data;
      console.log('Partial body: ' + body);
    });
    request.on('end', function() {
      console.log('Body: ' + body);
      console.log(lastWattage);
      for(var i=0; i<lastWattage.length; i++) lastWattage[i]["date"]=new Date(new Date().getTime());
      response.writeHead(200, {'Content-Type': 'application/json'});
      response.end(JSON.stringify(lastWattage));
    })
  }
})

const port = 3000
const port2 = 4000
const host = '0.0.0.0'
datarecieve.listen(port, host)
console.log(`Listening for data at http://${host}:${port}`)
datasend.listen(port2, host)
console.log(`Listening for request at http://${host}:${port2}`)