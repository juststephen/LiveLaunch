from datetime import datetime, timezone
from dateutil.parser import isoparse
from operator import itemgetter

try:
    from bin import get
except:
    from aget import get

class SpaceflightNewsAPI:
    """
    Spaceflight News API (SNAPI) by
    The Space Devs (https://thespacedevs.com/).
    """
    def __init__(self):
        # Keys in the returned data containing non ID data.
        self.data_keys = (
            'title',
            'url',
            'imageUrl',
            'newsSite',
            'summary',
            'publishedAt'
        )
        # Object to filter dictionaries
        self.get_items = itemgetter(*self.data_keys)
        # Store current datetime for first call of `.fetch_news()`
        self.last_check = datetime.now(timezone.utc)
        # SNAPI
        self.snapi_url = 'https://api.spaceflightnewsapi.net/v3/articles'

    async def __call__(self) -> list[dict[str, datetime and str]]:
        """
        Fetches news articles from SNAPI,
        only returns articles published
        after last call or object creation.
        """
        # Request data
        news = await get(self.snapi_url, True)

        # Retun empty list when failed
        if not news:
            return []

        # Iterate over articles to filter and convert
        new_news = []
        for article in news:
            # Convert `publishedAT`'s to datetime
            article['publishedAt'] = isoparse(article['publishedAt'])

            # Check if the article is new, otherwise ignore it
            if article['publishedAt'] > self.last_check:
                # Filter news so it only contains `.data_keys` keys
                new_news.append(
                    dict(
                        zip(self.data_keys, self.get_items(article))
                    )
                )

        # Store current datetime for next call
        self.last_check = datetime.now(timezone.utc)

        # Return new news list
        return new_news
