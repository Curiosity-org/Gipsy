

# -- Project information -----------------------------------------------------

project = "Gipsy"
copyright = "2023, Gunivers"
author = "Z_runner, Leirof, Aeris One, ascpial, theogiraudet, fantomitechno, Just_a_Player and Aragorn"

import os

# Project information ---------------------------------------------------------

project = 'Gipsy'
copyright = '2023, Gunivers'
author = 'Gunivers'
html_favicon = "_static/logo.png"

# -- General configuration ----------------------------------------------------

extensions = [
    'myst_parser',
    'sphinx_design',
    'sphinx_togglebutton',
    'sphinx_copybutton',
]
myst_heading_anchors = 6
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Options for HTML output -----------------------------------------------------

html_theme = 'pydata_sphinx_theme'

# html_css_files = [
#     'credits.css',
# ]

html_theme_options = {
    "github_url": "https://github.com/Gunivers/Gipsy",
    "logo": {
        "image_dark": "_static/logo.png",
        "text": "Gipsy",  # Uncomment to try text with logo
    },
    "icon_links": [
        {
            "name": "Support us",
            "url": "https://utip.io/gunivers",
            "icon": "fa fa-heart",
        },
        {
            "name": "Gunivers",
            "url": "https://gunivers.net",
            "icon": "_static/logo-gunivers.png",
            "type": "local",
        },
        {
            "name": "Discord server",
            "url": "https://discord.gg/E8qq6tN",
            "icon": "_static/logo-discord.png",
            "type": "local",
        },
    ]
}

html_logo = "_static/logo.png"

html_static_path = ['_static']

html_css_files = [
    'css/stylesheet.css',
]

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    #"linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

# Plugin doc generation -------------------------------------------------------

import shutil

CONTRIBUTE = """
```{admonition} 🤝 Help us to improve this documentation!
:class: tip
If you want to help us to improve this documentation, you can edit it on the [GitHub repo](https://github.com/Gunivers/Gipsy/) or come and discuss with us on our [Discord server](https://discord.gg/E8qq6tN)!
```
"""

GITHUB_DISCUSSION_FOOTER = """
---
## 💬 Did it help you?
Feel free to leave your questions and feedbacks below!
<script src="https://giscus.app/client.js"
        data-repo="{orga}/{repo}"
        data-repo-id="R_kgDOHQph3g"
        data-category="Documentation"
        data-category-id="DIC_kwDOHQph3s4CUSnO"
        data-mapping="title"
        data-strict="0"
        data-reactions-enabled="1"
        data-emit-metadata="0"
        data-input-position="bottom"
        data-theme="light"
        data-lang="fr"
        data-loading="lazy"
        crossorigin="anonymous"
        async>
</script>
"""

def generate_plugin_doc():

    # Saving index.md file content except plugin toctree
    with open("user_guide.md", "r", encoding="utf-8") as f:
        before = []
        for line in f:
            before.append(line)
            if line.startswith("<!-- Plugin toctree"):
                break

    # Removing old plugin doc files
    if os.path.isdir(f"plugins"):
        shutil.rmtree(f"plugins")

    # Restoring index.md file content without plugin toctree
    with open("user_guide.md", "w+", encoding="utf-8") as toctree:
        for line in before:
            toctree.write(line)
        toctree.write("\n\n```{toctree}\n:maxdepth: 2\n:hidden:\n\n")

        # Generating plugin toctree and moving pugin's doc files in the global docs folder
        path = os.path.join("", os.pardir)
        for plugin in os.listdir(f"{path}/plugins"):
            
            # Checking if plugin has a doc folder
            if not os.path.isdir(f"{path}/plugins/" + plugin + "/docs"):
                continue

            # Iterate over plugin's doc files
            for file in os.listdir(f"{path}/plugins/" + plugin + "/docs"):

                # Checking if file is a markdown or a restructured text file
                if not file[-3:] == ".md" and not file[-4:] == ".rst":
                    continue

                
                if not os.path.isdir(f"/plugins/{plugin}/"):
                    os.makedirs(f"plugins/{plugin}/")
                shutil.copyfile(
                    f"{path}/plugins/{plugin}/docs/{file}",
                    f"plugins/{plugin}/{file}",
                )
                toctree.write(f"plugins/{plugin}/{file}\n")

                with open(f"plugins/{plugin}/{file}", "a", encoding="utf-8") as f:
                    f.write(CONTRIBUTE)

                    if "repository_url" in html_theme_options\
                            and html_theme_options["repository_url"].startswith("https://github.com/"):
                        orga = html_theme_options["repository_url"].split("/")[3]
                        repo = html_theme_options["repository_url"].split("/")[4]
                        
                        f.write(
                            GITHUB_DISCUSSION_FOOTER.format(orga=orga, repo=repo)
                        )
        
        toctree.write("\n```")
generate_plugin_doc()
