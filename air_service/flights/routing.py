# from django.urls import path
# from . import consumers
#
# websocket_urlpatterns = [
#     path('ws/status_update/<int:user_id>/', consumers.StatusUpdateConsumer.as_asgi()),
# ]

from django.urls import re_path
from django.urls import path

from . import consumers
from .consumers import StatusUpdateConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
    path("ws/status_updates/", StatusUpdateConsumer.as_asgi()),
]