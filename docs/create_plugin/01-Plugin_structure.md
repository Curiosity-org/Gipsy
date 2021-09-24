# Plugin Structure

The plugin must respect this structure:
```
📁 <plugin_name>
├─ 📁 api
│  │  # plugin API (Python)
│  └─ 📄 /!\ The API feature is Work In Progress. The structure isn't yet totally defined.
├─ 📁 bot
│  │  # plugin actions files (Python)
│  ├─ 📄 main.py
│  └─ 📄 ...
├─ 📁 config
│  │  # plugin config files (JSON)
│  ├─ 📄 options.json
│  └─ 📄 ...
├─ 📁 data
│  │  # plugin database files (SQL)
│  ├─ 📄 model.sql
│  └─ 📄 ...
└─ 📁 docs
│  │  # plugin documentation files (Markdown)
│  ├─ 📄 user_documentation.md
│  └─ 📄 ...
├─ 📁 langs
│  │  # plugin language files (YML)
│  ├─ 📄 en.yml
│  ├─ 📄 fr.yml
│  └─ 📄 ...
└─ 📁 web
   │  # plugin web UI files (JS)
   └─ 📄 /!\ The web UI feature is Work In Progress. The structure isn't yet totally defined.
```

## Legend

* `bot/main.py` (the only required file) is the file that is used to lead the plugin as an extension of discord.py
* `option.json` is read by the bot to generate the configuration files (and will be used to generate a basic web UI)
* `models.sql` is automatically called when the bot start to create all tables needed by every plugin
* `user_documentation.md` will allow to your plugin to be listed in the auto-generated SUMMARY.md file (and so on gitlab pages if you use this feature)
* `fr.yml` and `en.yml` are both pre-implemented languages
* `📄 ...` mean that you are free to create every file or folders you want!