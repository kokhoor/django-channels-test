import datetime
import re
import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from django.conf import settings
from django.utils.dateformat import format

from .models import Room

log = logging.getLogger('chat')


class ChatConsumer(WebsocketConsumer):
    channel_layer_alias = settings.CHAT_CHANNEL_LAYER

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat-%s' % self.room_name    
        log.debug('room name: %s group: ', self.room_group_name)
        try:
            label = self.room_name
            room = Room.objects.get(label=label)
        except ValueError:
            log.debug('invalid room name=%s', self.room_name)
            return
        except Room.DoesNotExist:
            log.debug('room does not exist %s', self.room_name)
            return

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        handle = text_data_json['handle']
        message = text_data_json['message']

        # Look up the room from the channel session, bailing if it doesn't exist
        try:
            label = self.room_name
            room = Room.objects.get(label=label)
        except KeyError:
            log.debug('no room in channel_session')
            return
        except Room.DoesNotExist:
            log.debug('received message, but room does not exist label=%s', label)
            return

        if not handle or not message:
            log.debug("ws message unexpected format handle=%s message=%s", data, message)
            return

        data = {
            "handle": handle,
            "message": message,
            "room": room,
            "timestamp": datetime.datetime.now()
        }
        log.debug('chat message room=%s handle=%s message=%s', 
            room.label, handle, message)
        m = room.messages.create(**data)

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'data': {
                    "handle": handle,
                    "message": message,
                    "timestamp": format(data['timestamp'], settings.DATETIME_FORMAT)
                }
            }
        )


    def chat_message(self, event):
        message = event['data']

        # Send message to WebSocket
        self.send(text_data=json.dumps(message))

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )