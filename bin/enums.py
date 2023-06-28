from enum import auto, Enum

class EnableDisable(Enum):
    """
    Enable/Disable enumeration
    for application commands.
    """
    Enable = auto()
    Disable = auto()

class Features(Enum):
    """
    LiveLaunch features
    for application commands.
    """
    All = auto()
    Events = auto()
    Messages = auto()
    News = auto()
    Notifications = auto()

class HideShow(Enum):
    """
    Hide/Show enumeration
    for application commands.
    """
    Hide = auto()
    Show = auto()

class IncludeExclude(Enum):
    """
    Include/Exclude enumeration
    for application commands.
    """
    Include = auto()
    Exclude = auto()
