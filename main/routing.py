from channels.auth import AuthMiddlewareStack
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter

from django.urls import path

from . import batch, consumers


websocket_urlpatterns = [
    path('chat/<str:room_name>', consumers.ChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
    "channel": ChannelNameRouter({
        "send-email": batch.SendEmailConsumer.as_asgi(),
    }),
})