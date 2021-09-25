import os
from shutil import copyfile

def generate_docs():
    docs = open("docs/summary.rst","w+")
    docs.write("""
.. toctree::
    :maxdepth: 3
    :caption: Info

    contributing.md
    faq.md

.. toctree::
    :maxdepth: 2
    :caption: Installed plugins

""")

    if not os.path.isdir("./docs/plugins"):
        os.makedirs("./docs/plugins")
    for file in os.listdir("./docs/plugins"):
        os.remove("./docs/plugins/" + file)
    for plugin in os.listdir('./plugins/'):
        if plugin[0] != '_':
            if os.path.isfile('./plugins/' + plugin + "/docs/user_documentation.rst"):
                copyfile('./plugins/' + plugin + "/docs/user_documentation.rst", './docs/plugins/' + plugin + ".rst")
                docs.write("    plugins/" + plugin + ".rst\n")
            else:
                if os.path.isfile('./plugins/' + plugin + "/docs/user_documentation.md"):
                    copyfile('./plugins/' + plugin + "/docs/user_documentation.md", './docs/plugins/' + plugin + ".md")
                    docs.write("    plugins/" + plugin + ".md\n")


    if os.listdir('./docs/create_plugin') != []:
        docs.write("""
.. toctree::
    :maxdepth: 2
    :caption: For developers
    
""")

    for file in os.listdir('./docs/create_plugin'):
        if file[-3:] == ".md" or file[-4:] == ".rst":
            docs.write("    create_plugin/" + file + "\n")


    docs.close()