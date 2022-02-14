import aiohttp
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks
from discord.utils import _bytes_to_base64_data
import logging

from bin import (
    LaunchLibrary2,
    NASATV,
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
        # datetime accuracy
        self.timedelta_1m = timedelta(minutes=1)
        self.timedelta_1h = timedelta(hours=1)
        # Launch Library 2
        self.ll2 = LaunchLibrary2()
        # NASA
        self.nasa_id = 'UCLA_DiR1FfKNvjuUpBHmylQ'
        self.nasa_name = 'NASA'
        self.nasatv = NASATV()
        # YouTube API
        self.ytapi = YouTubeAPI()
        # YouTube RSS
        self.ytrss = YouTubeRSS()
        # YouTube regex for stripping IDs from URLs
        self.ytid_re = YouTubeStripVideoID()
        # YouTube base url for videos
        self.yt_base_url = 'https://www.youtube.com/watch?v='
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
            - Optional key:
                - ` embed ` : discord.Embed
                    Embed to send for
                    NASA TV streams.
        """
        async for guild_id, webhook_url in self.bot.lldb.enabled_guilds_webhook_iter():
            try:
                # Creating session
                async with aiohttp.ClientSession() as session:
                    # Creating webhook
                    webhook = discord.Webhook.from_url(
                        webhook_url,
                        session=session
                    )

                    # Sending streams
                    for send in sending:
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
        if not name is None:
            payload['name'] = name
        if not description is None:
            payload['description'] = description
        if not url is None:
            payload['entity_metadata'] = {'location': url}
        if not image is None:
            payload['image'] = _bytes_to_base64_data(image)
        if not (start and end) is None:
            payload['scheduled_start_time'] = start.isoformat()
            payload['scheduled_end_time'] = end.isoformat()
        if webcast_live:
            payload['status'] = 2
        # Modify
        return self.bot.http.modify_guild_scheduled_event(
            guild_id,
            scheduled_event_id,
            payload
        )

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

        #### Discord scheduled events ####
        # Iterate over the cached LL2 events
        cached_ll2_events = []
        async for cached in self.bot.lldb.ll2_events_iter():
            ll2_id = cached['ll2_id']
            cached_ll2_events.append(ll2_id)

            # Failure bool
            failed = False

            ## Update existing scheduled events ##

            # Check if the event still exists
            if data := upcoming.get(ll2_id):

                # Check for updates to the event
                check = {key: data[key] for key in self.ll2.data_keys if data[key] != cached[key]}

                # If there are any updates
                if check:

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
                        # Remove image, not cached
                        check.pop('image', None)
                        await self.bot.lldb.ll2_events_edit(
                            ll2_id,
                            **check
                        )

            ## Removal of existing scheduled events ##

            # Cached event no longer exists
            else:

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
                            failed = True
                            success = False
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

                # Remove event from the cache
                if not failed:
                    await self.bot.lldb.ll2_events_remove(
                        ll2_id
                    )

        ## Creation of new scheduled events ##

        # New events, not cached yet
        new_ll2_events = upcoming.keys() - cached_ll2_events

        # Add new events to the database
        for ll2_id in new_ll2_events:
            await self.bot.lldb.ll2_events_add(
                ll2_id,
                **upcoming[ll2_id]
            )

        # Asking the database for Guilds that need new events
        async for row in self.bot.lldb.scheduled_events_remove_create_iter():

            # Create wanted Launch Library 2 as Discord scheduled events
            if row['create_remove']:

                # Downloading image
                if (upcoming[row['ll2_id']].get('image') is None and
                    (image_url := upcoming[row['ll2_id']].get('image_url'))):
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
            if data['start'] - now < timedelta(hours=1):
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
                                'yt_vid_id': yt_vid_id
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
                                'yt_vid_id': yt_vid_id
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