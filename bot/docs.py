import os

def generate_docs():
    docs = open("SUMMARY.md","w+")
    docs.write("""# Summary

# For users

## Information

* [FAQ](docs/FAQ.md)
* [Contribute](docs/CONTRIBUTING.md)
* [License](LICENSE.md)

## Installed plugins
    """)

    for plugin in os.listdir('./plugins/'):
        if plugin[0] != '_':
            if os.path.isfile('./plugins/' + plugin + "/docs/user_documentation.md"):
                docs.write("* [" + plugin + "](plugins/" + plugin + "/docs/user_documentation.md)\n")


    if os.listdir('./docs/create_plugin') != []:
        docs.write("""
# For developpers

## Create a plugin
""")

    for file in os.listdir('./docs/create_plugin'):
        if file[-3:] == ".md":
            docs.write("* [" + file[:-3].replace("_"," ") + "](docs/create_plugin/" + file + ")\n")


    docs.close()