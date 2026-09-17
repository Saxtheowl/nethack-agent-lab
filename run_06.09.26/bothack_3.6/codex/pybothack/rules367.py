"""Version-specific rules audited against NetHack 3.6.7 source."""
def critically_low_hp(hp, maximum, level):
    """src/pray.c critically_low_hp(FALSE), for the displayed HP form."""
    divisor=5 if level<=5 else 6 if level<=13 else 7 if level<=21 else 8 if level<=29 else 9
    return hp<=5 or hp*divisor<=min(maximum,15*level)
