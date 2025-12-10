import aiohttp
from typing import Any, Literal, overload

@overload
async def get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json: Literal[False] = False,
) -> str:
    ...

@overload
async def get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json: Literal[True],
) -> dict[str, Any]:
    ...

async def get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json: bool = False
) -> str | dict[str, Any]:
    """
    Use aiohttp to get the contents of
    a webpage or API asynchronously.

    Parameters
    ----------
    url : str
        String containing the request URL.
    headers : dict[str, str] or None, default: None
        Request header dictionary.
    json : bool, default: False
        Whether to return a json instead of text.

    Returns
    -------
    response : str or dict[str, Any]
        Response data in a form of a string or dictionairy
        depending on the json parameter.
    """
    async with (
        aiohttp.ClientSession() as session,
        session.get(url, headers=headers) as response
    ):
        if json:
            return await response.json()
        else:
            return await response.text()
