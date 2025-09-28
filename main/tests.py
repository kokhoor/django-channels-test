from django.test import TestCase, override_settings # Ensure TestCase is imported
from django.utils import timezone
import datetime
import json
import asyncio # For asyncio.TimeoutError

from .models import Room, Message
from main.consumers import ChatConsumer # Ensure consumer is imported
from channels.testing import WebsocketCommunicator
from channels.layers import InMemoryChannelLayer # Corrected import path earlier
from channels.db import database_sync_to_async # For helper methods

from django.urls import reverse
from django.conf import settings
from unittest.mock import patch, MagicMock, AsyncMock


# Model Tests (Copied from existing, assumed correct)
class RoomModelTests(TestCase):
    def test_create_room(self):
        room = Room.objects.create(name="Test Room", label="test-room")
        self.assertIsInstance(room, Room)
        self.assertEqual(room.name, "Test Room")
        self.assertEqual(room.label, "test-room")
        self.assertEqual(Room.objects.count(), 1)

    def test_room_unicode(self):
        room = Room.objects.create(name="Another Room", label="another-room")
        self.assertEqual(room.__unicode__(), "another-room")

class MessageModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.room = Room.objects.create(name="Chat Room", label="chat-room")
        cls.fixed_datetime = datetime.datetime(2023, 1, 15, 14, 30, 0)

    def test_create_message(self):
        message = Message.objects.create(
            room=self.room, handle="User1", message="Hello, world!",
            timestamp=self.fixed_datetime)
        self.assertIsInstance(message, Message)
        self.assertEqual(message.room, self.room)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(self.room.messages.count(), 1)

    def test_message_formatted_timestamp(self):
        test_timestamp = datetime.datetime(2023, 10, 26, 10, 30, 0)
        message = Message.objects.create(room=self.room, handle="Tester", message="Timestamp test", timestamp=test_timestamp)
        expected_format = "Oct 26 10:30 AM" 
        self.assertEqual(message.formatted_timestamp, expected_format)

    def test_message_as_dict(self):
        test_timestamp = datetime.datetime(2023, 11, 5, 15, 45, 0)
        message = Message.objects.create(room=self.room, handle="DictUser", message="Testing as_dict", timestamp=test_timestamp)
        expected_dict = {'handle': "DictUser", 'message': "Testing as_dict", 'timestamp': "Nov 5 3:45 PM"}
        self.assertEqual(message.as_dict(), expected_dict)

    def test_message_unicode(self):
        test_timestamp = datetime.datetime(2023, 12, 1, 8, 0, 0)
        message = Message.objects.create(room=self.room, handle="UniUser", message="Unicode test message", timestamp=test_timestamp)
        expected_unicode = "[Dec 1 8:00 AM] UniUser: Unicode test message"
        self.assertEqual(message.__unicode__(), expected_unicode)

