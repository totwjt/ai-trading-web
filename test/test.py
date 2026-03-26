import socketio
import logging

logging.basicConfig(level=logging.DEBUG)
sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print("✅ 连接成功！")
    sio.emit('subscribe', {'topics': ['risk']})

@sio.on('risk')
def on_risk(data):
    print(f"📦 收到风控警报: {data}")

@sio.event
def connect_error(data):
    print(f"❌ 连接失败原因: {data}")

def run():
    try:
        sio.connect(
            'http://192.168.66.186:8766',
            transports=['polling', 'websocket'],
            wait_timeout=10
        )
        sio.wait()
    except Exception as e:
        print(f"🔥 捕获异常: {e}")

if __name__ == '__main__':
    run()