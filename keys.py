import glob
import os
import shutil

# Constants
KEYS = "/arma3/keys"


def copy(moddir):
    if not os.path.isdir(KEYS):
        if os.path.exists(KEYS):
            os.remove(KEYS)
        os.makedirs(KEYS)

    keys = glob.glob(os.path.join(moddir, "**/*.bikey"))
    
    if len(keys) > 0:
        for key in keys:
            if not os.path.isdir(key):
                shutil.copy2(key, KEYS)
    else:
        print("Missing keys:", moddir)

