import asyncio
import functools
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Optional

import ccxt
import numpy as np

logger = logging.getLogger(__name__)
Coroutine = Callable[..., Awaitable[list[dict[str, Any]]]]


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
        async def paginate_over_limit(**kwargs) -> list[dict[str, Any]]:
            params: dict = kwargs["params"]
            limit = kwargs.get("limit") or float("inf")
            limit_arg = min(limit, max_limit)
            kwargs["limit"] = limit_arg if limit_arg != float("inf") else None

            records = await func(**kwargs)
            all_records = records
            limit -= max_limit
            limit = limit if limit != np.nan else 0

            while (len(records) == max_limit) & (limit > 0):
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

        async def paginate_over_interval(**kwargs) -> list[dict[str, Any]]:
            params: dict = kwargs["params"]
            since: int = kwargs.get("since") or params.get(start_time_arg)
            now = int(datetime.now(timezone.utc).timestamp() * 1000)
            end = params.get(end_time_arg, now)
            if "timeframe" in kwargs:
                diff = (
                    ccxt.Exchange.parse_timeframe(kwargs["timeframe"])
                    * 1000
                    * max_limit
                )
                kwargs["limit"] = min(max_limit, kwargs.get("limit") or float("inf"))
            else:
                diff = (
                    int(max_interval.total_seconds() * 1000)
                    if max_interval is not None
                    else (now - since + 1)
                )

            coroutines = []
            for since in range(since, end, diff):
                ckwargs = kwargs.copy()
                params = params.copy()
                ckwargs["since"] = since
                params[end_time_arg] = min(since + diff - 1, end)
                ckwargs["params"] = params
                coroutines.append(paginate_over_limit(**ckwargs))

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
        async def wrapper(*args, **kwargs) -> list[dict[str, Any]]:
            co_varnames = func.__code__.co_varnames
            kwargs.update(zip(co_varnames, args))

            if id_arg in kwargs:
                return await paginate_over_limit(**kwargs)
            if (kwargs.get("since") is not None) or (start_time_arg in kwargs.get("params", {})):
                return await paginate_over_interval(**kwargs)
            return await func(**kwargs)

        return wrapper

    return decorator
