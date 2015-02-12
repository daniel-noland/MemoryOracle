var ws = new WebSocket("ws://localhost:8765/");
ws.onopen = function() {
   ws.send("hello, world");
};

ws.onmessage = function(evt) {
   alert(evt.data);
   $( "#title" ).text(evt.data);
}
