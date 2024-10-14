# ws://localhost:8000/ws?user_id=1
# uvicorn app:app --reload

import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles
from redis import Redis
from starlette.responses import FileResponse

app = FastAPI()
# app.mount("/", StaticFiles(directory="static", html=True), name="static")

redis = Redis(host="localhost", port=6379, db=0)

user_list = {}


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
    for user, ws in user_list.items():
        await ws.send_text(msg)


async def refresh_users():
    users_str = "@users:" + ";".join(
        [str(ws.query_params) for ws in user_list.values()]
    )
    await broadcast(users_str)


@app.get("/")
async def get():
    return FileResponse("index.html")
    # return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id=1):
    print(websocket.query_params, websocket.scope["client"])

    await websocket.accept()
    # Запуск фоновой задачи для отправки пинг-сообщений
    asyncio.create_task(ping(websocket))

    user_list[user_id] = websocket
    await refresh_users()

    try:
        while True:
            data = await websocket.receive_text()
            print(data)
            if data.startswith("@"):
                recipient_id, msg = data[1:].split(":", 1)
            else:
                recipient_id = None
                msg = data

            if recipient_id in user_list:
                await user_list[recipient_id].send_text(f"{user_id}: {msg}")
            else:
                await broadcast(msg)
                # await websocket.send_text(f"Unknown recipient: {recipient_id}")

    except WebSocketDisconnect:
        del user_list[user_id]
        await refresh_users()
        print(f"user {user_id} disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
