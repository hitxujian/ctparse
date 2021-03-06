from datetime import datetime


class Artifact:
    def __init__(self):
        self.mstart = 0
        self.mend = 0
        self._attrs = ['mstart', 'mend']

    def update_span(self, *args):
        self.mstart = args[0].mstart
        self.mend = args[-1].mend
        return self

    def __len__(self):
        return self.mend - self.mstart

    def __str__(self):
        return ''

    def __repr__(self):
        return '{}[{}-{}]{{{}}}'.format(
            self.__class__.__name__, self.mstart, self.mend, str(self))

    def nb_str(self):
        return '{}[]{{{}}}'.format(
            self.__class__.__name__, str(self))

    def __eq__(self, other):
        return all(getattr(self, a) == getattr(other, a) for a in self._attrs)

    def __hash__(self):
        return hash(tuple(getattr(self, a) for a in self._attrs))

    def _hasOnly(self, *args):
        '''check that all attributes set to True are set (i.e. not None) and
        all set to False are not set (i.e. None)

        '''
        return all(
            getattr(self, a) is not None if a in args else getattr(self, a) is None
            for a in self._attrs)

    def _hasAtLeast(self, *args):
        '''check that all attributes set to True are set (i.e. not None) and
        all set to False are not set (i.e. None)

        '''
        return all(getattr(self, a) is not None for a in args)


class RegexMatch(Artifact):
    def __init__(self, id, m):
        super().__init__()
        self._attrs = ['mstart', 'mend', 'id']
        self.key = 'R{}'.format(id)
        self.id = id
        self.match = m
        self.mstart = m.span(self.key)[0]
        self.mend = m.span(self.key)[1]
        self._text = m.group(self.key)

    def __str__(self):
        return '{}:{}'.format(self.id, self._text)


pod_hours = {
    'earlymorning': (0, 6),
    'morning': (5, 8),
    'latemorning': (8, 10),
    'earlybeforenoon': (8, 11),
    'beforenoon': (9, 12),
    'latebeforenoon': (10, 13),
    'earlynoon': (11, 13),
    'noon': (12, 14),
    'latenoon': (13, 15),
    'earlyafternoon': (13, 15),
    'afternoon': (14, 16),
    'lateafternoon': (15, 17),
    'earlyevening': (16, 18),
    'evening': (17, 19),
    'lateevening': (18, 20),
    'earlynight': (18, 20),
    'night': (19, 22),
    'latenight': (20, 23)
}


class Time(Artifact):
    def __init__(self, year=None, month=None, day=None, hour=None, minute=None, DOW=None, POD=None):
        super().__init__()
        self._attrs = ['year', 'month', 'day', 'hour', 'minute', 'DOW', 'POD']
        # Might add some validation here, did not to avoid the overhead
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.DOW = DOW
        self.POD = POD

    # ------------------------------------------------------------------------------------
    # Make sure to not accidentially test bool(x) as False when x==0, but you meant x==None
    # ------------------------------------------------------------------------------------
    @property
    def isDOY(self):
        '''isDayOfYear <=> a dd.mm but not year
        '''
        return self._hasOnly('month', 'day')

    @property
    def isDOM(self):
        '''isDayOfMonth <=> a dd but no month
        '''
        return self._hasOnly('day')

    @property
    def isDOW(self):
        '''isDayOfWeek <=> DOW is the 0=Monday index; fragile test, as the DOW
        could be accompanied by e.g. a full date etc.; in practice,
        however, the production rules do not do that.

        '''
        return self._hasOnly('DOW')

    @property
    def isMonth(self):
        return self._hasOnly('month')

    @property
    def isPOD(self):
        '''isPartOfDay <=> morning, etc.; fragile, tests only that there is a
        POD and neither a full date nor a full time
        '''
        return self._hasOnly('POD')

    @property
    def isTOD(self):
        '''isTimeOfDay - only a time, not date'''
        return self._hasOnly('hour') or self._hasOnly('hour', 'minute')

    @property
    def isDate(self):
        '''isDate - only a date, not time'''
        return self._hasOnly('year', 'month', 'day')

    @property
    def isDateTime(self):
        '''a date and a time'''
        return (self._hasOnly('year', 'month', 'day', 'hour') or
                self._hasOnly('year', 'month', 'day', 'hour', 'minute'))

    @property
    def isYear(self):
        '''just a year'''
        return self._hasOnly('year')

    @property
    def hasDate(self):
        '''at least a date'''
        return self._hasAtLeast('year', 'month', 'day')

    @property
    def hasDOW(self):
        '''at least a day of week'''
        return self._hasAtLeast('DOW')

    @property
    def hasTime(self):
        '''at least a time to the hour'''
        return self._hasAtLeast('hour')

    @property
    def hasPOD(self):
        '''at least a part of day'''
        return self._hasAtLeast('POD')

    @classmethod
    def intersect(cls, a, b, exclude=[]):
        params = {}
        if type(a) != type(b):
            return None
        for attr in a._attrs:
            if attr in exclude:
                continue
            if getattr(a, attr) is not None and getattr(b, attr) is not None:
                if getattr(a, attr) == getattr(b, attr):
                    params[attr] = getattr(a, attr)
                else:
                    return None
            elif getattr(a, attr) is not None:
                params[attr] = getattr(a, attr)
            elif getattr(b, attr) is not None:
                params[attr] = getattr(b, attr)
        return Time(**params)

    def __str__(self):
        return '{}-{}-{} {}:{} ({}/{})'.format(
            '{:04d}'.format(self.year) if self.year is not None else 'X',
            '{:02d}'.format(self.month) if self.month is not None else 'X',
            '{:02d}'.format(self.day) if self.day is not None else 'X',
            '{:02d}'.format(self.hour) if self.hour is not None else 'X',
            '{:02d}'.format(self.minute) if self.minute is not None else 'X',
            '{:d}'.format(self.DOW) if self.DOW is not None else 'X',
            '{}'.format(self.POD) if self.POD is not None else 'X')

    @property
    def start(self):
        if self.hasPOD:
            hour = pod_hours[self.POD][0]
        else:
            hour = self.hour or 0
        return Time(year=self.year, month=self.month, day=self.day,
                    hour=hour, minute=self.minute or 0)

    @property
    def end(self):
        if self.hasPOD:
            hour = pod_hours[self.POD][1]
        else:
            hour = self.hour or 23
        return Time(year=self.year, month=self.month, day=self.day,
                    hour=hour, minute=self.minute or 59)

    @property
    def dt(self):
        return datetime(self.year, self.month, self.day,
                        self.hour, self.minute)


class Interval(Artifact):
    def __init__(self, t_from=None, t_to=None):
        super().__init__()
        self._attrs = ['t_from', 't_to']
        self.t_from = t_from
        self.t_to = t_to

    @property
    def isTimeInterval(self):
        return self.t_from.isTOD and self.t_to.isTOD

    def __str__(self):
        return '{} - {}'.format(
            str(self.t_from),
            str(self.t_to))

    @property
    def start(self):
        if self.t_from is not None:
            return self.t_from.start
        else:
            end = self.t_to.end
            end.hour = 0
            end.minute = 0
            return end

    @property
    def end(self):
        if self.t_to is not None:
            return self.t_to.end
        else:
            start = self.t_from.start
            start.hour = 23
            start.minute = 59
            return start
