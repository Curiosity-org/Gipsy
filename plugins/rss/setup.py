import yaml
import os
from LRFutils.color import Color
import core

def run(save=False):

    blue = Color.Blue
    NC = Color.NC

    accept = ["yes", "y", "yeah","yep"]
    decline = ["no", "n", "nah", "nope"]
    
    config = core.config.get("rss")
    
    choice = input(f"\n{blue}🔄️ Do you want to enable the RSS loop? [Y/n]:{NC} ")
    if choice not in decline:
        config["rss_loop_enabled"] = True

        # Consumer key
        
        def set_consumer_key():
            if c := input(f"\n🔑 {blue}Twitter consumer key (let empty to ignore):{NC} ") != "":
                config["twitter"]["consumer_key"] = c

        if config["twitter"]["consumer_key"] is not None:
            choice = input(f"\n{blue}A consumer kkey is already set. Do you want to edit it? [y/N]:{NC} ")
            if choice in accept:
                set_consumer_key()
        else:
            set_consumer_key()

        #  Consumer secret

        def set_consumer_secret():
            if c := input(f"\n🔑 {blue}Twitter consumer secret (let empty to ignore):{NC} ") != "":
                config["twitter"]["consumer_secret"] = c
        
        if config["twitter"]["consumer_secret"] is not None:
            choice = input(f"\n{blue}A consumer secret is already set. Do you want to edit it? [y/N]:{NC} ")
            if choice in accept:
                set_consumer_secret()
        else:
            set_consumer_secret()

        # Access token key

        def set_access_token_key():
            if c := input(f"\n🔑 {blue}Twitter access token key (let empty to ignore):{NC} ") != "":
                    config["twitter"]["access_token_key"] = c

        if config["twitter"]["access_token_key"] is not None:
            choice = input(f"\n{blue}An access token key is already set. Do you want to edit it? [y/N]:{NC} ")
            if choice in accept:
                set_access_token_key()
        else:
            set_access_token_key()

        # Access token secret

        def set_access_token_secret():  
            if c := input(f"\n🔑 {blue}Twitter access token secret (let empty to ignore):{NC} ") != "":
                config["twitter"]["access_token_secret"] = c
        
        if config["twitter"]["access_token_secret"] is not None:   
            choice = input(f"\n{blue}An access token secret is already set. Do you want to edit it? [y/N]:{NC} ")
            if choice in accept:
                set_access_token_secret()
        else:
            set_access_token_secret()

    return config