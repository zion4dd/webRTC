# ws://localhost:8000/ws/111
# uvicorn app:app --reload

import asyncio
import logging
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles
from redis import Redis
from starlette.responses import FileResponse

app = FastAPI()
# app.mount("/", StaticFiles(directory="static", html=True), name="static")

redis = Redis(host="localhost", port=6379, db=0)

client_list = {}


async def ping(websocket: WebSocket):
    while True:
        await asyncio.sleep(60)  # Интервал пинга в 60 секунд
        try:
            await websocket.send_text("ping")  # Отправка пинг-сообщения
            logging.warning("ping")
        except Exception as e:
            print(f"Ошибка при отправке пинга: {e}")
            break


async def broadcast(msg):
    for client, ws in client_list.items():
        await ws.send_text(msg)


async def refresh_clients():
    clients_str = "@clients:" + ";".join([str(key) for key in client_list.keys()])
    await broadcast(clients_str)


@app.get("/")
async def index():
    return FileResponse("index.html")
    # return HTMLResponse(html)


@app.get("/call/")
async def call():
    return FileResponse("call.html")
    # return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    print(websocket.path_params, websocket.scope["client"])
    # print(websocket.query_params)

    await websocket.accept()
    # Запуск фоновой задачи для отправки пинг-сообщений
    asyncio.create_task(ping(websocket))

    client_list[client_id] = websocket
    await refresh_clients()

    try:
        while True:
            data = await websocket.receive_text()
            print(data)
            if data.startswith("@"):
                recipient_id, msg = data[1:].split(":", 1)
            else:
                recipient_id = None
                msg = data

            if recipient_id in client_list:
                await client_list[recipient_id].send_text(f"{client_id}: {msg}")
            else:
                await broadcast(msg)
                # await websocket.send_text(f"Unknown recipient: {recipient_id}")

    except WebSocketDisconnect:
        del client_list[client_id]
        await refresh_clients()
        print(f"client {client_id} disconnected")


@app.websocket("/call/{client_id}")
async def call_endpoint(websocket: WebSocket, client_id: int):
    print(websocket.path_params, websocket.scope["client"])
    # print(websocket.query_params)

    await websocket.accept()
    # Запуск фоновой задачи для отправки пинг-сообщений
    # asyncio.create_task(ping(websocket))

    client_list[client_id] = websocket
    await refresh_clients()

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "offer":
                print("OFFER", data.get("sdp", "empty string")[:100])
                await client_list[11].send_text(json.dumps(data))

            if data.get("type") == "answer":
                print("ANSWER", data.get("sdp", "empty string")[:100])
                await client_list[22].send_text(json.dumps(data))
                 
            # if data.startswith("@"):
            #     recipient_id, msg = data[1:].split(":", 1)
            # else:
            #     recipient_id = None
            #     msg = data

            # if recipient_id in client_list:
            #     await client_list[recipient_id].send_text(f"{client_id}: {msg}")
            # else:
            #     await broadcast(msg)
            # await websocket.send_text(f"Unknown recipient: {recipient_id}")

    except WebSocketDisconnect:
        del client_list[client_id]
        await refresh_clients()
        print(f"client {client_id} disconnected")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
