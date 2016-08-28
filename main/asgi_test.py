import os
import channels.asgi


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "channels_test.settings_prod")

channel_layer = channels.asgi.get_channel_layer('test')