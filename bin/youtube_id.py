import re

def youtube_strip_video_id(url: str) -> str | None:
    """
    Try to strip a YouTube Video ID from a URL using regex.

    Parameters
    ----------
    url : str
        Possible YouTube video url.

    Returns
    -------
    id : str or None
        YouTube video ID when it can be found, otherwise it returns None.
    """
    match = None
    if 'youtube' in url:
        match = re.search(r'(?<=youtube.com\/watch\?v=).*', url)
    elif 'youtu.be' in url:
        match = re.search(r'(?<=youtu.be\/).*', url)
    if match:
        return match.group()
