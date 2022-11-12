import os
import re
import subprocess

import local
import workshop

# Files to be created for the different statup stages
# Can be used for example to determine the liveliness of the server
INSTALL_SUCCESS = "/tmp/arma3_install_success"
HEADLESS_CLIENTS_SUCCESS = "/tmp/arma3_headless_clients_success"
LAUNCH_SUCCESS = "/tmp/arma3_launch_success"

# Environment Variables
ARMA_CONFIG = os.environ.get("ARMA_CONFIG")
HEADLESS_CLIENTS_PROFILE = os.environ.get("HEADLESS_CLIENTS_PROFILE")
HEADLESS_CLIENTS = int(os.environ.get("HEADLESS_CLIENTS"))
STEAM_USER = os.environ.get("STEAM_USER")
STEAM_BRANCH = os.environ.get("STEAM_BRANCH")
STEAM_PASSWORD = os.environ.get("STEAM_PASSWORD")
STEAM_BRANCH_PASSWORD = os.environ.get("STEAM_BRANCH_PASSWORD")
SKIP_INSTALL = bool(
    os.environ.get("SKIP_INSTALL", "False").lower() in ("true", "1", "t")
)
MODS_PRESET = os.environ.get("MODS_PRESET")
MODS_LOCAL = bool(os.environ.get("MODS_LOCAL", "False").lower() in ("true", "1", "t"))
ARMA_PROFILE = os.environ.get("ARMA_PROFILE")
ARMA_BINARY = os.environ.get("ARMA_BINARY")
ARMA_LIMITFPS = os.environ.get("ARMA_LIMITFPS")
ARMA_WORLD = os.environ.get("ARMA_WORLD")
ARMA_PARAMS = os.environ.get("ARMA_PARAMS")
ARMA_CDLC = os.environ.get("ARMA_CDLC")
PORT = os.environ.get("PORT")


if __name__ == "__main__":

    metrics = local.setup_metrics()

    if not SKIP_INSTALL:
        local.setup_arma(
            steam_user=STEAM_USER,
            steam_password=STEAM_PASSWORD,
            steam_branch=STEAM_BRANCH,
            steam_branch_password=STEAM_BRANCH_PASSWORD,
        )

    # Mods
    mods = []

    if MODS_PRESET:
        mods.extend(workshop.preset(MODS_PRESET, steam_user=STEAM_USER, steam_password=STEAM_PASSWORD, skip_install=SKIP_INSTALL))

    if MODS_LOCAL and os.path.exists("mods"):
        mods.extend(local.mods("mods"))

    launch = "{} -limitFPS={} -world={} {} {}".format(
        ARMA_BINARY,
        ARMA_LIMITFPS,
        ARMA_WORLD,
        ARMA_PARAMS,
        local.mod_param("mod", mods),
    )

    if ARMA_CDLC:
        for cdlc in ARMA_CDLC.split(";"):
            launch += " -mod={}".format(cdlc)

    launch += ' -config="/arma3/configs/{}"'.format(ARMA_CONFIG)
    launch += ' -port={} -name="{}" -profiles="/arma3/configs/profiles"'.format(
        PORT, ARMA_PROFILE
    )

    if os.path.exists("servermods"):
        launch += local.mod_param("serverMod", local.mods("servermods"))

    print("LAUNCHING ARMA SERVER WITH", launch, flush=True)
    open(INSTALL_SUCCESS, "a").close()

    # Launch ARMA and parse stdout as metrics
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

                if "Dedicated host created".lower() in line:
                    open(LAUNCH_SUCCESS, "a").close()

                if "Dedicated client created".lower() in line:
                    open(HEADLESS_CLIENTS_SUCCESS, "a").close()

                if "Server load: FPS".lower() in line:
                    result = local.parse_monitor_log(line)
                    for m in local.server_fields:
                        m = local.sanitize(m)
                        metrics["server_" + m].set(
                            result[m]
                        )

                if (
                    "Antistasi".lower() in line
                    and "A3A_fnc_logPerformance".lower() in line
                ):
                    result = local.parse_antistasi_log(line, local.antistasi_fields)
                    for m in local.antistasi_fields:
                        m = local.sanitize(m)
                        metrics["antistasi_" + m].set(
                            result[m]
                        )

            except UnicodeDecodeError as e:
                print(e)
