# LiveLaunch

Creates space related events and sends live streams!

[Add to Server](https://discord.com/api/oauth2/authorize?client_id=869969874036867082&permissions=17601312868352&scope=bot%20applications.commands)

## Features:
The events are created from Launch Library 2 launch and event data, events are automatically maintained by the bot by updating information, starting the event when the livestream goes live and ending it when the launch is a success or fails.

The messages are YouTube livestreams using webhooks so it looks like the actual YouTube channel send them.

The news articles are queried from the Spaceflight News API, the articles can be filtered by their respective news sites per guild.

Notifications can be set up to send custom countdowns or changes to launch statuses (liftoff, hold, success/failure/partial failure).
Even Discord events can be included within the countdown notifications.

## Options:
- Create events with a maximum of 50 using the events option.
- Send YouTube livestreams of launches and events to a channel using the messages option.
- Send Space related news articles and filter them by their respective news site.
- Receive notifications for countdowns, T-0 changes and/or launch status changes.

LiveLaunch can be enabled and disabled using slash commands.
