# Dev migration guide

## Migrating 1.3 -> 1.4


## Global config
If your plugin were using config variable, it now must use the `core.config.get()` command in the cog class builder, such as:

```yaml
# in /plugins/foo/config.yaml
bar: "Hello World"
```

```python
# in /plugins/foo/foo.py
from utils import Gunibot
import core

async def setup(bot:Gunibot):
    await bot.add_cog(Foo(bot))

class Foo():
    def ___init__(self, bot:Gunibot):
        self.config = core.config.get("foo") # Get the plugin config
        print(self.config["bar"]) # Output: "Hello World"
```
⚠️ The capital letters are important here. The config variable must be named the same as the plugin folder.

This function return a doctionary containing the config information such as defined in the `/plugins/foo/config.yaml` file. This file must contains the default config for the plugin and will never be edited by the bot.

You can also, at any moment, use a path in the `core.config.get` function:
```python
res = core.config.get("foo.bar")
print(res) # Output: "Hello World"
```

## Plugin structure

The plugin structure has been completely refactored. The main goal was to simplify the plugin creation and the plugin management. The new structure:
    
```
/plugins/
    foo/
        config.yaml
        foo.py
        setup.py
        langs/
            en.yaml
            fr.yaml
            [...].yaml
        docs/
            [...].md
            [...].rst
```
- `config.yaml` must contain the default config for the plugin.
- `foo.py` must contain the cog class declaration and a `setup()` function.
- `setup.py` must contain the `run()` function which will be called by the global setup script to allow the user to configure the plugin. This function will have to return a dictionary containing the config for the plugin.

## Plugin emoji

You can now add a plugin emoji that will be diplayed in the `help` command. To do so, just add the `icon` keyword when you declare the cog:

```python
from utils import Gunibot

async def setup(bot:Gunibot):
    await bot.add_cog(Foo(bot), icon="👋")

class Foo():
    def ___init__(self, bot:Gunibot):
        [...]
```