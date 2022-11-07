import os
import re
import subprocess
from string import Template

import local
import workshop


def mod_param(name, mods):
    return ' -{}="{}" '.format(name, ";".join(mods))


def env_defined(key):
    return key in os.environ and len(os.environ[key]) > 0


if __name__ == "__main__":

    CONFIG_FILE = os.environ["ARMA_CONFIG"]
    KEYS = "/arma3/keys"

    if not os.path.isdir(KEYS):
        if os.path.exists(KEYS):
            os.remove(KEYS)
        os.makedirs(KEYS)

    if os.environ["SKIP_INSTALL"] in ["", "false"]:
        # Install Arma
        print("Installing ARMA 3")
        steamcmd = ["/steamcmd/steamcmd.sh"]
        steamcmd.extend(["+force_install_dir", "/arma3"])

        if env_defined("STEAM_USER") and env_defined("STEAM_PASSWORD"):
            steamcmd.extend(
                ["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]]
            )
            steamcmd.extend(["+app_update", "233780"])
        else:
            print(
                "WARNING: Skipping installation as STEAM_USER or STEAM_PASSWORD are missing"
            )

        if env_defined("STEAM_BRANCH"):
            steamcmd.extend(["-beta", os.environ["STEAM_BRANCH"]])

        if env_defined("STEAM_BRANCH_PASSWORD"):
            steamcmd.extend(["-betapassword", os.environ["STEAM_BRANCH_PASSWORD"]])

        steamcmd.extend(["validate", "+quit"])
        subprocess.call(steamcmd)
    else:
        print(
            "Skipping installation of ARMA because SKIP_INSTALL is {}".format(
                os.environ["SKIP_INSTALL"]
            )
        )

    # Mods

    mods = []

    if os.environ["MODS_PRESET"] != "":
        mods.extend(workshop.preset(os.environ["MODS_PRESET"]))

    if os.environ["MODS_LOCAL"] == "true" and os.path.exists("mods"):
        mods.extend(local.mods("mods"))

    launch = "{} -limitFPS={} -world={} {} {}".format(
        os.environ["ARMA_BINARY"],
        os.environ["ARMA_LIMITFPS"],
        os.environ["ARMA_WORLD"],
        os.environ["ARMA_PARAMS"],
        mod_param("mod", mods),
    )

    if os.environ["ARMA_CDLC"] != "":
        for cdlc in os.environ["ARMA_CDLC"].split(";"):
            launch += " -mod={}".format(cdlc)

    clients = int(os.environ["HEADLESS_CLIENTS"])
    print("Headless Clients:", clients)

    if clients != 0:
        with open("/arma3/configs/{}".format(CONFIG_FILE)) as config:
            data = config.read()
            regex = r"(.+?)(?:\s+)?=(?:\s+)?(.+?)(?:$|\/|;)"

            config_values = {}

            matches = re.finditer(regex, data, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                config_values[match.group(1).lower()] = match.group(2)

            if "headlessclients[]" not in config_values:
                data += '\nheadlessclients[] = {"127.0.0.1"};\n'
            if "localclient[]" not in config_values:
                data += '\nlocalclient[] = {"127.0.0.1"};\n'

            with open("/tmp/arma3.cfg", "w") as tmp_config:
                tmp_config.write(data)
            launch += ' -config="/tmp/arma3.cfg"'

        client_launch = launch
        client_launch += " -client -connect=127.0.0.1"
        if "password" in config_values:
            client_launch += " -password={}".format(config_values["password"])

        for i in range(0, clients):
            hc_template = Template(
                os.environ["HEADLESS_CLIENTS_PROFILE"]
            )  # eg. '$profile-hc-$i'
            hc_name = hc_template.substitute(
                profile=os.environ["ARMA_PROFILE"], i=i, ii=i + 1
            )

            hc_launch = client_launch + ' -name="{}"'.format(hc_name)
            print("LAUNCHING ARMA CLIENT {} WITH".format(i), hc_launch)
            subprocess.Popen(hc_launch, shell=True)

    else:
        launch += ' -config="/arma3/configs/{}"'.format(CONFIG_FILE)

    launch += ' -port={} -name="{}" -profiles="/arma3/configs/profiles"'.format(
        os.environ["PORT"], os.environ["ARMA_PROFILE"]
    )

    if os.path.exists("servermods"):
        launch += mod_param("serverMod", local.mods("servermods"))

    print("LAUNCHING ARMA SERVER WITH", launch, flush=True)
    open("/tmp/arma3_install_success", "a").close()

    # setup prometheus metrics

    from prometheus_client import start_http_server, Gauge
    import random

    start_http_server(8000)

    metrics = {}
    for m in local.antistasi_fields:
        metrics["antistasi_" + local.sanitize(m)] = Gauge("arma3_antistasi_" + local.sanitize(m), m)

    for m in local.server_fields:
        metrics["server_" + local.sanitize(m)] = Gauge("arma3_server_" + local.sanitize(m), m)

    import subprocess

    with subprocess.Popen(
        (launch.split(" ")),
        stdout=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
        stderr=subprocess.STDOUT,
        encoding="iso-8859-1",
    ) as process:
        for line in process.stdout:
            try:
                print(line, end="")

                if "Dedicated Host created" in line:
                    open("/tmp/arma3_launch_success", "a").close()

                if "Server load: FPS" in line:
                    result = local.parse_monitor_log(line)
                    for m in local.server_fields:
                        metrics["server_" + local.sanitize(m)].set(result[local.sanitize(m)])

                if "Antistasi" in line and "A3A_fnc_logPerformance" in line:
                    result = local.parse_antistasi_log(line, local.antistasi_fields)
                    for m in local.antistasi_fields:
                        metrics["antistasi_" + local.sanitize(m)].set(result[local.sanitize(m)])

            except UnicodeDecodeError as e:
                print(e)
