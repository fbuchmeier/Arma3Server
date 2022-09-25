import os
import re
import subprocess
import urllib.request

import keys

WORKSHOP = "steamapps/workshop/content/107410/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"  # noqa: E501

def env_defined(key):
    return key in os.environ and len(os.environ[key]) > 0


def mod(id):
    if os.environ["SKIP_INSTALL"] in ["", "false"]:
        steamcmd = ["/steamcmd/steamcmd.sh"]
        steamcmd.extend(["+force_install_dir", "/arma3"])
        if env_defined("STEAM_USER") and env_defined("STEAM_PASSWORD"):
            steamcmd.extend(["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]])
        steamcmd.extend(["+workshop_download_item", "107410", id])
        steamcmd.extend(["+quit"])
        res = ""
        # steamcmd returns 10 for errors like timeouts
        while res != 0:
            res = subprocess.call(steamcmd)
            if res != 0:
                subprocess.call(["/usr/bin/rsync","-aPq","/arma3/steamapps/workshop/downloads/107410/{}/".format(id),"/arma3/steamapps/workshop/content/107410/{}/".format(id)])
    else:
        print("Skipping installation of mods because SKIP_INSTALL is {}".format(os.environ["SKIP_INSTALL"]))

def preset(mod_file):
    if mod_file.startswith("http"):
        req = urllib.request.Request(
            mod_file,
            headers={"User-Agent": USER_AGENT},
        )
        remote = urllib.request.urlopen(req)
        with open("preset.html", "wb") as f:
            f.write(remote.read())
        mod_file = "preset.html"
    mods = []
    with open(mod_file) as f:
        html = f.read()
        regex = r"filedetails\/\?id=(\d+)\""
        matches = re.finditer(regex, html, re.MULTILINE)
        for _, match in enumerate(matches, start=1):
            mod(match.group(1))
            moddir = WORKSHOP + match.group(1)
            mods.append(moddir)
            keys.copy(moddir)
    return mods
