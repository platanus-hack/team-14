import json
import logging
import os
import time
from datetime import datetime
from typing import Any
import hashlib

import requests
import websockets
from pydantic import BaseModel
import asyncio

DEV = True

def generate_md5_hash(data):
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.md5(json_data.encode("utf-8")).hexdigest()


class Push(BaseModel):
    type: str
    source_user_iden: str
    source_device_iden: str
    client_version: int
    icon: str
    title: str
    body: str
    application_name: str
    package_name: str
    notification_id: str
    notification_tag: str

    def generate_payload(self) -> dict[str, Any]:
        result = {
            "input": {
                "notification_id": self.notification_id,
                "notification_tag": self.notification_tag,
                "package_name": self.package_name,
                "source_user_iden": self.source_user_iden,
                "title": self.title,
                "message": self.body,
                "app_name": self.application_name,
            },
            "config": {},
            "kwargs": {},
        }
        id = generate_md5_hash(result)
        result["input"]["id"] = id
        result["input"]["timestamp"] = time.time()
        return result


logging.basicConfig(
    format="%(asctime)s %(message)s",
    level=logging.CRITICAL,
)
def classify(push: Push):

    print(push.generate_payload())
    output = push.generate_payload()
    if DEV:
        path = "http://localhost:8000/classify/invoke"
    else:
        path = "https://mind-sift-app-262464751960.us-central1.run.app/classify/invoke"
    response = requests.post(
        path,
        json=output,
    )
    print("classify response", response.status_code)


async def process(msg):
    event = json.loads(msg)
    if event.get("type") == "push":
        p_json_data = event.get("push", {})
        try:
            push = Push(**p_json_data)
        except ValueError as e:
            print(e.errors())
            print("uwu")
            print(p_json_data)
            return
        print()
        print(push.model_dump())
        print()
        classify(push)


async def stream():
    KEY = os.getenv("PUSHBULLET_API_KEY")
    async for websocket in websockets.connect(
        f"wss://stream.pushbullet.com/websocket/{KEY}",
        logger=logging.getLogger("websockets"),
    ):
        try:
            async for message in websocket:
                await process(message)
        except websockets.ConnectionClosed:
            continue

# async def stream():
#     KEY = os.getenv("PUSHBULLET_API_KEY")
#     backoff = 1  # Initial backoff time in seconds
#     max_backoff = 60  # Maximum backoff time

#     while True:
#         try:
#             async for websocket in websockets.connect(
#                 f"wss://stream.pushbullet.com/websocket/{KEY}",
#                 logger=logging.getLogger("websockets"),
#             ):
#                 try:
#                     async for message in websocket:
#                         await process(message)
#                 except websockets.ConnectionClosed:
#                     print("Websocket connection closed. Reconnecting...")
#                     logging.warning("Websocket connection closed. Reconnecting...")
#                     break  # Exit inner `async for websocket` loop
#         except Exception as e:
#             logging.error(f"Connection error: {e}. Retrying in {backoff} seconds...")
#             await asyncio.sleep(backoff)
#             backoff = min(backoff * 2, max_backoff)  # Exponential backoff with a cap
#         else:
#             backoff = 1  # Reset backoff after a successful connection
