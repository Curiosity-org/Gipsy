# Welcome

## Verification system

The bot has a member verification system, where each newcomer will have to enter a key phrase that will give him access to the rest of the server.

The system is designed in such a way that the bot will only do three actions: send a message when the member joins the server, detect when the member sends the right keyphrase in the right room, and then give/remove the configured role by sending a confirmation message at the same time.

The configuration currently has 4 options:

* `verification_channel` : Channel in which the bot messages will be sent, and in which the member will have to send the keyphrase
* `verification_role` : Role given or removed to verified members
* `verification_add_role` : Boolean (true/false) indicating if the role should be given (true) or removed (false)
* `pass_message` : The phrase to enter to be verified

It is up to you to make sure that the unverified member can write in the verification room, and to configure your roles as you wish.

Other options will come later, like customizing the welcome message.

## Automatic roles

It is also possible to configure the bot to give a role to any newcomer, independently of the verification system detailed above. To do so, you just have to configure the `welcome_roles` option with the list of roles to give.
