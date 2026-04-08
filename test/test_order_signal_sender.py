import argparse
import socketio


def main() -> None:
    parser = argparse.ArgumentParser(description="Signal platform order sender test client")
    parser.add_argument("--url", default="http://127.0.0.1:8766", help="Socket.IO server URL")
    parser.add_argument("--user-id", default="u_1001", help="User ID")
    parser.add_argument("--stock-code", default="600519", help="Stock code")
    parser.add_argument("--price", type=float, default=1723.4, help="Order price")
    parser.add_argument("--quantity", type=int, default=100, help="Order quantity")
    parser.add_argument("--position-level", type=int, default=2, choices=[1, 2, 3, 4], help="Position level")
    args = parser.parse_args()

    sio = socketio.Client(logger=False, engineio_logger=False, reconnection=False)

    @sio.event
    def connect():
        print("[sender] connected")
        sio.emit(
            "push_order",
            {
                "userId": args.user_id,
                "eventType": "order.create",
                "source": "signal_platform",
                "data": {
                    "stock_code": args.stock_code,
                    "price": args.price,
                    "quantity": args.quantity,
                    "position_level": args.position_level,
                },
            },
        )

    @sio.on("push_ack")
    def on_push_ack(msg):
        print("[sender] push_ack:", msg)
        sio.disconnect()

    @sio.on("terminal_error")
    def on_terminal_error(data):
        print("[sender] terminal_error:", data)
        sio.disconnect()

    @sio.event
    def connect_error(err):
        print("[sender] connect_error:", err)

    sio.connect(args.url, transports=["websocket", "polling"])
    sio.wait()


if __name__ == "__main__":
    main()

