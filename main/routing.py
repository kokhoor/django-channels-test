from channels.auth import AuthMiddlewareStack
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter

from django.urls import path

from . import batch, consumers


application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    "websocket": AuthMiddlewareStack(
        URLRouter([
        	path('chat/<str:room_name>', consumers.ChatConsumer),
        ])
    ),
    "channel": ChannelNameRouter({
        "send-email": batch.SendEmailConsumer,
    }),
})
"""
from channels.routing import route


channel_routing = [
    route('send-invite', batch.send_invite),
]


chat_routing = [
    route('websocket.connect', consumers.ws_connect),
    route('websocket.receive', consumers.ws_receive),
    route('websocket.disconnect', consumers.ws_disconnect),
]


default_routing = channel_routing + chat_routing
"""