<!--
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
-->

# Message manager

## Moving messages

Gunibot.py offers the possibility to manage messages by moving them to other rooms. To do this, you will need to perform the command:

`/move <Message> <Channel>`

Where `<Message>` can be replaced by the ID or link to a message, and `<Channel>` can be replaced by the ID or mention of the destination channel. It is also possible to move multiple messages at once by doing:

`/move <Message1> <Message2> <Channel>`

This will move all the messages copied between the two messages indicated. Make sure that these two messages are in the same channel, and that there are no more than 20 messages separating them (this limitation prevents the bot from being considered a spammer by Discord).

## Request to change room

If a discussion is rambling and no longer appropriate for the channel, you can send a message visible to everyone with the command: /hs `<Channel>`. The bot will then ask all participants to continue their discussion in the indicated channel, or to find a more appropriate one if you don't indicate one.
