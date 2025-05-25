import datetime
import re
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer # Changed import
from channels.db import database_sync_to_async
from django.conf import settings
from django.utils.dateformat import format
# from django.utils import timezone

from .models import Room, Message

log = logging.getLogger('chat')


class ChatConsumer(AsyncWebsocketConsumer): # Changed base class
    channel_layer_alias = settings.CHAT_CHANNEL_LAYER

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat-%s' % self.room_name
        log.debug('room name: %s group: %s', self.room_name, self.room_group_name)
        
        try:
            room_label = self.room_name
            # ORM calls are sync, need database_sync_to_async
            self.room_instance = await database_sync_to_async(Room.objects.get)(label=room_label)
        except Room.DoesNotExist:
            log.debug('room does not exist %s', self.room_name)
            self.room_instance = None
            await self.close() # Use await for async close
            return

        # Channel layer methods are async with AsyncWebsocketConsumer
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept() # Use await for async accept


    async def disconnect(self, close_code): # Now async
        if hasattr(self, 'room_group_name') and hasattr(self, 'channel_name'):
            # Channel layer methods are async
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError as e:
            log.debug(f"Failed to decode JSON: {text_data} - error: {e}")
            await self.close()
            return
        
        handle = text_data_json.get('handle')
        message_text = text_data_json.get('message')

        if not handle or not message_text:
            log.debug(f"Missing handle or message: handle='{handle}', message='{message_text}'")
            await self.send(text_data=json.dumps({'error': 'Handle and message are required.'}))
            await self.close() # Close connection due to bad data
            return

        if not hasattr(self, 'room_instance') or self.room_instance is None:
            log.debug('receive called but room_instance is not set or None.')
            # Attempt to fetch room again if not set (should ideally be handled by connect logic)
            try:
                room_label = self.scope['url_route']['kwargs']['room_name']
                room = await database_sync_to_async(Room.objects.get)(label=room_label)
            except Room.DoesNotExist:
                log.debug('received message, but room does not exist (refetch) label=%s', self.scope['url_route']['kwargs'].get('room_name'))
                await self.close() # Close if room still not found
                return
        else:
            room = self.room_instance
        
        current_timestamp = datetime.datetime.now()
        
        # ORM calls are sync, need database_sync_to_async
        # room.messages.create is a synchronous method.
        log.debug(f"Attempting to create message in room: {room.label} (ID: {room.id}), "
                  f"handle: {handle}, message: {message_text}, timestamp: {current_timestamp}")
        create_message_for_room = database_sync_to_async(room.messages.create)
        new_message = await create_message_for_room(
            handle=handle,
            message=message_text,
            timestamp=current_timestamp
        )
        if new_message and hasattr(new_message, 'id'):
            log.debug(f"Message supposedly created with ID: {new_message.id}, Handle: {new_message.handle}")
        else:
            log.debug("Message creation call completed, but new_message object is None or has no ID.")
        log.debug('chat message room=%s handle=%s message=%s timestamp=%s', # This is the original log line, can be kept or removed
                  room.label, handle, message_text, current_timestamp)

        # Channel layer methods are async
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'data': {
                    "handle": handle,
                    "message": message_text,
                    "timestamp": format(current_timestamp, settings.DATETIME_FORMAT)
                }
            }
        )

    async def chat_message(self, event): # Now async
        message_data = event['data']
        # Corrected to use self.send with json.dumps for AsyncWebsocketConsumer
        await self.send(text_data=json.dumps(message_data))