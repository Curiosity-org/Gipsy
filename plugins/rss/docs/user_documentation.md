# RSS

Gipsy offers you the possibility to follow different content sources, from social networks like Youtube or Twitter to simple blogs equipped with an RSS feed system.

## **Add or remove a feed**

```
rss add <link>
```

where `<link>` is the link to the source of the content. If it's a social network account, put e link to the main page of the account (because it's the only one that shows account ID correctly in the URL). If it is a blog, forum or other soruce with an RSS feed, simply add the link to the RSS feed.

To remove a feed:

```
rss remove <id>
```

Where `<id>` is the number of the feed you will find in the feed list.

## **See feed list**

```
rss list
```

## **Move a feed to another room**.

```
rss move <id> <channel>
```

Where `<id>` is the number of the feed you will find in the feed list, and `<channel>` is the lounge you want to move it to.

## **Mention a role when content appears**

```
rss roles
```

Will run a script that will guide you through making changes.

```
rss mentions <id> <role1> [role2] [role3] ...
```

Will directly modify the feed to mention the filled-in roles

## **Change the text of an rss feed**

```
rss text <id> <text>
```

Modifies the text of the feed. Several variables can be used in the text:

* `{author}` : the author of the post
* `{channel}` : the name of the channel
* `{date}` : the date of publication of the post (UTC)
* `{link}` or `{url}` : the link to the post
* `{logo}` : an emoji representing the type of post (web, Twitter, YouTube...)
* `{mentions}` : the list of roles mentioned
* `{title}` : the title of the post

You can also use the command

```
rss text
```

Which will run a guided script, similar to the rss roles command.

## **Test if the feed is working properly**

```
rss test <link>
```

Where link is the link to the rss feed or the social network account.

## **Use embeds to display content**

```
rss embed <id> <true/false>
```

Enables/disables embeds for the specified feed.

```
rss embed 6678466620137 true title="hey u" footer = "Hi \nI'm a footer"
```

Changes the content of the embed for the specified feed. You can also use variables, like the `rss text` command.
