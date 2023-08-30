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

    decline = ["no", "n", "nah", "nope"]

    config = core.config.get("rss")

    choice = input(f"\n{blue}🔄️ Do you want to enable the RSS loop? [Y/n]:{stop} ")
    if choice not in decline:
        config["rss_loop_enabled"] = True

    return config
