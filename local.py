import os
import keys
import re
import subprocess
from string import Template
from prometheus_client import start_http_server, Gauge

server_fields = ["fps", "memory", "players"]

antistasi_fields = [
    "ServerFPS",
    "Players",
    "DeadUnits",
    "AllUnits",
    "UnitsAwareOfEnemies",
    "AllVehicles",
    "WreckedVehicles",
    "Entities",
    "GroupsRebels",
    "GroupsInvaders",
    "GroupsOccupants",
    "GroupsCiv",
    "GroupsTotal",
    "GroupsCombatBehaviour",
    "Faction Cash",
    "HR",
    "OccAggro",
    "InvAggro",
    "Warlevel",
]


def mods(d):
    mods = []

    # Find mod folders
    for m in os.listdir(d):
        moddir = os.path.join(d, m)
        if os.path.isdir(moddir):
            mods.append(moddir)
            keys.copy(moddir)

    return mods


def parse_monitor_log(line):
    """
    >>> parse_monitor_log("19:54:09 Server load: FPS 29, memory used: 1535 MB, out: 19 Kbps, in: 0 Kbps, NG:0, G:65, BE-NG:0, BE-G:0, Players: 1 (L:0, R:1, B:0, G:0, D:0)")
    {'timestamp': '19:54:09', 'fps': 29, 'memory': 1535, 'players': 1}

    >>> parse_monitor_log('19:53:37 "main/BIS_fnc_log: HandleDisconnect : B Alpha 1-1:21"')
    False
    """

    log_pattern = re.compile(
        r"(?P<timestamp>\d{2}:\d{2}:\d{2}) Server load: FPS (?P<fps>\d+), memory used: (?P<memory>\d+).*Players: (?P<players>\d+)"
    )
    match = log_pattern.match(line)

    if "Server load: FPS" in line:
        return {
            "timestamp": match["timestamp"],
            "fps": int(match["fps"]),
            "memory": int(match["memory"]),
            "players": int(match["players"]),
        }
    else:
        return False


