<!--
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
-->

# 🔐 Permissions

This plugin allows you to see the permissions of a role or a member in a given context (the guild globally or a channel specifically).

`!perms [<channel>] <target>`

Where

* `[<channel>]` indicates the channel for which the permissions will be displayed.
  If ignored, the permissions for the server as a whole will be displayed.
* `<target>` indicates the user for which to display permissions.
  If ignored, displays the permissions of the user using the command.

To display its own global permissions, the command `!perms` can simply be used.

To see the permissions of the user `@ascpial` in the `#gipsy` channel, you could use the command `!perms #gipsy @ascpial`.