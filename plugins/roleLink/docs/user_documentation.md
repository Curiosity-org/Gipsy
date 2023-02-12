<!--
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
-->

# 📎 Role link

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

```{admonition} 🤝 Help us to improve this documentation!
:class: tip

If you want to help us to improve this documentation, you can edit it on the [GitHub repo](https://github.com/Gunivers/Gipsy/) or come and discuss with us on our [Discord server](https://discord.gg/E8qq6tN)!
```