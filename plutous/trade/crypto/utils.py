from typing import Callable, Optional, Awaitable, List, Dict, Any
from datetime import datetime, timedelta, timezone
import numpy as np
import functools
import logging
import asyncio
import ccxt


logger = logging.getLogger(__name__)
Coroutine = Callable[[Any], Awaitable[List[Dict[str, Any]]]]


def _preprocess(kwargs: dict, co_varnames: tuple[str]):
    """
    Update ``since`` in kwargs so that it accepts ``millisecond`` and ``datetime``
    and ``**kwargs`` to ``params``.
    """
    since = kwargs.get("since")
    if since is not None:
        if isinstance(since, datetime):
            kwargs["since"] = int(since.timestamp() * 1000)
    params = kwargs.get("params", {})
    for key in kwargs.copy():
        if key not in co_varnames:
            params[key] = kwargs.pop(key)
    kwargs["params"] = params


def add_preprocess(cls):
    """
    Decorator for a ``ccxt.Exchange`` class to add ``preprocess``
    to all existing ``fetch_*`` function  with ``params`` in argument.
    """

    def decorate(func: Coroutine) -> Coroutine:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> List[Dict[str, Any]]:
            func_code = func.__code__
            co_varnames = func_code.co_varnames[: func_code.co_argcount]
            kwargs.update(zip(co_varnames, args))
            _preprocess(kwargs, co_varnames)
            return await func(**kwargs)

        return wrapper

    for attr in dir(cls):
        if "fetch_" in attr:
            func: Callable = getattr(cls, attr)
            func_code = func.__code__
            co_varnames = func_code.co_varnames[: func_code.co_argcount]

            if "params" in co_varnames:
                setattr(cls, attr, decorate(func))
    return cls


def paginate(
    id_arg: str = "fromId",
    start_time_arg: str = "startTime",
    end_time_arg: str = "endTime",
    max_limit: int | float = float("inf"),
    max_interval: Optional[timedelta] = None,
) -> Callable:
    """
    Decorator for adding pagination to a ``ccxt.Exchange`` class's method
    based on specified settings.

    Parameters
    ----------
    id_arg : str, optional
        Parameter name to filter ``id`` of the request. Default to ``fromId``.
    start_time_arg : str, optional
        Parameter name for start_time filter of the request. Default to ``startTime``.
    end_time_arg : str, optional
        Parameter name for end_time filter of the request. Default to ``endTime``.
    max_limit: int, optional
        Max limit of the given endpoint. Default to ``float('inf')``.
    max_interval: datetime.timedelta, optional
        Max interval between ``start_time`` and ``end_time`` that the give end points allowed

    Returns
    ----------
    Callable
        Decorator on given function
    """

    def decorator(func: Coroutine) -> Coroutine:
        async def paginate_over_limit(**kwargs) -> List[Dict[str, Any]]:
            params = kwargs["params"]
            limit = kwargs.get("limit") or float("inf")
            limit_arg = min(limit, max_limit)
            kwargs["limit"] = limit_arg if limit_arg != float("inf") else None

            records = await func(**kwargs)
            all_records = records
            limit -= max_limit
            limit = limit if limit != np.nan else 0

            while (records == max_limit) & (limit > 0):
                if id_arg in kwargs:
                    params[id_arg] = int(records[-1]["id"]) + 1
                elif ("since" in kwargs) or (start_time_arg in params):
                    kwargs["since"] = int(records[-1]["timestamp"]) + 1
                else:
                    break
                kwargs["limit"] = min(limit, max_limit)
                records = await func(**kwargs)
                all_records.extend(records)
                limit -= max_limit
            return all_records

        async def paginate_over_interval(**kwargs) -> List[Dict[str, Any]]:
            params = kwargs["params"]
            since = kwargs.get("since") or params.get(start_time_arg)
            now = int(datetime.now(timezone.utc).timestamp() * 1000)
            end = params.get(end_time_arg, now)
            if "timeframe" in kwargs:
                diff = (
                    ccxt.Exchange.parse_timeframe(kwargs["timeframe"])
                    * 1000
                    * max_limit
                )
                kwargs["limit"] = max_limit
            else:
                diff = (
                    int(max_interval.total_seconds() * 1000)
                    if max_interval is not None
                    else (now - since + 1)
                )

            coroutines = []
            for since in range(since, end, diff):
                params = kwargs.copy()
                kwargs["since"] = since
                params[end_time_arg] = min(since + diff - 1, end)
                coroutines.append(paginate_over_limit(**kwargs))

            logger.info(
                f"Calling {func.__name__} {kwargs} "
                + f"max_interval: {max_interval} "
                + f"Paginating over {len(coroutines)} intervals."
            )
            records = []
            all_records = await asyncio.gather(*coroutines)
            for record in all_records:
                records.extend(record)

            return records

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> List[Dict[str, Any]]:
            co_varnames = func.__code__.co_varnames
            kwargs.update(zip(co_varnames, args))
            _preprocess(kwargs, co_varnames)

            if id_arg in kwargs:
                return await paginate_over_limit(**kwargs)
            if ("since" in kwargs) or (start_time_arg in kwargs["params"]):
                return await paginate_over_interval(**kwargs)
            return await func(**kwargs)

        return wrapper

    return decorator
