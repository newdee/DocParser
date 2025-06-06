from collections.abc import Callable, Awaitable
from functools import wraps
from io import BytesIO
import re
from time import perf_counter
from typing import ParamSpec, TypeVar
from loguru import logger
from pathlib import Path
from typeric.result import resulty
from urllib.parse import urlparse, quote
import requests


def is_valid_url(address: list[str]) -> bool:
    try:
        for addr in address:
            response = requests.head(addr)
            logger.info(f"{response.status_code = }")
            if response.status_code < 200 or response.status_code >= 400:
                return False
        return True
    except Exception as e:
        logger.error(e)
        return False


@resulty
def download_pdf(addr: str) -> tuple[str, BytesIO]:
    resp = requests.get(addr)
    resp.raise_for_status()
    cd = resp.headers.get("Content-Disposition")
    if cd:
        fname = re.findall('filename="?([^"]+)"?', cd)
        if fname:
            return (fname[0], BytesIO(resp.content))
    path = urlparse(addr).path

    return (quote(path.split("/")[-1]), BytesIO(resp.content))


def is_valid_path(address: list[str]) -> bool:
    try:
        for addr in address:
            path = Path(addr)
            if not path.exists():
                return False
        return True
    except Exception as e:
        logger.error(e)
        return False


P = ParamSpec("P")
R = TypeVar("R")


def get_time_async(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def timed_execution(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.info(f"Starting async func@{func.__name__} with {args= }, {kwargs= }")
        try:
            start_time = perf_counter()
            result = await func(*args, **kwargs)
            end_time = perf_counter()
            logger.info(f"{func.__name__} took {end_time - start_time:.3f}s")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with exception: {e}")
            raise

    return timed_execution


def get_time_sync(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def timed_execution(*args: P.args, **kwargs: P.kwargs) -> R:
        logger.info(f"Starting sync func@{func.__name__} with {args= }, {kwargs= }")
        try:
            start_time = perf_counter()
            result = func(*args, **kwargs)
            end_time = perf_counter()
            logger.info(f"{func.__name__} took {end_time - start_time:.3f}s")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with exception: {e}")
            raise

    return timed_execution
