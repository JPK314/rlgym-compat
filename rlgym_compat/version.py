# From https://github.com/RLBot/RLBot/blob/master/src/main/python/rlbot/version.py
# Store the version here so:
# 1) we don't load dependencies by storing it in __init__.py
# 2) we can import it in setup.py for the same reason
# 3) we can import it into your module module
# https://stackoverflow.com/questions/458550/standard-way-to-embed-version-into-python-package

__version__ = "2.2.0"

release_notes = {
    "2.2.0": """
    - update to RLBot v5 release 0.7.x
    - update ball touch tracking mechanism, requiring users to manually reset ball touches when appropriate (based on the results of the action parser and the delay used) when using the RLGym v2 compat object
    """,
    "2.1.0": """
    - Update car state to match RLGym 2.0.1
    """,
    "2.0.2": """
    - Fix rename of BoostMutator to BoostAmountMutator in sim extra info
    """,
    "2.0.1": """
    - Fix can_flip property when on ground to better match RLGym
    """,
    "2.0.0": """
    - Modify for RLGym v2 and RLBot v5
    """,
    "1.1.1": """
    - Added additional properties, make has_jump more accurate
    """,
    "1.1.0": """
    - Added has_jump
    """,
    "1.0.2": """
    - Fixed car_id
    """,
    "1.0.1": """
    - Fixed on_ground bug
    """,
    "1.0.0": """
    Initial Release
    - Tested with RLGym 0.4.1
    """,
}


def get_current_release_notes():
    if __version__ in release_notes:
        return release_notes[__version__]
    return ""


def print_current_release_notes():
    print(f"Version {__version__}")
    print(get_current_release_notes())
    print("")
