from googleapiclient.discovery import build
from os import getenv

class YouTubeAPI:
    """
    YouTube API class with methods for getting
    information of videos and their channels.

    Notes
    -----
    Available methods:
        `.get_channel_thumbtitle()`
        `.get_channel_from_video()`
    """
    def __init__(self):
        # Youtube v3 API
        self._key = getenv('YOUTUBE_KEY')
        self._API_SERVICE_NAME = 'youtube'
        self._API_VERSION = 'v3'
        # Authenticate
        self._get_authenticated_service()

    def _get_authenticated_service(self) -> None:
        """
        Logs into the YouTube API using the API key.

        Notes
        -----
        Stores the API access resource ``googleapiclient.discovery.build``
        into the `.youtube` variable.
        """
        self.youtube = build(self._API_SERVICE_NAME, self._API_VERSION, \
            developerKey=self._key)

    def get_channel_thumbtitle(self, id: str) -> dict[str, str] or None:
        """
        Retrieves a thumbnail URL and title for a given YouTube channel ID.

        Parameters
        ----------
        id : str
            YouTube channel ID.

        Returns
        -------
        (thumb, title) : tuple of two strings or None
            Returns the thumbnail and channel title or None if it fails.
        """
        try:
            response = self.youtube.channels().list(
                part='snippet',
                id=id,
                fields='items/snippet(title,thumbnails/default/url)'
            ).execute()
            thumb = response['items'][0]['snippet']['thumbnails']['default']['url']
            title = response['items'][0]['snippet']['title']
            return thumb, title
        except:
            return None

    def get_channel_broadcasts(self, id: str, eventType: str = 'upcoming', maxResults: int = 8) -> list[str] or None:
        """
        #### DEPRECATED ####

        Retrieves broadcast URLs for a given YouTube channel id.

        Parameters
        ----------
        id : str
            YouTube channel ID.
        eventType : int, default: 'upcoming'
            What videos to search for.
        maxResults : int, default: 8
            maximum amount of returned results.

        Returns
        -------
        videos : list containing strings or None
            Returns a list containing URLs or None if it fails.
        """
        try:
            response = self.youtube.search().list(
                part='snippet',
                channelId=id,
                eventType=eventType,
                maxResults=maxResults,
                type='video',
                fields='items/id/videoId'
            ).execute()
            return [f"https://www.youtube.com/watch?v={i['id']['videoId']}" for i in response['items']]
        except:
            return None

    def get_channel_from_video(self, id: str) -> str or None:
        """
        Uses a YouTube video ID to find the corresponding channel ID.

        Parameters
        ----------
        id : str
            YouTube video ID.

        Returns
        -------
        channel : str or None
            Returns a string containing the channel ID or None if it fails. 
        """
        try:
            response = self.youtube.videos().list(
                part='snippet',
                id=id,
                fields='items/snippet/channelId'
            ).execute()
            return response['items'][0]['snippet']['channelId']
        except:
            return None