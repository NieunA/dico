import sys
import typing
import inspect
import traceback


async def safe_call(coro, additional_message: typing.Optional[str] = None):
    """
    Calls coroutine, ignoring raised exception and only print traceback.
    This is used for event listener call, and intended to be used at creating task.

    :param coro: Coroutine to safely call
    :param additional_message: Additional traceback message to print at the top.
    """

    try:
        await coro
    except Exception as ex:
        tb = traceback.format_exc()
        if additional_message:
            _p = additional_message + "\n" + tb
        else:
            _p = tb
        print(_p, file=sys.stderr)


def cdn_url(route, *, image_hash, extension="webp", size=1024, **snowflake_ids):
    if not 16 <= size <= 4096:
        raise ValueError("size must be between 16 and 4096.")
    if snowflake_ids:
        route = route.format(**snowflake_ids)
    return f"https://cdn.discordapp.com/{route}/{image_hash}.{extension}?size={size}"


def ensure_coro(func):
    async def wrap(*args, **kwargs):
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    return wrap


def format_discord_error(resp: dict):
    msgs = []

    def get_error_message(k, v):
        if "_errors" not in v:
            if isinstance(v, list):
                [msgs.append(f"In {k}: {x['message']} ({x['code']})") for x in v]
            else:
                for a, b in v.items():
                    get_error_message(k + "." + a, b)
        elif isinstance(v, list):
            pass
        else:
            [msgs.append(f"In {k}: {x['message']} ({x['code']})") for x in v["_errors"]]

    for k, v in resp.get("errors", {}).items():
        get_error_message(k, v)

    return resp["message"] + ((" - " + ' | '.join(msgs)) if msgs else "")


def from_emoji(emoji):
    from .model.emoji import Emoji  # Prevent circular import.
    if isinstance(emoji, Emoji):
        emoji = emoji.name if not emoji.id else f"{emoji.name}:{emoji.id}"
    elif emoji.startswith("<") and emoji.endswith(">"):
        emoji = emoji.lstrip("<").rstrip(">")
    return emoji


async def wrap_to_async(cls, client, resp, as_create: bool = True, **kwargs):
    resp = await resp
    if isinstance(resp, dict):
        args = (client, resp) if client is not None else (resp,)
        return cls.create(*args, **kwargs) if as_create else cls(*args, **kwargs)
    elif isinstance(resp, list):
        ret = []
        for x in resp:
            args = (client, x) if client is not None else (x,)
            ret.append(cls.create(*args, **kwargs) if as_create else cls(*args, **kwargs))
        return ret
    else:
        return resp
