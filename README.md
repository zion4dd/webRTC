```
function db(command) {
        var socket = new WebSocket("ws://localhost:9999");

        socket.onopen = function() {};

        socket.onclose = function(event) {};

        socket.addEventListener('open', function (event) {
            socket.send(command);
        });

        socket.onmessage = function(event) {
           console.log(event.data)
        };

        socket.onerror = function(error) {
            console.log("Ошибка " + error.message);
        };
    }
```