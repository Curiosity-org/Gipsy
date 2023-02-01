.. Gipsy documentation master file, created by
   sphinx-quickstart on Sat Sep 25 11:57:54 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Gipsy's documentation!
=================================

Gipsy is a multifunction bot managed by the `Gunivers <https://gunivers.net>`_ community.

Please use at least **Python 3.9** to run this project.

Use ``pip install -r requirements.txt`` in the directory to install dependencies.

**Description**
-------------------

Gipsy is a Discord bot whose first objective is to meet the expectations of the Gunivers community. However, if we want to create new features, we might as well let those who might be interested in them enjoy them !
You can invite the bot, learn what it can do and follow its evolution.

**Invite**
--------------

You can invite the bot by `clicking here <http://utip.io/s/1yhs7W>`_


You can also invite the bot in beta version to enjoy the latest features added. Be careful though: the bot in beta version may contain security holes and many bugs. It may also stop working suddenly and for long periods. If you want to invite it though, `click here <https://discordapp.com/oauth2/authorize?client_id=813836349147840513&scope=bot&permissions=8>`_

.. toctree::
    :maxdepth: 3
    :caption: Info

    contributing.md
    faq.md

.. Start plugins documentation

.. toctree::
   :maxdepth: 1
   :caption: Installed plugins

   plugins/antikikoo/user_documentation.md
   plugins/channelArchive/user_documentation.md
   plugins/contact/user_documentation.md
   plugins/general/user_documentation.md
   plugins/giveaway/user_documentation.md
   plugins/group/user_documentation.md
   plugins/hypesquad/user_documentation.md
   plugins/log/user_documentation.md
   plugins/messageManager/user_documentation.md
   plugins/misc/user_documentation.md
   plugins/quizz/user_documentation.md
   plugins/roleLink/user_documentation.md
   plugins/rss/user_documentation.md
   plugins/thanks/user_documentation.md
   plugins/voice/user_documentation.md
   plugins/welcome/user_documentation.md
   plugins/wormhole/user_documentation.md
   plugins/xp/user_documentation.md

.. End plugins documentation

.. toctree::
    :maxdepth: 2
    :caption: For developers

    create_plugin/01-Plugin_structure.md
    create_plugin/02-Server_configuration_variables.md