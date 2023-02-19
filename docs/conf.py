# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = "Gipsy"
copyright = "2023, Gunivers"
author = "Z_runner, Leirof, Aeris One, ascpial, theogiraudet, fantomitechno, Just_a_Player and Aragorn"

# The full version, including alpha/beta/rc tags
# release = ""

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx_design",
]


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The root document.
root_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_book_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_theme_options = {
    "home_page_in_toc": False,
    "github_url": "https://github.com/Gunivers/Gipsy",
    "repository_url": "https://github.com/Gunivers/Gipsy",
    "repository_branch": "master",
    "path_to_docs": "docs",
    "use_repository_button": True,
    "use_edit_page_button": True,
  "announcement": "⚠️ You are reading a doc of an undergoing development version. Information can be out of date and/or change at any time. ⚠️",
}

html_logo = "img/logo.png"

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

#==============================================================================
# Plugin doc extraction
#==============================================================================

import os
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
    # Saving index.rst file content
    with open("index.rst", "r") as f:
        before = []
        after = []
        started = False
        ended = False
        for line in f:
            if not started:
                before.append(line)
            if line.startswith(".. Start plugins documentation"):
                started = True
            if line.startswith(".. End plugins documentation"):
                ended = True
            if ended:
                after.append(line)

    if os.path.isdir(f"plugins"):
        shutil.rmtree(f"plugins")

    with open("index.rst", "w+") as toctree:
        for line in before:
            toctree.write(line)

        # Generating plugin toctree and moving pugin's doc files in the global docs folder
        toctree.write("\n.. toctree::\n   :maxdepth: 1\n   :caption: User guide\n\n")
        path = os.path.join("", os.pardir)
        for plugin in os.listdir(f"{path}/plugins"):
            if os.path.isdir(f"{path}/plugins/" + plugin + "/docs"):
                for file in os.listdir(f"{path}/plugins/" + plugin + "/docs"):
                    if file[-3:] == ".md" or file[-4:] == ".rst":
                        if not os.path.isdir(f"/plugins/{plugin}/"):
                            os.makedirs(f"plugins/{plugin}/")
                        shutil.copyfile(
                            f"{path}/plugins/{plugin}/docs/{file}",
                            f"plugins/{plugin}/{file}",
                        )
                        toctree.write(f"   plugins/{plugin}/{file}\n")

                        with open(f"plugins/{plugin}/{file}", "a", encoding="utf-8") as f:
                            f.write(CONTRIBUTE)

                            if "repository_url" in html_theme_options and html_theme_options["repository_url"].startswith("https://github.com/"):
                                orga = html_theme_options["repository_url"].split("/")[3]
                                repo = html_theme_options["repository_url"].split("/")[4]
                                
                                f.write(
                                    GITHUB_DISCUSSION_FOOTER.format(orga=orga, repo=repo)
                                )

        toctree.write("\n")
        for line in after:
            toctree.write(line)

generate_plugin_doc()