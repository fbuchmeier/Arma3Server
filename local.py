import os
import keys
import re


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

    log_pattern = re.compile(r"(?P<timestamp>\d{2}:\d{2}:\d{2}) Server load: FPS (?P<fps>\d+), memory used: (?P<memory>\d+).*Players: (?P<players>\d+)")
    match = log_pattern.match(line)

    if "Server load: FPS" in line:
        return {
            "timestamp": match["timestamp"], 
            "fps": int(match["fps"]),
            "memory": int(match["memory"]),
            "players": int(match["players"])
        }
    else:
        return False

if __name__ == "__main__":
    import doctest
    doctest.testmod()