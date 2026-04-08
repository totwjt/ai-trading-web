import argparse
import socketio


def main() -> None:
    parser = argparse.ArgumentParser(description="Terminal order receiver test client")
    parser.add_argument("--url", default="http://127.0.0.1:8766", help="Socket.IO server URL")
    parser.add_argument("--user-id", default="u_1001", help="User ID")
    parser.add_argument("--terminal-id", default="terminal-test-order-1", help="Terminal ID")
    parser.add_argument("--mac", default="AA:BB:CC:DD:EE:FF", help="Terminal MAC address")
    parser.add_argument("--terminal-name", default="Order Receiver", help="Terminal display name")
    parser.add_argument("--account-name", default="receiver_demo", help="Terminal account name")
    args = parser.parse_args()

    sio = socketio.Client(logger=False, engineio_logger=False, reconnection=True)

    @sio.event
    def connect():
        print("[receiver] connected")
        sio.emit(
            "terminal_register",
            {
                "userId": args.user_id,
                "terminalId": args.terminal_id,
                "macAddress": args.mac,
                "terminalName": args.terminal_name,
                "accountName": args.account_name,
                "status": "online",
            },
        )

    @sio.event
    def disconnect():
        print("[receiver] disconnected")

    @sio.on("terminal_error")
    def on_terminal_error(data):
        print("[receiver] terminal_error:", data)

    @sio.on("terminal_registered")
    def on_registered(msg):
        print("[receiver] terminal_registered:", msg)
        order_topic = msg.get("orderTopic")
        if not order_topic:
            print("[receiver] no orderTopic in terminal_registered")
            return

        @sio.on(order_topic)
        def on_order(order_msg):
            print("[receiver] order message:", order_msg)

        print(f"[receiver] listening topic: {order_topic}")

    sio.connect(args.url, transports=["websocket", "polling"])
    sio.wait()


if __name__ == "__main__":
    main()