def parse_antistasi_log(line, fields=[]):
    """
    >>> parse_antistasi_log('13:32:29 2022-11-06 13:32:29:878 | Antistasi | Info | File: A3A_fnc_logPerformance |  ServerFPS:6.16333, Players:3, DeadUnits:22, AllUnits:24, UnitsAwareOfEnemies:0, AllVehicles:220, WreckedVehicles:4, Entities:274, GroupsRebels:4, GroupsInvaders:6, GroupsOccupants:0, GroupsCiv:0, GroupsTotal:10, GroupsCombatBehaviour:0, Faction Cash:<null>, HR:<null>, OccAggro: 39, InvAggro: 0, Warlevel: 9', antistasi_fields)
    {'server_fps': 6, 'players': 3, 'dead_units': 22, 'all_units': 24, 'units_aware_of_enemies': 0, 'all_vehicles': 220, 'wrecked_vehicles': 4, 'entities': 274, 'groups_rebels': 4, 'groups_invaders': 6, 'groups_occupants': 0, 'groups_civ': 0, 'groups_total': 10, 'groups_combat_behaviour': 0, 'faction_cash': 0, 'hr': 0, 'occ_aggro': 39, 'inv_aggro': 0, 'warlevel': 9}

    >>> parse_antistasi_log('13:32:29 2022-11-06 13:32:29:878 | Antistasi | Info | File: A3A_fnc_logPerformance |  ServerFPS:6.86333, Players:3, DeadUnits:22, AllUnits:24, UnitsAwareOfEnemies:0, AllVehicles:220, WreckedVehicles:4, Entities:274, GroupsRebels:4, GroupsInvaders:6, GroupsOccupants:0, GroupsCiv:0, GroupsTotal:10, GroupsCombatBehaviour:0, Faction Cash:<null>, HR:<null>, OccAggro: 39, InvAggro: 0, Warlevel: 9', antistasi_fields)
    {'server_fps': 7, 'players': 3, 'dead_units': 22, 'all_units': 24, 'units_aware_of_enemies': 0, 'all_vehicles': 220, 'wrecked_vehicles': 4, 'entities': 274, 'groups_rebels': 4, 'groups_invaders': 6, 'groups_occupants': 0, 'groups_civ': 0, 'groups_total': 10, 'groups_combat_behaviour': 0, 'faction_cash': 0, 'hr': 0, 'occ_aggro': 39, 'inv_aggro': 0, 'warlevel': 9}

    >>> parse_antistasi_log('16:02:15 Warning: Cleanup player - person 2:823 not found', antistasi_fields)
    False

    >>> parse_antistasi_log('16:02:15 Warning: Cleanup Players - person 2:823 not found', antistasi_fields)
    False

    >>> parse_antistasi_log("19:54:09 Server load: FPS 29, memory used: 1535 MB, out: 19 Kbps, in: 0 Kbps, NG:0, G:65, BE-NG:0, BE-G:0, Players: 1 (L:0, R:1, B:0, G:0, D:0)", antistasi_fields)
    {'players': 1}

    >>> parse_antistasi_log('13:32:29 2022-11-06 13:32:29:878 | Antistasi | Info | File: A3A_fnc_logPerformance |  ServerFPS:6.16333, Players:3, DeadUnits:22, AllUnits:24, UnitsAwareOfEnemies:0, GroupsOccupants:0, GroupsCiv:0, GroupsTotal:10, GroupsCombatBehaviour:0, Faction Cash:<null>, HR:<null>, OccAggro: 39, InvAggro: 0, Warlevel: 9', antistasi_fields)
    {'server_fps': 6, 'players': 3, 'dead_units': 22, 'all_units': 24, 'units_aware_of_enemies': 0, 'groups_occupants': 0, 'groups_civ': 0, 'groups_total': 10, 'groups_combat_behaviour': 0, 'faction_cash': 0, 'hr': 0, 'occ_aggro': 39, 'inv_aggro': 0, 'warlevel': 9}
    """

    results = {}

    for f in fields:
        match = re.compile(
            rf".*\s+{f}:(?P<{sanitize(f)}>\s?\d+(\.(\d+))?|<null>).*"
        ).match(line)

        if not match:
            continue

        if match[sanitize(f)] == "<null>":
            value = 0
        else:
            value = round(float(match[sanitize(f)]))

        results[sanitize(f)] = value

    if results:
        return results
    else:
        return False


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def sanitize(s):
    return camel_to_snake(re.sub(r"\W+", "", s))


def setup_metrics():
    """
    Sets up /metrics endpoint at localhost:8000
    and exposes all metrics defined in server_fields and anstistasi_fields
    """
    start_http_server(8000)

    metrics = {}
    for m in antistasi_fields:
        metrics["antistasi_" + sanitize(m)] = Gauge(
            "arma3_antistasi_" + sanitize(m), m
        )

    for m in server_fields:
        metrics["server_" + sanitize(m)] = Gauge(
            "arma3_server_" + sanitize(m), m
        )

    return metrics

def setup_arma(steam_user, steam_password, steam_branch="", steam_branch_password="", home="/arma3"):
    """
    Setup ARMA with the given user, password and branch
    """
    print("Installing ARMA 3")
    steamcmd = ["/steamcmd/steamcmd.sh"]
    steamcmd.extend(["+force_install_dir", home])
    steamcmd.extend(["+login", steam_user, steam_password])
    steamcmd.extend(["+app_update", "233780"])

    if steam_branch:
        steamcmd.extend(["-beta", steam_branch])

    if steam_branch_password:
        steamcmd.extend(["-betapassword", steam_branch_password])

    steamcmd.extend(["validate", "+quit"])

    return subprocess.call(steamcmd)


def mod_param(name, mods):
    return ' -{}="{}" '.format(name, ";".join(mods))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
