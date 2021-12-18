import re

class YouTubeStripVideoID:
    """
    Strip the YouTube Video
    ID from a URL if possible,
    using regex.
    """
    def __init__(self):
        self.full = re.compile('(?<=youtube.com\/watch\?v=).*').search
        self.short = re.compile('(?<=youtu.be\/).*').search

    def __call__(self, url: str) -> str or None:
        """
        Parameters
        ----------
        url : str
            Possible YouTube
            video url.

        Returns
        -------
        id : str or None
            YouTube video ID when
            it can be found, otherwise
            it returns None.
        """
        if 'youtube' in url:
            return self.full(url)
        elif 'youtu.be' in url:
            return self.short(url)