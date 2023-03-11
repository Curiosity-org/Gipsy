---
html_theme.sidebar_secondary.remove: true
---

# 🤝 Contribute

```{admonition} 🤝 Help us building this project!
:class: note

This part of the documentation is still under construction. If you want to help us, you can contribute to the project on [GitHub](https://github.com/Gunivers/Gipsy) or come on our [Discord server](https://discord.gg/E8qq6tN).
```

## Commit Message Format
We do not have a strict policy regarding commit messages, however we tend to apply a consistent style looking like this:
`:emote: [type](scope): <subject>`

*examples:*  `🪱 fix(all): fix some import errors`
            `🧱 deps: use discord.py 2.0`

### Emote
The emote should represent the commit you've made. For example, a commit which make the code looks prettier may use those emotes 🌟, 😍 or ✨.\
The emote choice is left at the committer appreciation.

### Type
As of types, we try to align with AngularJS policy, types may be:
* **ci**: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs)
* **docs**: Documentation only changes
* **feat**: A new feature
* **fix**: A bug fix
* **perf**: A code change that improves performance
* **refactor**: A code change that neither fixes a bug nor adds a feature
* **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)

You may also use any type which is not listed in this document as long as you find it better suiting the commit type. (example: `deps`, `chore`, etc.)


### Scope
The scope should be the name of the part of the code affected. As an example, a commit which overhaul the admin plugin should have a scope of "admin".\
Scope is optional if the commit is global or doesn't apply to a specific part of the code (example: commits on the README file may start with `:emote: docs:` without scope)

### Subject
The subject contains a succinct description of the change:

* use the imperative, present tense: "change" not "changed" nor "changes"
* don't capitalize the first letter
* no dot (.) at the end

```{admonition} 🤝 Help us to improve this documentation!
:class: tip

If you want to help us to improve this documentation, you can edit it on the [GitHub repo](https://github.com/Gunivers/Gipsy/) or come and discuss with us on our [Discord server](https://discord.gg/E8qq6tN)!
```