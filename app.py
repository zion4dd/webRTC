# uvicorn app:app --reload  # ws://localhost:8000/ws/111

import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


class ConnectionManager:
    def __init__(self) -> None:
        self.client_list: dict[str, WebSocket] = {}

    @staticmethod
    async def ping(websocket: WebSocket):
        while True:
            await asyncio.sleep(60)  # Интервал пинга 60 секунд
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
        self, client_id: str, websocket: WebSocket, ping: bool = False
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

    async def disconnect(self, client_id: str):
        self.client_list.pop(client_id, None)
        logging.info(f"client {client_id} disconnected")
        await self._refresh_clients()

    async def send_pm(self, client_id: str, msg: str = None, json: str = None):
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
    return FileResponse("static/index.html")


@app.websocket("/ws/{client_id}")
async def call_endpoint(websocket: WebSocket, client_id: str):
    await manager.add_client(client_id=client_id, websocket=websocket)
    target = None
    try:
        while True:
            data: dict = await websocket.receive_json()

            if data.get("type") == "msg":
                msg: str = data.get("msg")
                if msg.startswith("@"):
                    target, msg = msg[1:].split(":", 1)
                if target:
                    await manager.send_pm(client_id=target, msg=msg)
                else:
                    await manager.broadcast(msg=msg)

            elif data.get("type") in ("offer", "answer", "icecandidate", "bye"):
                logging.info(data.get("type"))
                await manager.send_pm(client_id=data.get("target", None), json=data)

            else:
                print("DATA", data)

    except WebSocketDisconnect:
        await manager.disconnect(client_id=client_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
