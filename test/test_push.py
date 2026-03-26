import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print('✅ 已连接，订阅 risk...')
    sio.emit('subscribe', {'topics': ['risk']})

@sio.on('subscribed')
def on_subscribed(data):
    print(f'SUBSCRIBED: {data}')
    time.sleep(2)
    sio.emit('push_from_external', {
        'topic': 'risk',
        'data': {
            'level': '警告',
            'title': '测试推送',
            'content': '测试消息内容'
        }
    })

@sio.on('risk')
def on_risk(data):
    print(f'RECEIVED_RISK: {data}')

@sio.on('push_ack')
def on_push_ack(data):
    print(f'PUSH_ACK: {data}')

try:
    sio.connect('http://192.168.66.186:8766', transports=['polling'], wait_timeout=10)
    sio.wait()
except Exception as e:
    print(f'ERROR: {e}')
