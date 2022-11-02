# Changelog

## 1.4

> **This version include breaking changes 💥**
> 
> If you host an instance of the bot, please read the [user migration guide](USER_MIGRATION_GUIDE.md)
>
> If you are a plugin developer, please read the [developer migration guide](DEV_MIGRATION_GUIDE.md) to update your plugins to the new structure

### ➕ Additions

- A fresh new setup script to drastically simplify to bot installation! 🎉
- `rolladice [faces]` command, which allow  you to generate a random number between 1 and `faces`. By Default, `faces = 6`. Command aliases: `dice`, `rad`, `🎲`
- `hs` command now support all channel types.
- `move` and `moveall` commands now support all messageable channels
- Possibility to exclude entire categories from XP gain
- Possibility to setup XP reduction to prevent long term AFK users to keep prestigious roles
- Wormholes now support bot messages. Only messages coming from the webhook used by the wormhole are excluded, to avoid message loops

### 🔀 Tweaks

- 💥 New plugin structure
- 💥 Complete refactor of the global config system
- Improved `help` command output
- Improved `flipacoin` command output
- Improved error messages
    - Now, when you enter a wrong command, the bot will try to send you the appropriate help message

### 🐛 Fixes

- Reply in wormholes now works properly

### 📝 Docs

- Added changelog, user migration guide and dev migration guide.
