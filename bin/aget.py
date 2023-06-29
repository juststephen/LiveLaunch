import aiohttp

async def get(
    url: str,
    *,
    headers: dict[str, str] = None,
    json: bool = False
) -> str or dict:
    """
    Use aiohttp to get the contents of
    a webpage or API asynchronously.

    Parameters
    ----------
    url : str
        String containing the request URL.
    headers : dict[str, str], default: None
        Request header dictionary.
    json : bool, default: False
        Whether to return a json instead of text.

    Returns
    -------
    response : str or dict
        Response data in a form of a string or dictionairy
        depending on the json parameter.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if json:
                return await response.json()
            else:
                return await response.text()
