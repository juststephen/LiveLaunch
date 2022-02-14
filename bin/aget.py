import aiohttp
from os import getenv

# Authentication header
__ll2_header = {'Authorization': f'Token {getenv("LL2_TOKEN")}'}

async def get(url: str, *, json: bool = False) -> str or dict:
    """
    Use aiohttp to get the contents of
    a webpage or API asynchronously.

    Parameters
    ----------
    url : str
        String containing the request URL.
    json : bool, default: False
        Whether to return a json instead of text.

    Returns
    -------
    response : str or dict
        Response data in a form of a string or dictionairy
        depending on the json parameter.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if json:
                return await response.json()
            else:
                return await response.text()

async def ll2_get(url: str) -> dict:
    """
    Use aiohttp to get the contents of
    the Launch Library 2 API asynchronously.

    Parameters
    ----------
    url : str
        String containing the
        Launch Library 2 request URL.

    Returns
    -------
    response : dict
        Response data.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=__ll2_header) as response:
            return await response.json()