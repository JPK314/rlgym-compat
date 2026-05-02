# From https://github.com/RLBot/RLBot/blob/master/src/main/python/rlbot/version.py
# Store the version here so:
# 1) we don't load dependencies by storing it in __init__.py
# 2) we can import it in setup.py for the same reason
# 3) we can import it into your module module
# https://stackoverflow.com/questions/458550/standard-way-to-embed-version-into-python-package

__version__ = "2.3.6"

release_notes = {
    "2.3.6": """
    - update math functions to maintain dtype and fix edge case in physics object orientation array caching
    """,
    "2.3.5": """
    - change function signature for v2 create_compat_game_state to make agent_ids_fn optional instead of with default lambda function in function signature
    """,
    "2.3.4": """
    - fix dtypes in physics objects to be consistent with rocketsim engine behavior in rlgym v2
    - add agent_ids_fn as an optional parameter to GameState upon creation to calculate agent ids based on packet and provide a mapping from player ids (in packet) to agent id (arbitrary type). Default value for this is no change from previous functionality
    """,
    "2.3.3": """
    - fix issue with SimExtraInfo introduced by 2.3.1
    """,
    "2.3.2": """
    - fix RocketSim failure to import breaking things even if SimExtraInfo is unused
    """,
    "2.3.1": """
    - change ExtraPlayerInfo to use ball_touch_ticks: Optional[List[int]] instead of ball_touches: Optional[int] and update other classes accordingly
    - remove tick_skip from SimExtraInfo and instead include a parameter to control how many ball touch ticks will be stored per player in the SimExtraInfo class (100 is default and that should be fine for most use cases)
    """,
    "2.3.0": """
    - rename match_settings to match_configuration to better match the RLBot flat spec naming convention
    - fix has_flip erroneously becoming true when the flip timer naturally expires while in the air
    """,
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
