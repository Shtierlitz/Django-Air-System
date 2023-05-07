import json
import logging
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from flights.models import User, Ticket
from flights.utils import send_message

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        logger.info(f"WebSocket connected: {self.scope}")
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send join message
        username = self.scope['user'].username
        await self.send_join_message(username)

    async def disconnect(self, close_code):

        logger.info(f"WebSocket disconnected: {self.scope}")
        # Send leave message
        username = self.scope['user'].username
        await self.send_leave_message(username)

        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        username = self.scope["user"].username

        if message.startswith("/"):
            # Обработка команды
            await self.handle_command(message, username)
        else:
            # Отправка сообщения
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "message": message, "username": username},
            )
        logger.info(f"WebSocket received message: {text_data}")

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        group_name = await self.get_user_group(username)

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {"message": f"{username} ({group_name}): {message}",}
            )
        )

    async def handle_command(self, command, username):
        if command == "/help":
            help_message = (
                "Available command list:\n"
                "/help - show command list\n"
                "/approve check_in - approves ticket check-in status (Supervisor or Check-In managers only)\n"
                "/approve onboard - approves ticket onboard status (Supervisor or Onboard managers only)"
                # Добавьте сюда другие команды и их описания
            )
            await self.send(text_data=json.dumps({"message": help_message}))
        elif command == "/approve check_in":
            has_permission = await self.user_has_permission(self.scope['user'].id, 'flights.can_approve_check_in')
            if has_permission:
                await self.change_checkin_status(self.room_name)
                confirm_message = (
                    f"Ticket {self.room_name} check-in was successfully approved!"
                )
                await self.send(text_data=json.dumps({"message": confirm_message}))
            else:
                error_message = f"{username}, you don't have permission to approve check-ins. " \
                                f"Please contact your Supervisor."
                await self.send(text_data=json.dumps({"message": error_message}))
        elif command == "/approve onboard":
            has_permission = await self.user_has_permission(self.scope['user'].id, 'flights.can_approve_onboard')
            if has_permission:
                await self.change_onboard_status(self.room_name)
                confirm_message = (
                    f"Ticket {self.room_name} onboard was successfully approved!"
                )
                await self.send(text_data=json.dumps({"message": confirm_message}))
            else:
                error_message = f"{username}, you don't have permission to approve onboards. " \
                                f""
                await self.send(text_data=json.dumps({"message": error_message}))
        else:
            error_message = f"{username}, unknown command: '{command}'. Type /help for command list."
            await self.send(text_data=json.dumps({"message": error_message}))

    async def send_join_message(self, username):
        join_message = " has joined the chat."
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': join_message,
                'username': username,
            }
        )

    async def send_leave_message(self, username):
        leave_message = " has left the chat."
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': leave_message,
                'username': username,
            }
        )

    @database_sync_to_async
    def get_user_group(self, username):
        user = User.objects.filter(username=username).first()
        if user.groups.exists():
            group = user.groups.first().name
        else:
            group = "User"
        return group

    @database_sync_to_async
    def change_checkin_status(self, code):
        ticket = Ticket.objects.filter(code=code).first()
        ticket.check_in = Ticket.Checking.APPROVED
        ticket.save()
        subject = f'Ticket {ticket.code} - check in.'
        content = f"<p>Greetings our dear customer!</p>" \
                  f"<p>Congratulations! You have been successfully checked in on board.</p>" \
                  f"<p>You can now await for boarding permission in airports awaiting hall.</p>" \
                  f"<p>Please do not miss yours boarding time.</p>" \
                  f"<p>With best regards - Check In Manger."
        send_message(ticket.user.username, ticket.user.email, content, subject)

    @database_sync_to_async
    def change_onboard_status(self, code):
        ticket = Ticket.objects.filter(code=code).first()
        ticket.onboard = Ticket.Checking.APPROVED
        ticket.save()
        subject = f'Ticket {ticket.code} - onboard.'
        content = f"<p>Greetings our dear customer!</p>" \
                  f"<p>You have successfully completed your boarding check.</p>" \
                  f"<p>Please go to the plane and follow the instructions of the flight attendants.</p>" \
                  f"<p>From the whole crew we wish you - Fly to your dreams!</p>" \
                  f"With Best Regards - Boarding Manager."
        send_message(ticket.user.username, ticket.user.email, content, subject)

    @database_sync_to_async
    def user_has_permission(self, user_id, permission):
        user = User.objects.get(pk=user_id)
        return user.has_perm(permission)


class StatusUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = f"user_{self.scope['url_route']['kwargs']['user_id']}"
        self.room_group_name = f"status_updates_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket connected: {self.scope}")
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        logger.info(f"WebSocket disconnected: {self.scope}")

    async def receive(self, text_data):
        pass

    async def send_status_update(self, event):
        await self.send(text_data=json.dumps(event['content']))
        logger.info(f"WebSocket send_status_update: {json.dumps(event['content'])}")