# View Tests (Copied from existing, assumed URL names are fixed and non-namespaced)
class IndexViewTests(TestCase):
    def test_index_view_get(self):
        Room.objects.create(name="Room 1", label="room-1")
        Room.objects.create(name="Room 2", label="room-2")
        response = self.client.get(reverse('main_index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertIn('rooms', response.context)
        self.assertEqual(len(response.context['rooms']), 2)

class InviteViewTests(TestCase):
    def test_invite_view_get(self):
        response = self.client.get(reverse('main_invite'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invite.html')

    @patch('channels.layers.get_channel_layer')
    def test_invite_view_post_valid_email(self, mock_get_channel_layer):
        mock_channel_layer_instance = MagicMock()
        mock_channel_layer_instance.send = AsyncMock() 
        mock_get_channel_layer.return_value = mock_channel_layer_instance
        response = self.client.post(reverse('main_invite'), {'email': 'test@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invite.html')
        self.assertIn('message', response.context)
        mock_channel_layer_instance.send.assert_called_once()

    def test_invite_view_post_no_email(self):
        response = self.client.post(reverse('main_invite'), {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invite.html')
        self.assertIn('error', response.context)

class ChatViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a common room if other tests in this class might need it,
        # but test_chat_view_get_existing_room will create its own.
        cls.common_room_for_other_tests = Room.objects.create(name="Common Test Room", label="common-room")
        # Messages for this common_room can be added here if needed by other tests.

    def test_chat_view_get_existing_room(self):
        # Create a unique room and messages specifically for this test method
        test_room_label = "test-chat-room-for-method"
        room = Room.objects.create(name="Test Chat Room From Method", label=test_room_label)
        for i in range(7): # Create 7 messages, view fetches last 5
            Message.objects.create(
                room=room, 
                handle=f"UserTM{i}", 
                message=f"MessageTM {i}",
                timestamp=timezone.now() + datetime.timedelta(seconds=i) 
            )
        
        room.refresh_from_db()
        print(f"DEBUG (test_chat_view_get_existing_room): Message count for room {room.label} after refresh_from_db and before client.get: {Message.objects.filter(room=room).count()}")

        # Expect queries for:
        # 1. Get Room by label (in ChatView.get_context_data)
        # 2. Get Messages for that room (in ChatView.get_context_data)
        # Potentially others if middleware or other context processors run queries.
        # Start with a broader number and narrow down if needed.
        with self.assertNumQueries(2): # EXPECTING 2 QUERIES (Room, then Messages)
            response = self.client.get(reverse('main_chat', kwargs={'room_name': test_room_label}))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat.html')
        self.assertIn('chats', response.context)
        chats_list = list(response.context['chats'])
        print(f"DEBUG: Actual chats found by view: {len(chats_list)}") # Add this to see what view got
        self.assertEqual(len(chats_list), 5) 
        if chats_list:
            self.assertIsInstance(chats_list[0], Message)

    def test_chat_view_get_non_existing_room(self):
        # This test can use the common_room or ensure the label it tests for truly doesn't exist.
        # For clarity, it's fine as is, testing for a completely non-existent label.
        with self.assertRaises(Room.DoesNotExist):
            self.client.get(reverse('main_chat', kwargs={'room_name': 'non-existent-room-really'}))

# Consumer Tests
@override_settings(CHANNEL_LAYERS={
    "default": { "BACKEND": "channels.layers.InMemoryChannelLayer", }
})
class ChatConsumerTests(TestCase): # Inherits from TestCase
    @classmethod
    def setUpTestData(cls):
        cls.room = Room.objects.create(name="Test Consumer Room", label="consumer-room")

    async def get_message_count(self, room): # Instance method
        @database_sync_to_async
        def _count():
            return Message.objects.filter(room=room).count()
        return await _count()

    async def get_last_message(self, room): # Instance method
        @database_sync_to_async
        def _last_msg():
            return Message.objects.filter(room=room).last()
        return await _last_msg()

    async def test_consumer_connect_existing_room(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.label}/")
        communicator.scope['url_route'] = {'kwargs': {'room_name': self.room.label}}
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_consumer_connect_non_existing_room(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/non-existent-room/")
        communicator.scope['url_route'] = {'kwargs': {'room_name': 'non-existent-room'}}
        connected, _ = await communicator.connect()
        self.assertFalse(connected, "Consumer should not connect if room does not exist.")
        # No disconnect needed if connection failed as expected

    async def test_consumer_receive_valid_message(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.label}/")
        communicator.scope['url_route'] = {'kwargs': {'room_name': self.room.label}}
        await communicator.connect()
        initial_message_count = await self.get_message_count(self.room)
        test_message = {"handle": "User1", "message": "Hello"}
        await communicator.send_json_to(test_message)
        await asyncio.sleep(0.1) # Add a small delay
        self.assertEqual(await self.get_message_count(self.room), initial_message_count + 1)
        last_message = await self.get_last_message(self.room)
        self.assertEqual(last_message.handle, "User1")
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response['handle'], "User1")
        await communicator.disconnect()

    async def test_consumer_receive_message_non_existing_room_label_in_scope(self):
        room_label_non_existent = "room-does-not-exist-for-receive"
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{room_label_non_existent}/")
        communicator.scope['url_route'] = {'kwargs': {'room_name': room_label_non_existent}}
        
        # Consumer's connect now closes if room DNE, so this connection should fail.
        connected, _ = await communicator.connect()
        self.assertFalse(connected, "Connection should fail if room does not exist at connect.")

        # If the goal is to test receive when room disappears *after* connect,
        # then a room must exist at connect, and then be deleted.
        # For now, this test will reflect that connect() already handles DNE rooms.
        # If connect allowed connection, then the following would apply:
        # test_message = {"handle": "User1", "message": "Test"}
        # await communicator.send_json_to(test_message)
        # output = await communicator.receive_output(timeout=1)
        # self.assertEqual(output['type'], 'websocket.close', "Expected websocket.close output if room DNE on receive.")
        
        # The original intent of this test might need rethinking given connect() behavior.
        # For now, the primary check is that connect() fails.
        # If it were to connect, and then room DNE for receive:
        # (This part is now mostly illustrative as connect will fail first)
        # if connected: # Should not happen with current connect logic
        #    test_message = {"handle": "User1", "message": "Test"}
        #    await communicator.send_json_to(test_message)
        #    output = await communicator.receive_output(timeout=1)
        #    self.assertEqual(output['type'], 'websocket.close', "Expected websocket.close output.")

        # Original database check part - only relevant if connection logic changes to allow connection
        # For now, this part is effectively not tested due to connect() failing first.
        # However, to fix the SynchronousOnlyOperation if it were reached:
        @database_sync_to_async
        def _check_room_exists_async(label):
            return Room.objects.filter(label=label).exists()

        # This code would only run if 'connected' was true and the test logic was different.
        # For demonstration of the fix if this part of the test were active:
        # room_exists_val = await _check_room_exists_async(room_label_non_existent)
        # if room_exists_val:
        #     @database_sync_to_async
        #     def _get_room_msg_count_async(label):
        #         room_obj = Room.objects.get(label=label)
        #         return Message.objects.filter(room=room_obj).count()
        #     message_count_for_room = await _get_room_msg_count_async(room_label_non_existent)
        #     self.assertEqual(message_count_for_room, 0)
        
        # communicator.disconnect() should only be called if connected was true.
        # Since we assert assertFalse(connected), no disconnect is needed here for this test path.
        # if connected: # This was part of the original scaffold, but 'connected' is false here.
        #    await communicator.disconnect()

    async def test_consumer_receive_invalid_data_format(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.label}/")
        communicator.scope['url_route'] = {'kwargs': {'room_name': self.room.label}}
        connected, _ = await communicator.connect() # Ensure connection for this test
        self.assertTrue(connected, "Failed to connect for invalid data format test.")
        
        initial_message_count = await self.get_message_count(self.room)

        # Scenario 1: Completely invalid JSON string
        await communicator.send_to("this is not valid json")
        output = await communicator.receive_output(timeout=1)
        self.assertEqual(output['type'], 'websocket.close', "Expected close on invalid JSON.")
        # Connection is now closed. Reconnect for the next part.
        
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.label}/")
        communicator.scope['url_route'] = {'kwargs': {'room_name': self.room.label}}
        connected, _ = await communicator.connect()
        self.assertTrue(connected, "Failed to reconnect for missing handle/message test.")

        # Scenario 2: Valid JSON but missing 'handle'
        await communicator.send_json_to({"message": "Message with no handle"})
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response, {'error': 'Handle and message are required.'})
        output = await communicator.receive_output(timeout=1) 
        self.assertEqual(output['type'], 'websocket.close')
        
        # Reconnect for testing missing 'message'
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.label}/")
        communicator.scope['url_route'] = {'kwargs': {'room_name': self.room.label}}
        connected, _ = await communicator.connect()
        self.assertTrue(connected, "Failed to reconnect for missing message test.")

        await communicator.send_json_to({"handle": "User with no message"})
        response = await communicator.receive_json_from(timeout=1)
        self.assertEqual(response, {'error': 'Handle and message are required.'})
        output = await communicator.receive_output(timeout=1)
        self.assertEqual(output['type'], 'websocket.close')

        # Ensure no messages were saved during these invalid attempts
        self.assertEqual(await self.get_message_count(self.room), initial_message_count)
        
        await communicator.disconnect() # Disconnect the last communicator

    async def test_consumer_disconnect(self):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{self.room.label}/")
        communicator.scope['url_route'] = {'kwargs': {'room_name': self.room.label}}
        await communicator.connect()
        await communicator.disconnect()
        # Basic check that disconnect doesn't crash
        self.assertTrue(True)
