# Role link

This system allows you to create dependencies between roles and thus manage automatically the gain/withdrawal of roles according to the acquisition or loss of other roles. To create a link between roles, you will need to perform the command:

`/rolelink add <action> <target_role> when <trigger> <tigger_roles>`

Where

* `<action>` can take the value `grant` or `revoke`.
* `<target_role>` is the ID or mention of the role that will be given/removed automatically.
* `<trigger>` corresponds to the trigger for the action, which can take the value `get-one`, `get-all`, `loose-one` or `loose-all`.
* `<trigger_roles>` is the list of roles targeted by the trigger.

To see the list of links between roles, you can enter the command :

`/rolelink list`

To remove one of them, you can simply do:

`/rolelink remove <ID>`

Where `<ID>` is the number present in front of the corresponding role links in the link list.
