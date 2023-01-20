#pylint: skip-file

import json
import iso8601
import rfc3339
import requests

from jsonschema import Draft7Validator, FormatChecker
from shapely import MultiLineString, LineString
from datetime import datetime


event = {
    'time_interval': {
        'start': '2023-01-01T00:00:00Z',
        'finish': '2023-01-02T00:00:00Z',
    },
    'events': [
        {
            'start': '2023-01-01T01:00:00Z',
            'finish': '2023-01-01T03:00:00Z',
        },
        {
            'start': '2023-01-01T02:00:00Z',
            'finish': '2023-01-01T04:00:00Z',
        },
        {
            'start': '2023-01-01T08:00:00Z',
            'finish': '2023-01-01T10:00:00Z',
        },
    ]
}


def lambda_handler(event, _):
    return FreeTimeCalculator().process(event)


class TimeInterval:
    def __init__(self, t0, t1):
        self.t0 = t0
        self.t1 = t1

    def __str__(self):
        return f'{self.t0} {self.t1}'


class FreeTimeCalculator:
    def process(self, lambda_event):
        self._validate(lambda_event)
        print(lambda_event)
        time_interval, events = self._unpack_event(lambda_event)
        time_interval_linestring = MultiLineString([[(time_interval.t0, 0),
                                                     (time_interval.t1, 0)]])
        events_linestring = MultiLineString()
        for event in events:
            print(event)
            event_linestring = MultiLineString(
                [[(event.t0, 0), (event.t1, 0)]])
            events_linestring = events_linestring.union(event_linestring)
            print(events_linestring)

        resulting_linestring = time_interval_linestring - events_linestring
        resulting_linestring = self._filter(resulting_linestring)
        return self._build_response(resulting_linestring)

    @staticmethod
    def _validate(lambda_event):
        with open('schema.json', 'r') as file:
            validator = Draft7Validator(schema=json.load(
                file), format_checker=FormatChecker())
            validator.is_valid(lambda_event)

    def _unpack_event(self, lambda_event):
        time_interval = self._time_interval_from_json_object(
            lambda_event['time_interval'])
        events = [self._time_interval_from_json_object(
            event) for event in lambda_event['events']]
        return time_interval, events

    @staticmethod
    def _time_interval_from_json_object(json_object):
        start = iso8601.parse_date(json_object['start'])
        finish = iso8601.parse_date(json_object['finish'])
        print(json_object)
        print(start, finish)
        return TimeInterval(start.timestamp(), finish.timestamp())

    @staticmethod
    def _filter(resulting_linestring, **kwargs):
        return resulting_linestring

    @staticmethod
    def _build_response(resulting_linestring):
        response = []
        for free_time in resulting_linestring.geoms:
            response.append({
                'start': rfc3339.rfc3339(datetime.utcfromtimestamp(free_time.bounds[0])),
                'finish': rfc3339.rfc3339(datetime.utcfromtimestamp(free_time.bounds[2]))
            })
        return {'response': response}


print(lambda_handler(event, None))
