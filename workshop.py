import os
import re
import subprocess
import urllib.request

import keys

WORKSHOP = "steamapps/workshop/content/107410/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"  # noqa: E501


def mod(id, steam_user="", steam_password="", skip_install=False):
    if not skip_install:
        steamcmd = ["/steamcmd/steamcmd.sh"]
        steamcmd.extend(["+force_install_dir", "/arma3"])
        if steam_password and steam_user:
            steamcmd.extend(
                ["+login", steam_user, steam_password]
            )
        steamcmd.extend(["+workshop_download_item", "107410", id])
        steamcmd.extend(["+quit"])
        res = ""
        # steamcmd returns 10 for errors like timeouts
        for i in range(1, 10):
            res = subprocess.call(steamcmd)
            if res != 0:
                subprocess.call(
                    [
                        "/usr/bin/rsync",
                        "-aPq",
                        "/arma3/steamapps/workshop/downloads/107410/{}/".format(id),
                        "/arma3/steamapps/workshop/content/107410/{}/".format(id),
                    ]
                )
            else:
                break
    else:
        print(
            "Skipping installation of mods because SKIP_INSTALL is {}".format(
                str(skip_install)
            )
        )


def preset(mod_file, steam_user="", steam_password="", skip_install=False):
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
            mod(match.group(1), steam_user=steam_user, steam_passwor=steam_password, skip_install=skip_install)
            moddir = WORKSHOP + match.group(1)
            mods.append(moddir)
            keys.copy(moddir)
    return mods
