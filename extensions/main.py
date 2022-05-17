import aiohttp
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks
from discord.ui import Button, MessageComponents
from discord.utils import _bytes_to_base64_data
from itertools import compress
import logging
from operator import itemgetter
import re

from bin import (
    LaunchLibrary2 as ll2,
    NASATV,
    NotificationCheck,
    YouTubeAPI,
    YouTubeRSS,
    YouTubeStripVideoID
)

class LiveLaunch(commands.Cog):
    """
    Discord.py cog for reporting live launches.
    """
    def __init__(self, bot):
        self.bot = bot
        #### Settings ####
        # Scheduled event base url
        self.se_url = 'https://discord.com/events/%s/%s'
        # datetime accuracy
        self.timedelta_1m = timedelta(minutes=1)
        self.timedelta_1h = timedelta(hours=1)
        # Launch Library 2
        self.ll2 = ll2()
        # NASA
        self.nasa_id = 'UCLA_DiR1FfKNvjuUpBHmylQ'
        self.nasa_name = 'NASA'
        self.nasatv = NASATV()
        # Notification check object
        self.notification_check = NotificationCheck()
        # YouTube API
        self.ytapi = YouTubeAPI()
        # YouTube RSS
        self.ytrss = YouTubeRSS()
        # YouTube regex for stripping IDs from URLs
        self.ytid_re = YouTubeStripVideoID()
        # YouTube base url for videos
        self.yt_base_url = 'https://www.youtube.com/watch?v='
        # Regex check for type checking
        self.type_check = re.compile('^[0-9]+$')
        # Itemgetter object for getting notification button settings
        self.button_settings = itemgetter(
            'button_sln',
            'button_g4l',
            'button_fc'
        )
        #### Start service ####
        # Start loops
        self.update_variables.start()
        self.check_ll2.start()
        self.check_rss.start()

    async def send_webhook_message(self, sending: list[dict[str, str]]) -> None:
        """
        Sends all streams within the sending list.

        Parameters
        ----------
        sending : list[dict[str, str]]
            List containing dictionaries of the
            streams that need to be sent.
            - Mandatory keys:
                - ` avatar ` : str
                    Avatar URL.
                - ` channel ` : str
                    Channel name.
                - ` yt_vid_id ` : str
                    YouTube video ID.
                - ` agency_id ` : int
                    Agency ID.
            - Optional key:
                - ` embed ` : discord.Embed
                    Embed to send for
                    NASA TV streams.
        """
        async for guild_id, webhook_url in self.bot.lldb.enabled_guilds_webhook_iter():

            # Check if the agencies are being filtered
            if not any(
                filters := [
                    await self.bot.lldb.ll2_agencies_filter_check(guild_id, i['agency_id'])
                    if i['agency_id']
                    else True
                    for i in sending
                ]
            ):
                continue

            try:
                # Creating session
                async with aiohttp.ClientSession() as session:
                    # Creating webhook
                    webhook = discord.Webhook.from_url(
                        webhook_url,
                        session=session
                    )

                    # Sending streams
                    for send in compress(sending, filters):
                        await webhook.send(
                            self.yt_base_url + send['yt_vid_id'],
                            username=send['channel'],
                            avatar_url=send['avatar']
                        )

            # Remove channel and url from the db when either is removed or deleted
            except discord.errors.NotFound:
                await self.bot.lldb.enabled_guilds_edit(
                    guild_id,
                    channel_id=None,
                    webhook_url=None
                )
                logging.warning(f'Guild ID: {guild_id}\tRemoved webhook, not found.')
            # When the bot fails (edge case)
            except Exception as e:
                logging.warning(f'Guild ID: {guild_id}\tError during webhook sending: {e}, {type(e)}')
                print(f'Guild ID: {guild_id}\tError during webhook sending: {e}, {type(e)}')

        # Sending complete, add streams to the database to prevent sending it again
        for send in sending:
            await self.bot.lldb.sent_media_add(yt_vid_id=send['yt_vid_id'])

    def create_scheduled_event(
        self,
        guild_id: int,
        name: str,
        description: str,
        url: str,
        start: datetime,
        end: datetime,
        webcast_live: bool = False,
        image: bytes = None,
        **kwargs
    ) -> dict[str, int and str]:
        """
        Create a Discord scheduled event
        at an external location.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        name : str
            Name of the event.
        description : str
            Description of the event.
        url : str
            External location of the event.
        start : datetime
            Start datetime of the event, if
            given, end must also be given.
        end : datetime
            End datetime of the event, if
            given, start must also be given.
        webcast_live : bool, default: False
            Start the Discord event.
        image : bytes, default: None
            Event cover image.
        **kwargs

        Returns
        -------
        dict[str, int and str]
            Created Discord scheduled
            event data object.

        Notes
        -----
        The following parameters are locked:
        privacy_level : int, default: 2
            Privacy of the scheduled event:
                ` 1 `: PUBLIC (unkown, guess)
                ` 2 `: GUILD_ONLY
        entity_type : int, default: 3
            Type of location, only external
            is currently supported:
                ` 1 `: STAGE_INSTANCE
                ` 2 `: VOICE
                ` 3 `: EXTERNAL
        """
        # Insert a replacement string when there is no stream URL
        if url is None:
            url = ll2.no_stream
        # Replace start with now + `.timedelta_1m` if `webcast_live`
        if webcast_live:
            start = datetime.now(timezone.utc) + self.timedelta_1m
        # Convert image bytes to base64
        if image:
            image = _bytes_to_base64_data(image)
        # Return creation coroutine
        return self.bot.http.create_guild_scheduled_event(
            guild_id,
            {
                'name': name, 'privacy_level': 2,
                'scheduled_start_time': start.isoformat(),
                'scheduled_end_time': end.isoformat(),
                'description': description, 'entity_type': 3,
                'entity_metadata': {'location': url},
                'image': image
            }
        )

    def modify_scheduled_event(
        self,
        guild_id: int,
        scheduled_event_id: str = None,
        name: str = None,
        description: str = None,
        url: str = None,
        image: bytes = None,
        start: datetime = None,
        end: datetime = None,
        webcast_live: bool = False,
        **kwargs
    ) -> dict[str, int and str]:
        """
        Update a Discord scheduled event
        at an external location.

        Parameters
        ----------
        guild_id : int
            Discord guild ID.
        scheduled_event_id : int
            Discord scheduled event ID.
        name : str, default: None
            Name of the event.
        description : str, default: None
            Description of the event.
        url : str, default: None
            External location of the event.
        image : bytes, default: None
            Event cover image.
        start : datetime, default: None
            Start datetime of the event, if
            given, end must also be given.
        end : datetime, default: None
            End datetime of the event, if
            given, start must also be given.
        webcast_live : bool, default: False
            Start the Discord event.
        **kwargs

        Returns
        -------
        dict[str, int and str]
            Modified Discord scheduled
            event data object.
        """
        # Empty payload
        payload = {}
        # Add given variables to the payload
        if name is not None:
            payload['name'] = name
        if description is not None:
            payload['description'] = description
        if url is not None:
            payload['entity_metadata'] = {'location': url}
        if image is not None:
            payload['image'] = _bytes_to_base64_data(image)
        if start is not None and not webcast_live:
            payload['scheduled_start_time'] = start.isoformat()
        if end is not None:
            payload['scheduled_end_time'] = end.isoformat()
        if webcast_live:
            payload['status'] = 2
        # Modify
        return self.bot.http.modify_guild_scheduled_event(
            guild_id,
            scheduled_event_id,
            payload
        )

    async def scheduled_events_update(
        self,
        ll2_id: str,
        *,
        cached: dict[str, bool and datetime and int and str],
        check: dict[str, bool or datetime or int or str]
    ) -> None:
        """
        Update scheduled events when any
        changes appear to upcoming events.

        Parameters
        ----------
        ll2_id : str
            Launch Library 2 ID.
        cached: dict[
            str, bool and datetime and int and str
        ]
            Cached data for the event.
        check : dict[
            str, bool or datetime or int or str
        ]
            Data from events that changed.
        """
        failed = False

        # Downloading image
        if (image_url := check.get('image_url')):
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        check['image'] = await resp.read()

        # Iterate over scheduled events corresponding to the ll2_id
        async for scheduled_event_id, guild_id in self.bot.lldb.scheduled_events_ll2_id_iter(ll2_id):

            # webcast_live went from True to False, remove event
            if check.get('webcast_live') is False:
                try:
                    # Remove the scheduled event from Discord
                    await self.bot.http.delete_guild_scheduled_event(
                        guild_id,
                        scheduled_event_id
                    )
                except:
                    pass
                # Remove scheduled event from the database
                await self.bot.lldb.scheduled_events_remove(
                    scheduled_event_id
                )

            # Updating
            else:

                # Seperate dict for updating Discord & database for next if statement
                modify = check.copy()

                if (start := check.get('start')):

                    # If `start` changed to a datetime in the past
                    if start < (now := datetime.now(timezone.utc) + self.timedelta_1m):
                        # Remove `start` value from the modify dict, can't update
                        del modify['start']
                        # Start event if it hasn't yet
                        if cached['start'] > now:
                            modify['webcast_live'] = True

                    # If `start` moved forward while the event is live
                    elif cached['webcast_live'] or cached['start'] < now:
                        if start > now + self.timedelta_1h:

                            try:
                                # Remove the scheduled event from Discord
                                await self.bot.http.delete_guild_scheduled_event(
                                    guild_id,
                                    scheduled_event_id
                                )
                            except:
                                pass

                            # Remove scheduled event from the database
                            await self.bot.lldb.scheduled_events_remove(
                                scheduled_event_id
                            )

                            # Skip updating, event is removed
                            continue

                        # Remove `start` value from the modify dict, new start isn't too far from current
                        del modify['start']

                # Insert a replacement string when there is no stream URL
                if check.get('url', False) is None:
                    modify['url'] = ll2.no_stream

                remove_event = False
                try:
                    await self.modify_scheduled_event(
                        guild_id,
                        scheduled_event_id,
                        **modify
                    )
                except (discord.errors.Forbidden, discord.errors.NotFound):
                    # When missing access or already removed event
                    remove_event = True
                except Exception as e:
                    str_e = str(e)
                    # Wrong permissions
                    if '50013' in str_e:
                        remove_event = True
                    else:
                        failed = True
                        logging.warning(
                            f'LL2 ID: {ll2_id}\tGuild ID: {guild_id}\t' \
                            f'Modify failure: {e} {type(e)}'
                        )
                        print('Modify failure:', e, type(e))
                if remove_event:
                    # Remove scheduled event from the database
                    await self.bot.lldb.scheduled_events_remove(
                        scheduled_event_id
                    )

        # Update cache
        if not failed:
            await self.bot.lldb.ll2_events_edit(
                ll2_id,
                **check
            )

    async def scheduled_events_remove(self, ll2_id: str) -> None:
        """
        Remove a scheduled event in
        all Discord guilds.

        Parameters
        ----------
        ll2_id : str
            Launch Library 2 ID.

        Returns
        -------
        status : bool
            Whether or not the deletion of
            all Discord events went well.
        """
        status = True

        # Iterate over scheduled events corresponding to the ll2_id
        async for scheduled_event_id, guild_id in self.bot.lldb.scheduled_events_ll2_id_iter(ll2_id):
            success = True
            try:
                # Remove the scheduled event from Discord
                await self.bot.http.delete_guild_scheduled_event(
                    guild_id,
                    scheduled_event_id
                )
            except (discord.errors.Forbidden, discord.errors.NotFound):
                # When missing access or already removed event
                pass
            except Exception as e:
                # Wrong permissions
                if not '50013' in str(e):
                    success = False
                    status = False
                    logging.warning(
                        f'LL2 ID: {ll2_id}\tGuild ID: {guild_id}\t' \
                        f'Removal failure: {e} {type(e)}'
                    )
                    print('Removal failure:', e, type(e))
            if success:
                # Remove scheduled event from the database
                await self.bot.lldb.scheduled_events_remove(
                    scheduled_event_id
                )

        # Return overall success status
        return status

    async def send_notification(
        self,
        notification_type : int,
        *,
        ll2_id: str,
        data: dict[str, bool and datetime and int and str],
        cached_start: datetime = None
    ) -> None:
        """
        Send a notification when called, uses the
        provided data to create the notification
        embed and sends it to all guilds that enabled
        the type within their settings.

        Parameters
        ----------
        notification_type : int
            0 : Status notifications only.
            1 : T-0 change notifications only.
            2 : Both notification types.
        ll2_id : str
            Launch Library 2 ID.
        data : dict[
            str, bool and datetime and int and str
        ]
            Data of the event.
        cached_start : datetime, default: None
            Previous start datetime.
        """
        async def send(
            embed: discord.Embed,
            buttons: dict[str, MessageComponents],
            kwargs: dict[str, bool or int and str]
        ) -> None:
            """
            Send notifications depending on the type.

            Parameters
            ----------
            embed : discord.Embed
                Embed object to send.
            buttons : dict[str, Button]
                Buttons to external sites:
                    ` fc `: FC button.
                    ` g4l `: G4L button.
                    ` sln `: SLN button.
            kwargs : dict[str, bool or int and str]
                Iteration kwargs.
            """
            # Iterate over guilds that enabled the notification type
            async for notification in self.bot.lldb.notification_iter(**kwargs):
                guild_id = notification['guild_id']
                scheduled_event_id = notification['scheduled_event_id']

                # Scheduled event
                message = {}
                if scheduled_event_id:
                    message['content'] = self.se_url % (
                        guild_id,
                        scheduled_event_id
                    )

                # Add correct buttons
                if any(button_settings := self.button_settings(notification)):
                    message['components'] = MessageComponents.add_buttons_with_rows(
                        *compress(buttons, button_settings)
                    )

                try:
                    # Creating session
                    async with aiohttp.ClientSession() as session:
                        # Creating webhook
                        webhook = discord.Webhook.from_url(
                            notification['notification_webhook_url'],
                            session=session
                        )

                        # Sending notification
                        await webhook.send(
                            **message,
                            embed=embed,
                            username=agency,
                            avatar_url=logo_url
                        )

                # Remove channel and url from the db when either is removed or deleted
                except discord.errors.NotFound:
                    await self.bot.lldb.enabled_guilds_edit(
                        guild_id,
                        notification_channel_id=None,
                        notification_webhook_url=None
                    )
                    logging.warning(f'Guild ID: {guild_id}\tRemoved notification webhook, not found.')
                # When the bot fails (edge case)
                except Exception as e:
                    logging.warning(f'Guild ID: {guild_id}\tError during notification webhook sending: {e}, {type(e)}')
                    print(f'Guild ID: {guild_id}\tError during notification webhook sending: {e}, {type(e)}')

        # Kwargs dict and get status
        kwargs = {'ll2_id': ll2_id}
        status = data.get('status')

        # Only enable video URL when available
        if (url := data['url']):
            title_url = {'url': url}
            url = f'[Stream]({url})'
        else:
            title_url = {}
            url = ll2.no_stream

        # Select the correct G4L and SLN base URL
        if self.type_check.match(ll2_id):
            g4l_url = ll2.g4l_event_url
            sln_url = ll2.sln_event_url
            kwargs['event'] = True
        else:
            g4l_url = ll2.g4l_launch_url
            sln_url = ll2.sln_launch_url
            kwargs['launch'] = True

        # FC, G4L and SLN buttons for the event
        buttons = []
        # Add SLN button
        buttons.append(
            Button(
                label=ll2.sln_name,
                style=discord.ButtonStyle.link,
                emoji=ll2.sln_emoji,
                url=sln_url % data['slug']
            )
        )
        # Add G4L button
        buttons.append(
            Button(
                label=ll2.g4l_name,
                style=discord.ButtonStyle.link,
                emoji=ll2.g4l_emoji,
                url=g4l_url % ll2_id
            )
        )
        # Add FC button
        buttons.append(
            Button(
                label=ll2.fc_name,
                style=discord.ButtonStyle.link,
                emoji=ll2.fc_emoji,
                url=ll2.fc_url % ll2_id
            )
        )

        # Get the agency's name and logo
        if (agency := await self.bot.lldb.ll2_agencies_get(ll2_id)):
            agency, logo_url = agency
        else:
            agency, logo_url = None, None

        # Creating embed
        embed = discord.Embed(
            color=ll2.status_colours.get(status, 0xFFFF00),
            timestamp=data['start'],
            title=data['name'],
            **title_url
        )
        # Set thumbnail
        if data['image_url']:
            embed.set_thumbnail(
                url=data['image_url']
            )
        # Set footer
        embed.set_footer(
            text='LiveLaunch Notifications'
        )

        # Status change
        if notification_type != 1:
            # Reference or shallow copy
            status_embed = embed.copy() if notification_type == 2 else embed
            # Set description
            status_embed.description = f'**New status:** {ll2.status_names[status]}\n{url}'

            # Send notifications
            if notification_type == 0:
                await send(status_embed, buttons, {'ll2_id': ll2_id, 'status': status})
            else:
                # Add status to the kwargs
                kwargs['status'] = status

        # T-0 change
        if notification_type != 0:
            # Reference or shallow copy
            t0_embed = embed.copy() if notification_type == 2 else embed
            # Set description
            t0_embed.description = f'**T-0** changed from <t:{int(cached_start.timestamp())}:F>' \
                f" to <t:{int(data['start'].timestamp())}:F>\n" + \
                (f'**Status:** {ll2.status_names[status]}\n{url}' if status else url)

            # Send notifications
            if notification_type == 1:
                await send(t0_embed, buttons, kwargs)

        # Both T-0 change and status change
        if notification_type == 2:
            # Set description
            embed.description = f'**T-0** changed from <t:{int(cached_start.timestamp())}:F>' \
                f" to <t:{int(data['start'].timestamp())}:F>\n" + \
                (f'**New status:** {ll2.status_names[status]}\n{url}' if status else url)

            # Send to servers with both T-0 and status change
            await send(embed, buttons, kwargs)

            # Send to servers with status change, but not T-0 change
            kwargs['no_t0'] = True
            await send(status_embed, buttons, kwargs)

            # Send to servers with T-0 change, but not status change
            kwargs.pop('no_t0')
            kwargs['no_status'] = True
            await send(t0_embed, buttons, kwargs)

    @tasks.loop(hours=1)
    async def update_variables(self):
        """
        Discord task for getting new NASA TV streams.
        """
        self.nasatv.update()

    @tasks.loop(minutes=3)
    async def check_ll2(self):
        """
        Discord task for checking the Launch Library 2 API.

        Notes
        -----
        Makes or updates Discord scheduled events and
        sends webhook messages of the livestream URL.
        """
        # Get upcoming launches and events from the LL2 API
        upcoming = await self.ll2.upcoming()

        # No data, return
        if not upcoming:
            print('No LL2 Data')
            return

        #### Discord scheduled events & notifications ####
        # Iterate over the cached LL2 events
        cached_ll2_events = []
        async for cached in self.bot.lldb.ll2_events_iter():
            ll2_id = cached['ll2_id']
            cached_ll2_events.append(ll2_id)

            ## Update LL2 event data ##

            # Check if the event still exists
            if data := upcoming.get(ll2_id):

                # Now datetime for checks
                now = datetime.now(timezone.utc)

                # Scheduled event check
                scheduled_event_check = data['end'] > now \
                    and data.get('status') not in self.ll2.launch_status_end

                # Check for updates to the event
                check = {key: data.get(key) for key in self.ll2.data_keys if data.get(key) != cached[key]}

                # Update agency data
                if (agency_id := check.get('agency_id')):
                    # Update agencies table
                    await self.bot.lldb.ll2_agencies_replace(
                        agency_id,
                        data['agency_name']
                    )
                    # Update events table
                    await self.bot.lldb.ll2_events_edit(
                        ll2_id,
                        agency_id=agency_id
                    )
                    # Done
                    check.pop('agency_id')

                # Update flightclub boolean
                if (flightclub := check.get('flightclub')):
                    # Update events table
                    await self.bot.lldb.ll2_events_edit(
                        ll2_id,
                        flightclub=flightclub
                    )
                    # Done
                    check.pop('flightclub')

                # Get current and possible new status
                old_status = cached.get('status')
                new_status = check.get('status', old_status)
                # Get current start time
                cached_start = cached['start']
                # Get the notifications types for these statuses
                notification_type = self.notification_check(
                    old_status=old_status,
                    new_status=new_status,
                    old_start=cached_start,
                    new_start=check.get('start')
                )

                # Check for notifications
                if notification_type is not None:
                    # Status only or both (0, 2)
                    if notification_type != 1:
                        # Update events table
                        await self.bot.lldb.ll2_events_edit(
                            ll2_id,
                            status=new_status
                        )
                        # Done
                        check.pop('status')

                    # Send notifications
                    await self.send_notification(
                        notification_type,
                        ll2_id=ll2_id,
                        data=data,
                        cached_start=cached_start
                    )

                # Check for scheduled event relevance
                if scheduled_event_check:
                    # If there are any more updates, update the scheduled events
                    if check:
                        await self.scheduled_events_update(
                            ll2_id,
                            cached=cached,
                            check=check
                        )
                # Removal of existing scheduled events
                else:
                    await self.scheduled_events_remove(ll2_id)

            # Cached event no longer exists
            else:
                # Remove Discord events
                if await self.scheduled_events_remove(ll2_id):
                    # Remove from the database
                    await self.bot.lldb.ll2_events_remove(ll2_id)

        ## Creation of new scheduled events ##

        # New events, not cached yet
        new_ll2_events = upcoming.keys() - cached_ll2_events

        # Add new events to the database
        for ll2_id in new_ll2_events:
            # Update agency if needed
            if (agency_id := upcoming[ll2_id].get('agency_id')):
                await self.bot.lldb.ll2_agencies_replace(
                    agency_id,
                    name=upcoming[ll2_id]['agency_name']
                )
            # Add event
            await self.bot.lldb.ll2_events_add(
                ll2_id,
                **upcoming[ll2_id]
            )

        # Asking the database for Guilds that need new events
        async for row in self.bot.lldb.scheduled_events_remove_create_iter():

            # Create wanted Launch Library 2 as Discord scheduled events
            if row['create_remove']:

                # Downloading image
                if (upcoming[row['ll2_id']].get('image') is None
                        and (image_url := upcoming[row['ll2_id']].get('image_url'))):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            if resp.status == 200:
                                upcoming[row['ll2_id']]['image'] = await resp.read()

                reset_settings = False
                try:
                    # Create Discord scheduled event
                    new_event = await self.create_scheduled_event(
                        row['guild_id'],
                        **upcoming[row['ll2_id']]
                    )
                except (discord.errors.Forbidden, discord.errors.NotFound):
                    # When missing access or already removed event
                    reset_settings = True
                except Exception as e:
                    # Wrong permissions
                    if '50013' in str(e):
                        reset_settings = True
                    else:
                        logging.warning(f'Creation failure in iter: {e} {type(e)}')
                        print('Creation failure in iter:', e, type(e))
                else:
                    # Add scheduled event to the database
                    await self.bot.lldb.scheduled_events_add(
                        new_event['id'],
                        row['guild_id'],
                        row['ll2_id']
                    )
                # Guild has kicked or removed permissions, turn events off
                if reset_settings:
                    # Set amount of events to 0
                    await self.bot.lldb.enabled_guilds_edit(
                        row['guild_id'],
                        scheduled_events=0
                    )

            # Remove unwanted Discord scheduled events
            else:
                removed = True
                try:
                    # Remove the scheduled event from Discord
                    await self.bot.http.delete_guild_scheduled_event(
                        row['guild_id'],
                        row['scheduled_event_id']
                    )
                except (discord.errors.Forbidden, discord.errors.NotFound):
                    # When missing access or already removed event
                    pass
                except Exception as e:
                    # Wrong permissions
                    if not '50013' in str(e):
                        removed = False
                        logging.warning(f'Removal failure in iter: {e} {type(e)}')
                        print('Removal failure in iter:', e, type(e))
                if removed:
                    # Remove scheduled event from the database
                    await self.bot.lldb.scheduled_events_remove(
                        row['scheduled_event_id']
                    )

        #### Sending streams using webhooks ####

        # Go through upcoming streams for webhook sending
        sending = []
        for ll2_id, data in upcoming.items():
            # Add stream if it is within 1 hour to the sending list
            now = datetime.now(timezone.utc)
            if abs(data['start'] - now) < timedelta(hours=1) and data['url']:
                # Check if the stream is on YouTube and not a NASA TV stream
                yt_vid_id = self.ytid_re(data['url'])
                if yt_vid_id and self.yt_base_url + (yt_vid_id := yt_vid_id[0]) not in self.nasatv:
                    # Only send streams that aren't sent already
                    if not await self.bot.lldb.sent_media_exists(yt_vid_id=yt_vid_id):

                        # Get YouTube channel
                        channel = self.ytapi.get_channel_from_video(yt_vid_id)
                        # Get YouTube channel name and avatar
                        thumb, title = self.ytapi.get_channel_thumbtitle(channel)

                        # Adding to the sending list
                        sending.append(
                            {
                                'avatar': thumb,
                                'channel': title,
                                'yt_vid_id': yt_vid_id,
                                'agency_id': data.get('agency_id')
                            }
                        )

        if sending:
            # Send streams
            await self.send_webhook_message(sending)

        #### Cleaning up database ####
        # Remove all disabled Guilds from the database
        await self.bot.lldb.enabled_guilds_clean()

    @tasks.loop(minutes=1)
    async def check_rss(self):
        """
        Discord task for checking the YouTube RSS feed.
        """
        # Storage list of streams to send
        sending = []

        # Check if there are any streams
        streams = await self.ytrss.request()

        # Iterate over dictionary to see which streams needs to be sent
        for channel in streams:
            # Check if the channel has any streams
            if streams[channel]:
                # Iterate through the streams of a channel
                for yt_vid_id in streams[channel]:
                    # Only send streams that aren't sent already
                    if not await self.bot.lldb.sent_media_exists(yt_vid_id=yt_vid_id):

                        # Get YouTube channel name and avatar
                        thumb, title = self.ytapi.get_channel_thumbtitle(channel)

                        # Adding to the sending list
                        sending.append(
                            {
                                'avatar': thumb,
                                'channel': title,
                                'yt_vid_id': yt_vid_id,
                                'agency_id': self.ytrss.agency_ids.get(channel)
                            }
                        )

        if sending:
            # Send streams
            await self.send_webhook_message(sending)

    @check_ll2.before_loop
    @check_rss.before_loop
    async def before_loop(self):
        """
        Wait untill the database is loaded.
        """
        await self.bot.wait_until_ready()


def setup(client):
    client.add_cog(LiveLaunch(client))
