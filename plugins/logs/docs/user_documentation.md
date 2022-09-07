# Log

This bot offers a log system for your server, which grows over time. So you can set up a room where you can send messages when a member leaves the server, when a message is deleted, when an invitation is created... and many other things.

For this, only two configurations are needed:

* `logs_channel`: The textual channel where to send logs
* `modlogs`: The list of active logs

To enable or disable a log category, the command is `config modlogs enable/disable <option>`. You can use the `config modlogs list` command to get a list of available categories.

Make sure the bot can send embeds to the log room. Also, some logs are only accessible under certain permissions: for example, the bot must have the `Manage Lounges` permission to send invitation creation logs.
