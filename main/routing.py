from channels.routing import route
from . import consumers
from . import batch


channel_routing = [
    route('send-invite', batch.send_invite),
]


chat_routing = [
    route('websocket.connect', consumers.ws_connect),
    route('websocket.receive', consumers.ws_receive),
    route('websocket.disconnect', consumers.ws_disconnect),
]


default_routing = channel_routing + chat_routing