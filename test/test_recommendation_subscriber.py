#!/usr/bin/env python3
"""
局域网 recommendation topic 订阅验证脚本

输出步骤：
1) 连接状态
2) 订阅确认
3) 心跳发送与回包
4) topic 消息接收

用法示例：
  backend/.venv/bin/python test/test_recommendation_subscriber.py \
    --url http://192.168.66.186:8766 \
    --topic recommendation \
    --heartbeat-interval 10 \
    --duration 0

参数说明：
  --duration 0 代表一直运行，直到 Ctrl+C
"""

from __future__ import annotations

import argparse
import threading
import time
from datetime import datetime
from typing import Any, Dict

import socketio


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(step: str, detail: str) -> None:
    print(f"[{ts()}] [{step}] {detail}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Subscribe recommendation topic and print every step.")
    parser.add_argument("--url", default="http://127.0.0.1:8766", help="Socket.IO server URL")
    parser.add_argument("--topic", default="recommendation", help="Topic to subscribe")
    parser.add_argument("--path", default="/socket.io", help="Socket.IO path")
    parser.add_argument("--heartbeat-interval", type=int, default=10, help="Heartbeat emit interval in seconds")
    parser.add_argument("--duration", type=int, default=0, help="Run seconds. 0 means forever")
    args = parser.parse_args()

    sio = socketio.Client(logger=False, engineio_logger=False, reconnection=True)
    stop_event = threading.Event()
    heartbeat_count = 0
    recommendation_count = 0

    @sio.event
    def connect() -> None:
        log("CONNECT", f"connected sid={sio.sid}")
        payload: Dict[str, Any] = {"topics": [args.topic]}
        sio.emit("subscribe", payload)
        log("SUBSCRIBE", f"emit subscribe payload={payload}")

    @sio.event
    def disconnect() -> None:
        log("DISCONNECT", "connection closed")

    @sio.event
    def connect_error(data: Any) -> None:
        log("ERROR", f"connect_error data={data}")

    @sio.on("subscribed")
    def on_subscribed(data: Any) -> None:
        log("SUBSCRIBED", f"server ack={data}")

    @sio.on("unsubscribed")
    def on_unsubscribed(data: Any) -> None:
        log("UNSUBSCRIBED", f"server ack={data}")

    @sio.on("heartbeat")
    def on_heartbeat(data: Any) -> None:
        log("HEARTBEAT_ACK", f"payload={data}")

    @sio.on("recommendation")
    def on_recommendation(data: Any) -> None:
        nonlocal recommendation_count
        recommendation_count += 1
        preview = str(data)
        if len(preview) > 240:
            preview = preview[:240] + "...(truncated)"
        log("TOPIC_MESSAGE", f"topic={args.topic} count={recommendation_count} payload={preview}")

    @sio.on("terminal_error")
    def on_terminal_error(data: Any) -> None:
        log("TERMINAL_ERROR", f"payload={data}")

    @sio.on("push_ack")
    def on_push_ack(data: Any) -> None:
        log("PUSH_ACK", f"payload={data}")

    def heartbeat_loop() -> None:
        nonlocal heartbeat_count
        while not stop_event.is_set():
            if sio.connected:
                heartbeat_count += 1
                sio.emit("heartbeat")
                log("HEARTBEAT", f"emit heartbeat #{heartbeat_count}")
            stop_event.wait(max(args.heartbeat_interval, 1))

    log("START", f"url={args.url} path={args.path} topic={args.topic}")
    sio.connect(args.url, socketio_path=args.path, transports=["websocket", "polling"])
    worker = threading.Thread(target=heartbeat_loop, daemon=True)
    worker.start()

    start = time.time()
    try:
        while True:
            if args.duration > 0 and (time.time() - start) >= args.duration:
                log("STOP", f"duration reached ({args.duration}s)")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        log("STOP", "KeyboardInterrupt")
    finally:
        stop_event.set()
        if sio.connected:
            sio.emit("unsubscribe", {"topics": [args.topic]})
            log("UNSUBSCRIBE", f"emit unsubscribe topic={args.topic}")
            time.sleep(0.2)
            sio.disconnect()
        log(
            "SUMMARY",
            f"heartbeat_sent={heartbeat_count} recommendation_received={recommendation_count}",
        )


if __name__ == "__main__":
    main()

