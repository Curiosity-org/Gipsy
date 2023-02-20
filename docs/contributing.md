# 🤝 Contributing

## Pre-commit hooks
We use [pre-commit](https://pre-commit.com/) to ensure a consistent code style.\
Before starting to contribute, you should install the pre-commit hooks by running `pre-commit install` in the root
directory of the project (make sure you have dependencies in `requirements.txt` installed, and that you're in the venv
if you use one).

Hooks are in place to ensure :
- consistent code style (black is enabled with auto-fix)
- no broken configs (JSON and YAML files are checked for syntax errors)
- commit message format consistency

Hooks are strongly recommended, but you can bypass them by using the `--no-verify` flag when committing.\
Note that we will most likely refuse any PR that doesn't pass successfully the pre-commit hooks

## Commit Message Format
To ensure consistency and ease of reading of the history, commit messages must follow this format:
`:emote: [type](scope): <subject>`

*examples:*  `🪱 fix(all): fix some import errors`
            `🧱 deps: use discord.py 2.0`


#### Emote
We use [gitmoji](https://gitmoji.dev/) to add an emote to the commit message.\
You can find the list of available emotes [here](https://gitmoji.dev/)
There's also a [VSCode extension](https://marketplace.visualstudio.com/items?itemName=vtrois.gitmoji-vscode) or a
[PyCharm plugin](https://plugins.jetbrains.com/plugin/13389-gitmoji) to help you find the right emote.

### Type
As of types, we try to align with AngularJS policy, types may be:
* **build**: Changes that affect the build system or external dependencies
* **ci**: Changes to our CI configuration files and scripts
* **docs**: Documentation only changes
* **feat**: A new feature
* **fix**: A bug fix
* **perf**: A code change that improves performance
* **refactor**: A code change that neither fixes a bug nor adds a feature
* **revert**: Reverts a previous commit
* **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
* **test**: Adding missing tests or correcting existing tests
* **chore**: Changes to the build process or auxiliary tools and libraries such as documentation generation
* **wip**: Work in progress


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