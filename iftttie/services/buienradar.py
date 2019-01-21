from __future__ import annotations

from asyncio import Queue, sleep
from datetime import datetime, timedelta
from typing import Any

from aiohttp import ClientSession
from loguru import logger

from iftttie.core import Update
from iftttie.services.base import BaseService
from iftttie.types import Unit

url = 'https://api.buienradar.nl/data/public/2.0/jsonfeed'
headers = [('Cache-Control', 'no-cache')]
keys = (
    ('airpressure', 'air_pressure', Unit.HPA, 'Pressure'),
    ('feeltemperature', 'feel_temperature', Unit.CELSIUS, 'Feels Like'),
    ('groundtemperature', 'ground_temperature', Unit.CELSIUS, 'Ground Temperature'),
    ('humidity', 'humidity', Unit.RH, 'Humidity'),
    ('temperature', 'temperature', Unit.CELSIUS, 'Air Temperature'),
    ('winddirection', 'wind_direction', Unit.ENUM, 'Wind Direction'),
    ('windspeed', 'wind_speed', Unit.MPS, 'Wind Speed'),
    ('windspeedBft', 'wind_speed_bft', Unit.BEAUFORT, 'Wind BFT'),
    ('sunpower', 'sun_power', Unit.WATT, 'Sun Power'),
)
timestamp_format = '%Y-%m-%dT%H:%M:%S'


class Buienradar(BaseService):
    def __init__(self, station_id: int, interval=timedelta(seconds=300.0)):
        self.station_id = station_id
        self.interval = interval.total_seconds()

    async def run(self, client_session: ClientSession, event_queue: Queue[Update], **kwargs: Any):
        while True:
            async with client_session.get(url, headers=headers) as response:
                feed = await response.json()
            sunrise = parse_datetime(feed['actual']['sunrise'])
            await event_queue.put(Update(
                key='buienradar:sunrise',
                value=sunrise,
                unit=Unit.DATETIME,
                title='Sunrise',
                id_=feed['actual']['sunrise'],
            ))
            sunset = parse_datetime(feed['actual']['sunset'])
            await event_queue.put(Update(
                key='buienradar:sunset',
                value=sunset,
                unit=Unit.DATETIME,
                title='Sunset',
                id_=feed['actual']['sunset'],
            ))
            await event_queue.put(Update(
                key='buienradar:day_length',
                value=(sunset - sunrise),
                unit=Unit.TIMEDELTA,
                title='Day Length',
                id_=feed['actual']['sunrise'],
            ))
            try:
                measurement = self.find_measurement(feed)
            except KeyError as e:
                logger.error('Station ID {} is not found.', e)
            else:
                for source_key, target_key, unit, title in keys:
                    await event_queue.put(Update(
                        key=f'buienradar:{self.station_id}:{target_key}',
                        value=measurement[source_key],
                        unit=unit,
                        timestamp=parse_datetime(measurement['timestamp']),
                        id_=measurement['timestamp'],
                        title=f'{measurement["stationname"]} {title}',
                    ))
            logger.debug('Next reading in {interval} seconds.', interval=self.interval)
            await sleep(self.interval)

    def find_measurement(self, feed: Any) -> Any:
        for measurement in feed['actual']['stationmeasurements']:
            if measurement['stationid'] == self.station_id:
                return measurement
        raise KeyError(self.station_id)

    def __str__(self) -> str:
        return f'{Buienradar.__name__}(station_id={self.station_id!r})'


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, timestamp_format).astimezone()
