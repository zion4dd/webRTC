import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# HTML page to connect to the WebSocket
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <form id="form">
            <input type="text" id="message" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id="messages"></ul>
        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");
            const form = document.getElementById('form');
            const input = document.getElementById('message');
            const messages = document.getElementById('messages');

            ws.onmessage = function(event) {
                const li = document.createElement('li');
                li.textContent = event.data;
                messages.appendChild(li);
            };

            form.onsubmit = function(event) {
                event.preventDefault();
                ws.send(input.value);
                input.value = '';
            };
        </script>
    </body>
</html>
"""

users = {}


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id):
    await websocket.accept()
    users[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            print(data)
            recipient_id = data.get("recipient_id", None)
            msg = data.get("msg", "")

            if recipient_id in users:
                await users[recipient_id].send_text(f"{user_id}: {msg}")
            else:
                await websocket.send_text(f"Unknown recipient: {recipient_id}")

    except WebSocketDisconnect:
        print(f"user {user_id} disconnected")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
