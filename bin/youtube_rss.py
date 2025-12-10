from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
from os.path import isfile
import re

from bin import get

class YouTubeRSS:
    """
    YouTube RSS class with methods for getting
    videos from preselected channels in the
    `LiveLaunch_YouTube.json` file using keywords.

    Notes
    -----
    Use the `.request()` method to try to find new streams.
    """
    def __init__(self):
        # YouTube channels & keywords
        self.ytfile = 'LiveLaunch_YouTube.json'

        self.channels: list[str] = []
        self.keywords: dict[str, list[str]] = {}
        self.ignore: dict[str, list[str]] = {}
        self.agency_ids: dict[str, int] = {}

    def _get_channel_list(self) -> None:
        """
        Opens the `.ytfile` json file to see what YouTube channels to check and
        their keywords to find livestreams.

        Notes
        -----
        Stores the data into the `.channels` and `.keywords` variables.
        """
        if isfile(self.ytfile):
            with open(self.ytfile, 'r', encoding='utf-8') as f:
                f = json.load(f)
            try:
                self.channels = f['channels']
                self.keywords = f['keywords']
                self.ignore = f['ignore']
                self.agency_ids = f['agency_ids']
            except:
                self.channels = []
                self.keywords = {}
                self.ignore = {}
                self.agency_ids = {}
        else:
            with open(self.ytfile, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        'channels': [],
                        'keywords': {},
                        'ignore': {},
                        'agency_ids': {}
                    },
                    f, indent=2
                )
            self.channels = []
            self.keywords = {}
            self.ignore = {}
            self.agency_ids = {}

    async def _requestRSS(self, channel: str) -> BeautifulSoup:
        """
        Requests the RSS feed of the requested channel.

        Parameters
        ----------
        channel : str
            YouTube channel ID.

        Returns
        -------
        soup : bs4.BeautifulSoup
            Returns a soup object containing the RSS feed entries.
        """
        f = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel}'
        soup = BeautifulSoup(await get(f), features='xml')
        return soup

    def _word_in_text(self, word: str, text: str) -> bool:
        """
        Checks if a word is in a given text.

        Parameters
        ----------
        word : str
            Search word.
        text : str
            Text to search.

        Returns
        -------
        bool
        """
        match = re.search(r'\b({})\b'.format(word), text, re.IGNORECASE)
        return bool(match)

    async def _get_channel_broadcastsRSS(
        self,
        channel: str,
        max_days_ago: int = 2
    ) -> list[str]:
        """
        Retrieves broadcast IDs for a given YouTube channel ID using RSS.

        Parameters
        ----------
        channel : str
            YouTube channel ID.
        max_days_ago : int, default: 2
            Maximum days of video age to return

        Returns
        -------
        streams : list containing strings
            Returns a list containing YouTube video IDs.
        """
        soup = await self._requestRSS(channel)
        streams: list[str] = []
        # Get current time
        now = datetime.now(timezone.utc)
        for entry in soup.find_all('entry'):
            # get the amount of days ago the video was published & updated
            if entry.published:
                published = datetime.fromisoformat(entry.published.text)
            else:
                continue
            if entry.updated:
                updated = datetime.fromisoformat(entry.updated.text)
            else:
                continue

            # Check if the video was posted less or equal to 2 days ago
            if ((now - updated).days <= max_days_ago
                    and (updated - published).days < 2 * max_days_ago):
                # Check for the right words in the video title before appending
                if any([
                        self._word_in_text(i, entry.title.text)
                        if entry.title else False
                        for i in self.keywords[channel]
                ]):
                    # Don't append if the title contains an ignore keyword
                    if not (
                        (ignore := self.ignore.get(channel)) and
                        any([
                            self._word_in_text(i, entry.title.text)
                            if entry.title else False
                            for i in ignore
                        ])
                    ):
                        yt_vid_id = entry.find('yt:videoId')
                        if yt_vid_id and yt_vid_id.string:
                            streams.append(yt_vid_id.string)

        return streams

    async def request(self) -> dict[str, list[str]]:
        """
        Check the YouTube RSS of defined channels for new videos
        that fit the keywords set.

        Returns
        -------
        dict[str, list[str]] : dictionary
            Returns a dictionary containing lists of YouTube video IDs per
            channel and their YouTube channel ID as the value's key.
        """
        # Get YouTube channels and their keywords
        self._get_channel_list()
        # Request upcoming streams for channels and store livestream links
        streams: dict[str, list[str]] = {}
        for channel in self.channels:
            streams[channel] = await self._get_channel_broadcastsRSS(channel)
        # Returning
        return streams
