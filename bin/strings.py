def combine_strings(
    strings: list[str],
    block_size: int = 1018,
    encoding: str = 'utf-8'
) -> list[str]:
    """
    Combine strings until the block size is reached,
    then combining starts again from that point on.

    Parameters
    ----------
    strings : list[str]
        List of strings to combine.
    block_size : int, default: 1018
        Block size limit for combining.
        1018 comes from 1024 minus
        six times the grave accent,
        which is used for code blocks.
    encoding : str, default: 'utf-8'
        Encoding to use for counting
        the amount of bytes.

    Returns
    -------
    result : list[str]
        A list of the combined strings.

    Notes
    -----
    The function assumes that all strings, within the
    given list, are smaller than or equal to the block size.
    """
    combined = ''
    combined_size = 0
    result: list[str] = []

    for string in strings:
        # Count bytes of current string
        string_size = len(string.encode(encoding))
        # Currently still within the block
        if combined_size + string_size <= block_size:
            combined += string
            combined_size += string_size
        # Outside of the block, starting a new string
        else:
            result.append(combined)
            combined = string
            combined_size = string_size

    # Add final string
    if combined:
        result.append(combined)

    return result
