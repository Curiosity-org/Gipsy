# Create a configuration variable

In the `config/options.json` file, define your configuration variable like this:
```json
{
    "foo": {
        "default": "bar",
        "type": "text",
        "command": "foo"
    }
}
```
> __Note:__ the type can be either:
* text
* int
* float
* channels
* categories


> __Note:__ by convention, the name of the configuration variable and the name of the associated command are the same.

Just write a commande that will edit this config:
```python
@commands.command(name="foo") # tell to nextcord.py that the next function is a discord command
async def foo(self, ctx: MyContext, *, bar):
    await ctx.send(await self.bot.sconfig.edit_config(self, ctx.guild.id, "foo", bar)) # It will edit the config and send a confirmation message
```


In the `__init__` function of you main plugin class, link your
```python
bot.get_command("config").add_command(self.foo) # tell to nextcord.py that the command we defined is actually a sub-command of the "config" command
```