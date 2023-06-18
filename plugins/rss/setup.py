"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

from LRFutils import color
import core

def run():

    blue = color.fg.blue
    stop = color.stop

    accept = ["yes", "y", "yeah","yep"]
    decline = ["no", "n", "nah", "nope"]

    config = core.config.get("rss")

    choice = input(f"\n{blue}🔄️ Do you want to enable the RSS loop? [Y/n]:{stop} ")
    if choice not in decline:
        config["rss_loop_enabled"] = True

        # Consumer key

        def set_consumer_key():
            if key := input(f"\n🔑 {blue}Twitter consumer key (let empty to ignore):{stop} ") != "":
                config["twitter"]["consumer_key"] = key

        if config["twitter"]["consumer_key"] is not None:
            choice = input(f"\n{blue}A Twitter consumer key is already set. "\
                f"Do you want to edit it? [y/N]:{stop} ")
            if choice in accept:
                set_consumer_key()
        else:
            set_consumer_key()

        #  Consumer secret

        def set_consumer_secret():
            if secret := input(
                f"\n🔑 {blue}Twitter consumer secret (let empty to ignore):{stop} "
            ) != "":
                config["twitter"]["consumer_secret"] = secret

        if config["twitter"]["consumer_secret"] is not None:
            choice = input(f"\n{blue}A Twitter consumer secret is already set. "\
                f"Do you want to edit it? [y/N]:{stop} ")
            if choice in accept:
                set_consumer_secret()
        else:
            set_consumer_secret()

        # Access token key

        def set_access_token_key():
            if key := input(
                f"\n🔑 {blue}Twitter access token key (let empty to ignore):{stop} "
            ) != "":
                config["twitter"]["access_token_key"] = key

        if config["twitter"]["access_token_key"] is not None:
            choice = input(f"\n{blue}A Twitter access token key is already set. "\
                f"Do you want to edit it? [y/N]:{stop} ")
            if choice in accept:
                set_access_token_key()
        else:
            set_access_token_key()

        # Access token secret

        def set_access_token_secret():
            if secret := input(f"\n🔑 {blue}Twitter access token secret"\
                f"(let empty to ignore):{stop} ") != "":
                config["twitter"]["access_token_secret"] = secret

        if config["twitter"]["access_token_secret"] is not None:
            choice = input(f"\n{blue}A Twitter access token secret is already set. "\
                f"Do you want to edit it? [y/N]:{stop} ")
            if choice in accept:
                set_access_token_secret()
        else:
            set_access_token_secret()

    return config
