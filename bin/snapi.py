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
            'id',
            'title',
            'url',
            'image_url',
            'news_site',
            'summary',
            'published_at'
        )
        # Object to filter dictionaries
        self.get_items = itemgetter(*self.data_keys)
        # SNAPI
        self.snapi_url = 'https://api.spaceflightnewsapi.net/v4/articles/'

    async def __call__(self) -> list[dict[str, datetime and str]]:
        """
        Fetches news articles from SNAPI,
        only returns articles published
        after last call or object creation.
        """
        # Request data
        news = await get(self.snapi_url, json=True)

        # Retun empty list when failed
        if not news['results']:
            return []

        # Iterate over articles to filter and convert
        filtered_news = []
        for article in news['results']:
            # Convert `published_at`'s to datetime
            article['published_at'] = isoparse(article['published_at'])

            # Filter news so it only contains `.data_keys` keys
            filtered_news.append(
                dict(
                    zip(self.data_keys, self.get_items(article))
                )
            )

        # Return filtered news list
        return filtered_news
