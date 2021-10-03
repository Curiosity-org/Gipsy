# Contact

With this bot, you can create a room in your server where your members can contact the staff. The bot will then create a private room, visible only to said member and your staff, and delete the original message to keep the room clean.
A command also exists to delete contact rooms older than X days.

Three configuration options exist for this module:

* `contact_category` : The category in which the private room will be created
* `contact_channel` : The channel your members can access to start the process
* `contact_roles` : The roles that will have access to the private contact rooms

It is your duty to make sure that the bot can read the contact channel, and create the contact categories with the necessary permissions. Without this, nothing will happen.

The bot will send the message posted by the user back to his private room, if possible as a webhook with the user's name and avatar.

The command to semi-automatically clean up contact rooms is `contact-clear`. You can specify a minimum number of days of inactivity, by default 15: the bot will then look if the last message posted is old enough before deleting the room.
