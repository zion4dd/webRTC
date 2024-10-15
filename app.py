# ws://localhost:8000/ws/111
# uvicorn app:app --reload

import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

app = FastAPI()
app.mount("/video", StaticFiles(directory="static", html=True), name="static")

# from redis import Redis
# redis = Redis(host="localhost", port=6379, db=0)


class ConnectionManager:
    def __init__(self) -> None:
        self.client_list: dict[int, WebSocket] = {}

    @staticmethod
    async def ping(websocket: WebSocket):
        while True:
            await asyncio.sleep(60)  # Интервал пинга в 60 секунд
            try:
                await websocket.send_text("ping")  # Отправка пинг-сообщения
                logging.warning("ping")
            except Exception as e:
                print(f"Ошибка при отправке пинга: {e}")
                break

    async def _refresh_clients(self):
        clients_str = "@clients: " + "; ".join(
            [str(key) for key in self.client_list.keys()]
        )
        await self.broadcast(msg=clients_str)

    async def add_client(
        self, client_id: int, websocket: WebSocket, ping: bool = False
    ):
        print(
            websocket.path_params,
            # websocket.scope["client"],
            # websocket.query_params,
        )
        await websocket.accept()
        self.client_list[client_id] = websocket
        if ping:
            asyncio.create_task(self.ping(websocket))
        await self._refresh_clients()

    async def disconnect(self, client_id: int):
        self.client_list.pop(client_id, None)
        print(f"client {client_id} disconnected")
        await self._refresh_clients()

    async def send_pm(self, client_id: int, msg: str = None, json: str = None):
        ws = self.client_list.get(client_id, None)
        if ws:
            if msg:
                await ws.send_text(msg)
            if json:
                await ws.send_json(json)

    async def broadcast(self, msg: str = None, json: str = None):
        for ws in self.client_list.values():
            if msg:
                await ws.send_text(msg)
            if json:
                await ws.send_json(json)


manager = ConnectionManager()


@app.get("/")
async def index():
    return FileResponse("index.html")
    # return HTMLResponse(html)


@app.get("/video")
async def call():
    return FileResponse("call.html")
    # return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.add_client(client_id=client_id, websocket=websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
            recipient_id = None
            msg = data
            if data.startswith("@"):
                recipient_id, msg = data[1:].split(":", 1)
            if recipient_id:
                await manager.send_pm(client_id=recipient_id, msg=msg)
            else:
                await manager.broadcast(msg=msg)
    except WebSocketDisconnect:
        await manager.disconnect(client_id=client_id)


@app.websocket("/call/{client_id}")
async def call_endpoint(websocket: WebSocket, client_id: int):
    await manager.add_client(client_id=client_id, websocket=websocket)
    recipient_id = 11 if client_id == 22 else 22
    try:
        while True:
            data: dict = await websocket.receive_json()

            if data.get("type") == "offer":
                print("OFFER", data.get("sdp", "empty string")[:50])
                await manager.send_pm(client_id=recipient_id, json=data)
                # await client_list[recipient_id].send_text(json.dumps(data))

            elif data.get("type") == "answer":
                print("ANSWER", data.get("sdp", "empty string")[:50])
                await manager.send_pm(client_id=recipient_id, json=data)
                # await client_list[recipient_id].send_text(json.dumps(data))

            elif data.get("type") == "icecandidate":
                print("ICE", data.get("candidate", "empty string"))
                await manager.send_pm(client_id=recipient_id, json=data)

            else:
                print("DATA", data)

    except WebSocketDisconnect:
        await manager.disconnect(client_id=client_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
