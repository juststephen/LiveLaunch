from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
from os.path import isfile
import re

try:
    from bin import get
except:
    from aget import get

import asyncio

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
            except:
                self.channels = ['UCSUu1lih2RifWkKtDOJdsBA']
                self.keywords = {'UCSUu1lih2RifWkKtDOJdsBA': ['live']}
                self.ignore = {'UCSUu1lih2RifWkKtDOJdsBA': ['nsf live', 'nasaspaceflight live']}
        else:
            with open(self.ytfile, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        'channels': ['UCSUu1lih2RifWkKtDOJdsBA'],
                        'keywords': {"UCSUu1lih2RifWkKtDOJdsBA": ["live"]},
                        'ignore': {'UCSUu1lih2RifWkKtDOJdsBA': ['nsf live', 'nasaspaceflight live']}
                    },
                    f, indent=2
                )
            self.channels = ['UCSUu1lih2RifWkKtDOJdsBA']
            self.keywords = {'UCSUu1lih2RifWkKtDOJdsBA': ['live']}
            self.ignore = {'UCSUu1lih2RifWkKtDOJdsBA': ['nsf live', 'nasaspaceflight live']}

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

    def _findWholeWord(self, word: str) -> re.Pattern:
        """
        Searches for a word in the returned regex callable.

        Parameters
        ----------
        word : str
            Search word.

        Returns
        -------
        pattern : re.Pattern
            Returns the mentioned regex callable.

        Notes
        -----
        The returned regex pattern ignores upper- and lowercase.
        """
        return re.compile(r'\b({})\b'.format(word), \
            flags=re.IGNORECASE).search

    async def _get_channel_broadcastsRSS(self, channel: str, maxdaysago: int = 2) -> list[str]:
        """
        Retrieves broadcast IDs for a given YouTube channel ID using RSS.

        Parameters
        ----------
        channel : str
            YouTube channel ID.
        maxdaysago : int, default: 2
            Maximum days of video age to return

        Returns
        -------
        streams : list containing strings
            Returns a list containing YouTube video IDs.
        """
        soup = await self._requestRSS(channel)
        streams = []
        # Get current time
        now = datetime.now(timezone.utc)
        for entry in soup.find_all('entry'):
            # get the amount of days ago the video was published & updated
            published = datetime.fromisoformat(entry.published.text)
            updated = datetime.fromisoformat(entry.updated.text)
            # Check if the video was posted less or equal to 2 days ago
            if (now - updated).days <= maxdaysago and (updated - published).days < 2 * maxdaysago:
                # Check for the right words in the video title and then append them to the streams list
                if any([self._findWholeWord(i)(entry.title.text) for i in self.keywords[channel]]):
                    # Do not append them if the title contains an ignore keyword
                    if not (
                        (ignore := self.ignore.get(channel)) and
                        any([self._findWholeWord(i)(entry.title.text) for i in ignore])
                    ):
                        streams.append(entry.find('yt:videoId').string)
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
        streams = {}
        for channel in self.channels:
            streams[channel] = await self._get_channel_broadcastsRSS(channel)
        # Returning
        return streams
