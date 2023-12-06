
const http = require('http')

var lastWattage = null;
// {
//  "date": dateTime,
//  "wattage": int 
//}
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
        lastWattage=body
        response.writeHead(200, {'Content-Type': 'text/html'})
        response.end('post received')
        })
    }
});

const datasend = http.createServer(function(request, response) {
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
      response.writeHead(200, {'Content-Type': 'application/json'})
      response.end(lastWattage)
    })
  }
})

const port = 3000
const port2 = 4000
const host = '127.0.0.1'
datarecieve.listen(port, host)
console.log(`Listening for data at http://${host}:${port}`)
server.listen(port2, host)
console.log(`Listening for request at http://${host}:${port2}`)