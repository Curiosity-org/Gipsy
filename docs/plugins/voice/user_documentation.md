# Voice

## Automatic role giving

It is possible to automatically give a role to any member being in a voice room, and to remove them when this member is not in any voice room. To do this, you just have to configure the option `voice_roles` with the list of roles to give. As simple as that.

## Creation of rooms on demand

The bot also has a voice room creation feature: when a member enters a specific voice room, the bot creates a special one, gives the permissions to manage the room to that user, and then moves the user to that new room. It is possible to customize the name of this room, which by default will take a random name via an API.

Three options exist for this module:

* `voice_category` : The category where to create the voice rooms
* voice_channel` : The lobby where users must connect to trigger the procedure
* `voice_channel_format` : The format of the name of the created channels. Use `{random}` for a random name, `{asterix}` for a random name from the adventures of Asterix, or `{user}` for the user's name

It's up to you to make sure the bot has sufficient permissions to create the rooms and move members in them.
