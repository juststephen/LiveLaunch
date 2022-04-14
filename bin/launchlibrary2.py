from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse

try:
    from bin import ll2_get
except:
    from aget import ll2_get

class LaunchLibrary2:
    """
    Launch Library 2 by The Space Devs (https://thespacedevs.com/).
    """
    # Replacement text for when there is no stream
    no_stream = 'No stream yet'

    # Space Launch Now
    sln_event_url = 'https://spacelaunchnow.me/event/%s'
    sln_launch_url = 'https://spacelaunchnow.me/launch/%s'

    # Status colours for embeds
    status_colours = {
        1: 0x00FF00, # Go
        2: 0xFF0000, # TBD
        3: 0x00FF00, # Success
        4: 0xFF0000, # Failure
        5: 0xFFFF00, # Hold
        6: 0x0000FF, # In Flight
        7: 0xFF7F00, # Partial Failure
        8: 0xFF7F00, # TBC
    }

    # Status names for embeds
    status_names = {
        1: 'Go for Launch',
        2: 'To Be Determined',
        3: 'Launch Successful',
        4: 'Launch Failure',
        5: 'On Hold',
        6: 'Launch in Flight',
        7: 'Launch was a Partial Failure',
        8: 'To Be Confirmed',
    }

    def __init__(self):
        # Keys in the returned data containing non ID data.
        self.data_keys = (
            'name',
            'status',
            'description',
            'url',
            'image_url',
            'start',
            'end',
            'webcast_live',
            'agency_id'
        )
        # Max amount of events
        self.max_events = 64
        # Max description length
        self.max_description_length = 1000
        # 1 hour timedelta
        self.dt1 = timedelta(hours=-1)
        # End launch status tags
        self.launch_status_end = (3, 4, 7)
        # Notification status tags
        self.notification_status = (3, 4, 5, 6, 7)
        # Event duration (i.e. long EVAs)
        self.event_duration = {
            'EVA': timedelta(hours=6),
            'default': timedelta(hours=1)
        }
        # Supported image formats
        self.image_formats = ('.gif', '.jpeg', '.jpg', '.png', '.webp')
        # Launch Library 2 API
        self.ll2_launch_url = 'https://ll.thespacedevs.com/2.2.0/launch/upcoming/?mode=detailed&limit=32'
        self.ll2_event_url = 'https://ll.thespacedevs.com/2.2.0/event/upcoming/?limit=32'

    async def ll2_request(self, url: str) -> dict or None:
        """
        Requests the Launch Library 2 API for the results of `url`.

        Parameters
        ----------
        url : str
            URL for the Launch Library 2 request.

        Returns
        -------
        results : dict or None
            Get a dictionary of the results or None if it fails.
        """
        # Request data from the LL2 API
        try:
            result = await ll2_get(url)
        except:
            return
        else:
            if 'results' in result:
                return result['results']

    async def upcoming_launches(self) -> dict[str, dict[str, bool and datetime and int and str]]:
        """
        Gets data of upcoming launches.

        Returns
        -------
        streams : dict[str, dict[str, bool and datetime and str]]
            Dictionairy with the launch name, webcast_live,
            mission description, net time, video URL and LL2 ID.
        """
        # Request data
        results = await self.ll2_request(self.ll2_launch_url)
        if results is None:
            return {}

        # Storage dict for returning
        launches = {}

        # Go through data
        for entry in results:
            # Start datetime of the entry
            net = isoparse(entry['net'])

            # Name with potential [TBD] (To Be Determined) prefix
            name = entry['name'] if entry['status']['id'] != 2 else '[TBD] ' + entry['name']

            # Check for videos
            picked_video = None
            if 'vidURLs' in entry and entry['vidURLs']:
                priority = None
                for url in entry['vidURLs']:
                    # Find lowest priority value
                    if priority is None or url['priority'] < priority:
                        priority = url['priority']
                        picked_video = url['url']

            # Check description length and trim if needed
            if (description := entry['mission']) is not None:
                # Grab description
                description = description['description']
                # Check length
                if len(description) > self.max_description_length:
                    description = description[:self.max_description_length-3] + '...'

            # Image format check
            if (image_url := entry['image']) and not image_url.lower().endswith(self.image_formats):
                image_url = None

            # Adding event to launches list
            launches[entry['id']] = {
                'name': name,
                'description': description,
                'url': picked_video,
                'image_url': image_url,
                'start': net,
                'end': net + self.event_duration['default'],
                'webcast_live': entry['webcast_live'],
                'agency_id': entry['launch_service_provider']['id'],
                'agency_name': entry['launch_service_provider']['name'],
                'status': entry['status']['id']
            }

        # Returning
        return launches

    async def upcoming_events(self) -> dict[str, dict[str, bool and datetime and str]]:
        """
        Gets data of upcoming events.

        Returns
        -------
        streams : dict[str, dict[str, bool and datetime and str]]
            Dictionairy with the event name, webcast_live,
            mission description, net time, video URL and LL2 ID.
        """
        # Request data
        results = await self.ll2_request(self.ll2_event_url)
        if results is None:
            return {}

        # Storage dict for returning
        events = {}

        # Go through data
        for entry in results:
            # Start datetime of the entry
            net = isoparse(entry['date'])

            # Default duration if event type is not known
            event_type = entry['type']['name']
            if not event_type in self.event_duration:
                event_type = 'default'

            # Check for video
            picked_video = None
            if 'video_url' in entry and entry['video_url']:
                picked_video = entry['video_url']

            # Check description length and trim if needed
            if ((description := entry['description']) is not None
                    and len(description) > self.max_description_length):
                description = description[:self.max_description_length-3] + '...'

            # Image format check
            if (image_url := entry['feature_image']) and not image_url.lower().endswith(self.image_formats):
                image_url = None

            # Adding event to events list
            events[str(entry['id'])] = {
                'name': entry['name'],
                'description': description,
                'url': picked_video,
                'image_url': image_url,
                'start': net,
                'end': net + self.event_duration[event_type],
                'webcast_live': entry['webcast_live']
            }

        # Returning
        return events

    async def upcoming(self) -> dict[str, dict[str, bool and datetime and int and str]]:
        """
        Gets data of upcoming events and launches.

        Returns
        -------
        streams : dict[str, dict[str, bool and datetime and str]]
            Dictionairy with the event name, webcast_live,
            mission description, net time, video URL and LL2 ID.
        """
        launches = await self.upcoming_launches()
        events = await self.upcoming_events()

        # Only return when there are both launches and events
        if not ( launches and events ):
            return {}

        # Combine
        try: # Python 3.9+
            upcoming = launches | events
        except: # Older versions
            upcoming = {**launches, **events}

        # Sort by start datetime and limit it to `.max_events` items
        upcoming = dict(
            sorted(upcoming.items(), key=lambda item: item[1]['start'])[:self.max_events]
        )

        # Returning
        return upcoming
