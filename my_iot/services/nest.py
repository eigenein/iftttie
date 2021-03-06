from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Tuple

from aiohttp_sse_client.client import EventSource, MessageEvent
from loguru import logger
from multidict import MultiDict
from ujson import loads

from my_iot.services.base import Service
from my_iot.types_ import Event, Unit

url = 'https://developer-api.nest.com'
headers = MultiDict([('Accept', 'text/event-stream')])
timestamp_format = '%Y-%m-%dT%H:%M:%S.%f%z'


class Nest(Service):
    def __init__(self, token: str):
        self.token = token
        self.params = {'auth': self.token}

    @property
    async def events(self):
        logger.info('Connecting to the streaming API…')
        async with EventSource(url, params=self.params, headers=headers, timeout=None) as source:
            logger.info('Connected.')
            async for server_event in source:
                if server_event.type == 'put':
                    for event in yield_events(server_event):
                        yield event

    def __str__(self) -> str:
        return f'{Nest.__name__}(token="{self.token[:4]}…{self.token[-4:]}")'


def yield_events(event: MessageEvent) -> Iterable[Event]:
    data: dict = loads(event.data)['data']
    devices: dict = data['devices']

    yield from yield_devices_events(data['structures'], 'nest:structure', [
        ('away', Unit.ENUM, 'Away'),
        ('wwn_security_state', Unit.ENUM, 'Security State'),
    ])
    yield from yield_devices_events(devices['cameras'], 'nest:camera', [
        ('is_streaming', Unit.BOOLEAN, 'Streaming'),
        ('is_online', Unit.BOOLEAN, 'Online'),
        ('snapshot_url', Unit.IMAGE_URL, 'Snapshot'),
    ])
    yield from yield_devices_events(devices['thermostats'], 'nest:thermostat', [
        ('ambient_temperature_c', Unit.CELSIUS, 'Ambient Temperature'),
        ('humidity', Unit.RH, 'Humidity'),
        ('is_online', Unit.BOOLEAN, 'Online'),
        ('hvac_state', Unit.ENUM, 'HVAC'),
        ('target_temperature_c', Unit.CELSIUS, 'Target Temperature'),
    ])
    yield from yield_devices_events(devices['smoke_co_alarms'], 'nest:smoke_co_alarm', [
        ('is_online', Unit.BOOLEAN, 'Online'),
    ])

    for camera_id, camera in devices['cameras'].items():
        last_event = camera.get('last_event')
        if last_event:
            yield Event(
                channel=f'nest:camera:{camera_id}:last_animated_image_url',
                value=last_event['animated_image_url'],
                unit=Unit.IMAGE_URL,
                timestamp=datetime.strptime(last_event['start_time'], timestamp_format),
                title=f'{camera["name_long"]} Last Event',
            )


def yield_devices_events(devices: dict, prefix: str, keys: List[Tuple[str, Unit, str]]) -> Iterable[Event]:
    for id_, device in devices.items():
        for key, unit, title in keys:
            yield Event(
                channel=f'{prefix}:{id_}:{key}',
                value=device[key],
                unit=unit,
                title=f'{device.get("name_long") or device["name"]} {title}',
            )
