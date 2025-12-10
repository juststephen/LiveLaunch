from datetime import datetime, timedelta, timezone
from isodate import parse_duration  # type: ignore
import os
from typing import Any

from bin import get

type Item = dict[str, bool | datetime | int | str | None]

class LaunchLibrary2:
    """
    Launch Library 2 by The Space Devs (https://thespacedevs.com/).
    """
    # Replacement text for when there is no stream
    no_stream = 'No stream yet'

    # Flight Club
    fc_name = 'Flight Club'
    fc_emoji = '<:FlightClub:972885637436964946>'
    fc_url = 'https://flightclub.io/result?llId=%s'

    # Go4Liftoff
    g4l_name = 'Go4Liftoff'
    g4l_emoji = '<:Go4Liftoff:970384895593562192>'
    g4l_event_url = 'https://go4liftoff.com/event/id/%s'
    g4l_launch_url = 'https://go4liftoff.com/launch/id/%s'

    # Space Launch Now
    sln_name = 'Space Launch Now'
    sln_emoji = '<:SpaceLaunchNow:970384894985379960>'
    sln_event_url = 'https://spacelaunchnow.me/event/%s/'
    sln_launch_url = 'https://spacelaunchnow.me/launch/%s/'

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
        9: 0x00FFFF, # Payload Deployed
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
        9: 'Payload Deployed',
    }

    net_precision_formats = {
        2: '[NET %H:00 UTC] ', # Hour
        3: '[Morning (local)] ', # Morning
        4: '[Afternoon (local)] ', # Afternoon
        # Day (Windows or Linux)
        5: '[NET %B %#d] ' if os.name == 'nt' else '[NET %B %-d] ',
        # Week (Windows or Linux)
        6: '[NET Week %#W] ' if os.name == 'nt' else '[NET Week %-W] ',
        7: '[NET %B] ', # Month
        8: '[Q1 %Y] ', # Q1
        9: '[Q2 %Y] ', # Q2
        10: '[Q3 %Y] ', # Q3
        11: '[Q4 %Y] ', # Q4
        12: '[H1 %Y] ', # H1
        13: '[H2 %Y] ', # H2
        14: '[TBD %Y] ', # Year
        15: '[FY %Y] ', # Fiscal year
    }

    def __init__(self) -> None:
        # Authentication header
        self.__ll2_auth_header = {'Authorization': f"Token {os.getenv('LL2_TOKEN')}"}
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
            'agency_id',
            'flightclub'
        )
        # Max amount of events
        self.max_events = 64
        # Max description length
        self.max_description_length = 1000
        # Timedelta to limit time frame of the query
        self.timedelta_max_net = timedelta(days=1461)
        # End launch status tags
        self.launch_status_end = (3, 4, 7)
        # Event duration (i.e. long EVAs)
        self.event_duration = {
            'EVA': timedelta(hours=6),
            'default': timedelta(hours=1)
        }
        # Supported image formats
        self.image_formats = ('.gif', '.jpeg', '.jpg', '.png', '.webp')
        # Launch Library 2 API
        self.ll2_launch_url = 'https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=50&mode=detailed&net__lte=%s'
        self.ll2_event_url = 'https://ll.thespacedevs.com/2.3.0/events/upcoming/?date__lte=%s&limit=50'

    async def ll2_request(self, url: str) -> list[dict[str, Any]] | None:
        """
        Requests the Launch Library 2 API for the results of `url`.

        Parameters
        ----------
        url : str
            URL for the Launch Library 2 request.

        Returns
        -------
        results : dict[str, Any] | None
            Get a dictionary of the results or None if it fails.
        """
        # Request data from the LL2 API
        try:
            result = await get(
                url,
                headers=self.__ll2_auth_header,
                json=True
            )
        except:
            return
        else:
            if 'results' in result:
                return result['results']

    async def upcoming_launches(
        self
    ) -> dict[str, Item]:
        """
        Gets data of upcoming launches.

        Returns
        -------
        streams : dict[str, Item]
            Dictionairy with the launch name, webcast_live,
            mission description, net time, video URL and LL2 ID.
        """
        # Request data
        max_net = datetime.now(timezone.utc) + self.timedelta_max_net
        results = await self.ll2_request(
            self.ll2_launch_url % max_net.strftime('%Y-%m-%dT%H:%M:%SZ')
        )
        if results is None:
            return {}

        # Storage dict for returning
        launches: dict[str, Item] = {}

        # Go through data
        for entry in results:
            # Start datetime of the entry
            net = datetime.fromisoformat(entry['net'])

            # Name formatting
            if (net_precision := entry['net_precision']) is not None:
                # Name with NET precision
                name = net.strftime(
                    self.net_precision_formats.get(net_precision['id'], '')
                ) + entry['name']
            else:
                # Name with potential [TBD] (To Be Determined) prefix
                name = entry['name'] if entry['status']['id'] != 2 else '[TBD] ' + entry['name']

            # Check for videos
            priority = None
            picked_video = None
            for url in entry['vid_urls']:
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
            if ((image := entry['image']) is None or
                    (image_url := image['image_url']) and
                    not image_url.lower().endswith(self.image_formats)):
                image_url = None

            # Adding event to launches list
            launches[entry['id']] = {
                'name': name,
                'description': description,
                'url': picked_video,
                'image_url': image_url,
                'start': net,
                'end': net + self.event_duration['default'],
                'location': entry['pad']['location']['name'],
                'webcast_live': entry['webcast_live'],
                'slug': entry['slug'],
                'agency_id': entry['launch_service_provider']['id'],
                'agency_name': entry['launch_service_provider']['name'],
                'status': entry['status']['id'],
                'flightclub': bool(entry['flightclub_url'])
            }

        # Returning
        return launches

    async def upcoming_events(
        self
    ) -> dict[str, Item]:
        """
        Gets data of upcoming events.

        Returns
        -------
        streams : dict[str, Item]
            Dictionairy with the event name, webcast_live,
            mission description, net time, video URL and LL2 ID.
        """
        # Request data
        max_net = datetime.now(timezone.utc) + self.timedelta_max_net
        results = await self.ll2_request(
            self.ll2_event_url % max_net.strftime('%Y-%m-%dT%H:%M:%SZ')
        )
        if results is None:
            return {}

        # Storage dict for returning
        events: dict[str, Item] = {}

        # Go through data
        for entry in results:
            # Start datetime of the entry
            net = datetime.fromisoformat(entry['date'])

            # Name formatting
            if (net_precision := entry['date_precision']) is not None:
                # Name with NET precision
                name = net.strftime(
                    self.net_precision_formats.get(net_precision['id'], '')
                ) + entry['name']
            else:
                name = '[TBD] ' + entry['name']

            # Default duration if event type is not known
            event_type = entry['type']['name']
            if not event_type in self.event_duration:
                event_type = 'default'

            # Duration timedelta using potential duration
            if (duration := entry['duration']) is not None:
                duration = parse_duration(duration)
            else:
                duration = self.event_duration[event_type]

            # Check for videos
            priority = None
            picked_video = None
            for url in entry['vid_urls']:
                # Find lowest priority value
                if priority is None or url['priority'] < priority:
                    priority = url['priority']
                    picked_video = url['url']

            # Check description length and trim if needed
            if ((description := entry['description']) is not None
                    and len(description) > self.max_description_length):
                description = description[:self.max_description_length-3] + '...'

            # Image format check
            if ((image := entry['image']) is None or
                    (image_url := image['image_url']) and
                    not image_url.lower().endswith(self.image_formats)):
                image_url = None

            # Adding event to events list
            events[str(entry['id'])] = {
                'name': name,
                'description': description,
                'url': picked_video,
                'image_url': image_url,
                'start': net,
                'end': net + duration,
                'location': entry['location'],
                'webcast_live': entry['webcast_live'],
                'slug': entry['slug'],
                'flightclub': False
            }

        # Returning
        return events

    async def upcoming(
        self
    ) -> dict[str, Item]:
        """
        Gets data of upcoming events and launches.

        Returns
        -------
        streams : dict[str, Item]
            Dictionairy with the event name, webcast_live,
            mission description, net time, video URL and LL2 ID.
        """
        launches = await self.upcoming_launches()
        events = await self.upcoming_events()

        # Only return when there are both launches and events
        if not ( launches and events ):
            return {}

        # Combine launches and events
        upcoming = launches | events  # type: ignore

        # Sort by start datetime and limit it to `.max_events` items
        upcoming: dict[str, Item] = dict(
            sorted(  # type: ignore
                upcoming.items(), key=lambda item: item[1]['start']  # type: ignore
            )[:self.max_events]
        )

        # Update cache
        self.cache = upcoming

        # Returning
        return upcoming
