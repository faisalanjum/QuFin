from datetime import datetime
from sqlalchemy.inspection import inspect
import pytz
import inspect

def is_dst():
    """Determine whether or not Daylight Savings Time (DST) is currently in effect"""
    x = datetime(datetime.now().year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern')) # Jan 1 of this year
    y = datetime.now(pytz.timezone('US/Eastern'))

    # if DST is in effect, their offsets will be different
    return not (y.utcoffset() == x.utcoffset())

def divide_chunks(lst, nbr_of_itms):
    for i in range(0, len(lst), nbr_of_itms):
        yield lst[i:i + nbr_of_itms]

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

def remove_dupe_dicts(l):
    return [dict(t) for t in {tuple(d.items()) for d in l }]
