from pathlib import Path
R=Path(__file__).resolve().parents[1]
S=R/'vendor/NetHack-NetHack-3.6.7_Released'
def edit(p,a,b):
 f=S/p; s=f.read_text(); assert s.count(a)==1,(p,s.count(a)); f.write_text(s.replace(a,b))
edit('include/hack.h','#define TELL 1','extern int bh_enabled(const char *);\nextern void bh_event(const char *, int);\nextern void bh_kit(void);\n\n#define TELL 1')
edit('src/allmain.c','    u_init();','    u_init();\n    bh_kit();')
edit('src/allmain.c','    flags.friday13 = friday_13th();','    if (getenv("BH_SEED")) flags.moonphase = 0;\n    flags.friday13 = getenv("BH_SEED") ? 0 : friday_13th();')
edit('src/allmain.c','    flags.moonphase = phase_of_the_moon();','    flags.moonphase = getenv("BH_SEED") ? 0 : phase_of_the_moon();')
edit('src/hacklib.c','    set_random(sys_random_seed(), fn);','    const char *s = getenv("BH_SEED");\n    set_random(s ? strtoul(s, (char **) 0, 10) : sys_random_seed(), fn);')
edit('src/hacklib.c','    if (has_strong_rngseed)','    if (!getenv("BH_SEED") && has_strong_rngseed)')
edit('src/eat.c','gethungry()\n{','gethungry()\n{\n    if (bh_enabled("BH_HUNGER") && u.uhunger < 700) {\n        bh_event("hunger", u.uhunger);\n        init_uhunger();\n    }')
edit('src/end.c','    boolean survive = FALSE;','    boolean survive = FALSE;\n\n    if (how < GENOCIDED + 1 && bh_enabled("BH_INVINCIBLE")) {\n        bh_event("prevent_death", how);\n        savelife(how);\n        killer.name[0] = 0;\n        return;\n    }')
edit('src/end.c','    program_state.gameover = 1;','    bh_event(how == ASCENDED ? "ascended" : how == PANICKED ? "panic" : how == QUIT ? "quit" : how == ESCAPED ? "escaped" : "death", how);\n    program_state.gameover = 1;')
edit('win/tty/wintty.c',"    HUPSKIP_RESULT('\\033');\n    print_vt_code1(AVTC_INLINE_SYNC);",'    bh_event("input", 0);\n    HUPSKIP_RESULT(\'\\033\');\n    print_vt_code1(AVTC_INLINE_SYNC);')
# Keep build system intact by compiling the small support unit as part of allmain.
with (S/'src/allmain.c').open('a') as f: f.write('\n#include "bh_support.c"\n')
(S/'src/bh_support.c').write_text((R/'patches/bh_support.c').read_text())
