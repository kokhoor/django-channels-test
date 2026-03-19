import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "channels_test.settings_sharding")

django_asgi_app = get_asgi_application()

# Import routing and batch AFTER get_asgi_application()
import main.routing
import main.batch

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            main.routing.websocket_urlpatterns
        )
    ),
    "channel": ChannelNameRouter({
        "send-email": main.batch.SendEmailConsumer.as_asgi(),
    }),
})
