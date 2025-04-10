from __future__ import annotations

import enum
import json

from datetime import datetime
from collections import OrderedDict


class AggregationPeriod(enum.Enum):
    DAY = 1
    WEEK = 2
    MONTH = 3
    YEAR = 4

    def strToEnum(s: str):
        try:
            return getattr(AggregationPeriod, s.upper())
        except AttributeError:
            return AggregationPeriod.DAY


class Activity:
    start_date = None

    def newFromDict(d):
        ret = Activity()
        if ('start_date' in d):
            ret.start_date = d['start_date']

        if ('average_watts' in d):
            ret.average_watts = d['average_watts']

        if ('weighted_average_watts' in d):
            ret.weighted_average_watts = d['weighted_average_watts']

        if ('average_speed' in d):
            ret.average_speed = d['average_speed']

        if ('distance' in d):
            ret.distance = d['distance']

        if ('moving_time' in d):
            ret.moving_time = d['moving_time']

        if ('total_elevation_gain' in d):
            ret.total_elevation_gain = d['total_elevation_gain']

        return ret

    def getDateTime(self):
        date_string = self.start_date.rstrip('Z')
        date = datetime.fromisoformat(date_string)

        return date

    def getDateTimestamp(self):
        return self.getDateTime().timestamp()

    def getDateHumanReadable(self):
        date = self.getDateTime()

        return(datetime.strftime(date, "%x"))

    def dump(self):
        out = {
            'start_date': getattr(self, 'start_date', None),
            'average_watts': getattr(self, 'average_watts', None),
            'average_speed': getattr(self, 'average_speed', None),
            'distance': getattr(self, 'distance', None),
            'moving_time': getattr(self, 'moving_time', None),
            'total_elevation_gain': getattr(self, 'total_elevation_gain', None),
        }
        return out


class ActivityList(list):
    def sortByDate(self, reverse: bool = False):
        return sorted(
            self,
            reverse=reverse,
            key=lambda self: self.getDateTimestamp()
        )

    def getMinDate(self):
        return self.sortByDate()[0].getDateTime()

    def getMaxDate(self):
        return self.sortByDate()[len(self) - 1].getDateTime()

    def aggregateAverageMetricByPeriod(
            self, metric: str, period: AggregationPeriod) -> OrderedDict:
        """
        Average the requested metric for the activities in the list over the
        given time format

        :param metric: the metric to average
        :param period: the time period to aggregate over

        :return Dict of activies with activity keys set based on timef
        """
        grouped_by_time = {}

        for activity in self:
            time_key = self._getTimeKey(activity, period)

            if (time_key not in grouped_by_time):
                grouped_by_time[time_key] = []

            grouped_by_time[time_key].append(activity)

        ret = {}
        for time in grouped_by_time:
            out_total = 0
            out_count = 0
            for activity in grouped_by_time[time]:
                try:
                    value = getattr(activity, metric)

                    if (value > 0):
                        out_total += value
                        out_count += 1
                except AttributeError:
                    pass

            if (out_count > 0):
                ret[time] = (out_total / out_count)

        return OrderedDict(sorted(ret.items(), key=lambda item: item[0]))

    def aggregateTotalMetricByPeriod(
            self, metric: str, period: AggregationPeriod) -> OrderedDict:
        """
        Total the requested metric for the activities in the list over the
        given time format

        :param metric: the metric to average
        :param period: the time period to aggregate over

        :return Dict of activies with activity keys set based on timef
        """
        grouped_by_time = {}

        for activity in self:
            time_key = self._getTimeKey(activity, period)

            if (time_key not in grouped_by_time):
                grouped_by_time[time_key] = []

            grouped_by_time[time_key].append(activity)

        ret = {}

        for time in grouped_by_time:
            for activity in grouped_by_time[time]:
                value = getattr(activity, metric, 0)

                if (value == 0):
                    continue

                if (time in ret):
                    ret[time] += value
                else:
                    ret[time] = value

        return OrderedDict(sorted(ret.items(), key=lambda item: item[0]))

    def _getTimeKey(
            self, activity: Activity,
            period: AggregationPeriod) -> str:
        """Determine the time key (i.e. the period start date) for an activity
        and aggregation period

        :param period:   the aggregation period
        :param activity: the activity to deterime the time key for

        :return string the time key in Y-m-d format
        """
        if period == AggregationPeriod.WEEK:
            week = datetime.strftime(activity.getDateTime(), "%Y-%U-1")
            return datetime.strptime(week, "%Y-%U-%w").strftime("%Y-%m-%d")

        if period == AggregationPeriod.MONTH:
            return datetime.strftime(activity.getDateTime(), "%Y-%m-01")

        if period == AggregationPeriod.YEAR:
            return datetime.strftime(activity.getDateTime(), "%Y")

        return datetime.strftime(activity.getDateTime(), "%Y-%m-%d")

    def dump(self) -> str:
        """
        Dump out the entire activity list in json
        """
        out = []

        for activity in self:
            out.append(activity.dump())

        return json.dumps(out)

    def slice(activities: ActivityList, start: int, end: int) -> ActivityList:
        """
        Return a slice of a given activity list

        :param activities: the input activity list to slice
        :param start:      the starting index of the slice
        :param end:        the ending index of the slice. If greater than the
                           size of the ActivityList, we will return up to the
                           end of the list

        :return ActivityList
        """
        out = ActivityList()
        i = start

        if (end > len(activities)):
            end = len(activities)

        while (i < end):
            out.append(activities[i])
            i += 1

        return out

    def trimBeforeDate(activities: ActivityList, date: datetime):
        """
        Remove all activities before the given date

        :param date: the starting date. Any activities earlier than this will
                     be removed

        :return ActivityList trimmed to the given date
        """
        date_ts = date.timestamp()
        out = ActivityList()

        for activity in activities:
            if (activity.getDateTimestamp() > date_ts):
                out.append(activity)

        return out
