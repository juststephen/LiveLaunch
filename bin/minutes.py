def convert_minutes(minutes: int) -> str:
    """
    Convert minutes into a string
    containing days, hours and minutes.

    Parameters
    ----------
    minutes : int
        Amount of minutes.

    Returns
    -------
    time_str : str
        Minutes converted into a string containing
        the amount of days, hours and minutes.
    """
    days = minutes // 1440
    hours = ( minutes - days * 1440 ) // 60
    minutes %= 60

    time_str = ''

    if days != 0:
        time_str += f"{days} Day{'s' if days > 1 else ''} "
    if hours != 0:
        time_str += f"{hours} Hour{'s' if hours > 1 else ''} "
    if minutes !=0:
        time_str += f"{minutes} Minute{'s' if minutes > 1 else ''}"

    return time_str
