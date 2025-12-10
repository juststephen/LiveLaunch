from datetime import datetime, timedelta, timezone
from operator import itemgetter

from bin import get

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

    async def __call__(self) -> list[dict[str, datetime | str]]:
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

        # Datetime object to compare with
        now_min5days = datetime.now(timezone.utc) - timedelta(days=5)
        # Iterate over articles to filter and convert
        filtered_news: list[dict[str, datetime | str]] = []
        for article in news['results']:
            # Convert `published_at` to datetime
            article['published_at'] = datetime.fromisoformat(
                article['published_at']
            )

            # Skip article when it is older than 5 days
            if article['published_at'] < now_min5days:
                continue

            # Filter news so it only contains `.data_keys` keys
            filtered_news.append(
                dict(
                    zip(self.data_keys, self.get_items(article))
                )
            )

        # Return filtered news list
        return filtered_news
