"""
This module initializes the aioesphomeapi package by importing all necessary submodules.

The following submodules are imported:
- basic_entity
- binary_sensor
- button
- climate
- cover
- device
- fan
- light
- lock
- media_player
- native_api_server
- number
- select
- sensor
- siren
- switch
- text
- text_sensor
- time
- valve
- web_server

Additionally, it imports MESSAGE_TYPE_TO_PROTO from aioesphomeapi.core 
and all definitions from aioesphomeapi.api_pb2.
"""
from aioesphomeapi.api_pb2 import *
from aioesphomeapi.core import (
    MESSAGE_TYPE_TO_PROTO,
)

from .basic_entity import *
from .binary_sensor import *
from .button import *
from .climate import *
from .cover import *
from .device import *
from .fan import *
from .light import *
from .lock import *
from .media_player import *
from .native_api_server import *
from .number import *
from .select import *
from .sensor import *
from .siren import *
from .switch import *
from .text import *
from .text_sensor import *
from .time import *
from .valve import *
from .web_server import *
