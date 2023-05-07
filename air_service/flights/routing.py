from django.urls import re_path
from django.urls import path

from . import consumers
from .consumers import StatusUpdateConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
    path("ws/status_updates/<int:user_id>/", StatusUpdateConsumer.as_asgi()),

]