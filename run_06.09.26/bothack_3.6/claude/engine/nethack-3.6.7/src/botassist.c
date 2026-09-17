/* NetHack 3.6.7  botassist.c
 *
 * Optional test assistance for bot development.  Every feature is off unless
 * its environment variable enables it, and every intervention is logged:
 *   - as an "assist" event in the bot protocol (window port "bot"), and
 *   - as a JSON line appended to $NH_ASSIST_LOG (if set).
 *
 *   NH_ASSIST_INVINCIBLE=1   death (except genocide/quit/panic) is undone:
 *                            the hero is restored like an amulet of life
 *                            saving that is never used up.
 *   NH_ASSIST_NOSTARVE=1     when nutrition drops below NH_ASSIST_NOSTARVE_AT
 *                            (default 50, i.e. before "Weak") it is reset to
 *                            900; choking to death on food is prevented.
 *   NH_ASSIST_KIT=<file>     extra starting items, one per line:
 *                               wear  <object description>
 *                               wield <object description>
 *                               inv   <object description>
 *                            descriptions use the wish syntax; items are
 *                            fully identified.
 *   NH_SEED=<unsigned>       fixed RNG seed (no reseeding on level change)
 *
 * The assistance never performs a goal for the bot: it does not move the
 * hero, create goal items, open levels or answer prompts.
 */

#include "hack.h"
#include "winbot.h"

static boolean assist_inited = FALSE;
static boolean a_invincible = FALSE, a_nostarve = FALSE;
static int a_nostarve_at = 50;
static const char *a_kit = 0, *a_logpath = 0;
static boolean a_seed_set = FALSE;
static unsigned long a_seed = 0UL;
static long a_count_lifesave = 0, a_count_feed = 0, a_count_choke = 0;
static long a_count_brain = 0, a_count_slime = 0;
static int a_peak_hpmax = 0;

/* called for every bot request: highest max HP seen (hero form) */
void
assist_track()
{
    if (!Upolyd && u.uhpmax > a_peak_hpmax)
        a_peak_hpmax = u.uhpmax;
}

static const char *const end_names[] = {
    "died", "choked", "poisoned", "starved", "drowned", "burned",
    "dissolved", "crushed", "stoned", "slimed", "genocided", "panicked",
    "tricked", "quit", "escaped", "ascended"
};

static boolean
env_true(name)
const char *name;
{
    const char *s = nh_getenv(name);

    return (boolean) (s && *s && *s != '0' && *s != 'n' && *s != 'N');
}

void
assist_init()
{
    const char *s;

    if (assist_inited)
        return;
    assist_inited = TRUE;
    a_invincible = env_true("NH_ASSIST_INVINCIBLE");
    a_nostarve = env_true("NH_ASSIST_NOSTARVE");
    if ((s = nh_getenv("NH_ASSIST_NOSTARVE_AT")) != 0 && *s)
        a_nostarve_at = atoi(s);
    if ((s = nh_getenv("NH_ASSIST_KIT")) != 0 && *s)
        a_kit = s;
    if ((s = nh_getenv("NH_ASSIST_LOG")) != 0 && *s)
        a_logpath = s;
    if ((s = nh_getenv("NH_SEED")) != 0 && *s) {
        a_seed = strtoul(s, (char **) 0, 10);
        a_seed_set = TRUE;
    }
}

boolean
assist_seed_set()
{
    assist_init();
    return a_seed_set;
}

unsigned long
assist_seed()
{
    assist_init();
    return a_seed;
}

/* minimal JSON string escaping into a fixed buffer */
static void
jstr(out, outsz, in)
char *out;
size_t outsz;
const char *in;
{
    size_t o = 0;
    const unsigned char *p = (const unsigned char *) (in ? in : "");

    if (outsz < 3)
        return;
    out[o++] = '"';
    for (; *p && o + 8 < outsz; p++) {
        if (*p == '"' || *p == '\\') {
            out[o++] = '\\';
            out[o++] = (char) *p;
        } else if (*p < 0x20 || *p >= 0x7f) {
            Sprintf(out + o, "\\u%04x", (unsigned) *p);
            o += 6;
        } else {
            out[o++] = (char) *p;
        }
    }
    out[o++] = '"';
    out[o] = '\0';
}

/* emit `["assist", {...}]` where body is the inside of the object */
static void
assist_emit(body)
const char *body;
{
    char buf[BUFSZ * 4];

    snprintf(buf, sizeof buf,
             "[\"assist\",{%s,\"turn\":%ld,\"depth\":%d,\"dnum\":%d}]", body,
             moves, depth(&u.uz), (int) u.uz.dnum);
#ifdef BOT_GRAPHICS
    botwin_event_json(buf);
#endif
    if (a_logpath) {
        FILE *fp = fopen(a_logpath, "a");

        if (fp) {
            fprintf(fp, "%s\n", buf);
            fclose(fp);
        }
    }
}

/* called from done() when the hero would die; TRUE = death undone */
boolean
assist_lifesave(how)
int how;
{
    char body[BUFSZ * 2], kname[BUFSZ];

    assist_init();
    if (!a_invincible || how >= GENOCIDED)
        return FALSE;
    a_count_lifesave++;
    jstr(kname, sizeof kname, killer.name);
    {
        /* a drained attribute would kill again at once (brainlessness,
           strength/constitution loss): restore drained attributes to their
           maximum, as the debug fuzzer's periodic restore ability does */
        int i, restored = 0;

        for (i = 0; i < A_MAX; i++)
            if (ABASE(i) < AMAX(i)) {
                ABASE(i) = AMAX(i);
                restored++;
            }
        /* repeated undone deaths also drain levels and max HP (Death's
           touch, level drainers): give them back too, or the invincible
           hero ends at XL1 unable to act (Astral Plane) */
        int levels = 0, hpgain = 0;

        assist_track();
        while (u.ulevel < u.ulevelmax && u.ulevel < MAXULEV) {
            pluslvl(FALSE);
            levels++;
        }
        if (!Upolyd && u.uhpmax < a_peak_hpmax) {
            hpgain = a_peak_hpmax - u.uhpmax;
            u.uhpmax = a_peak_hpmax;
        }
        if (restored || levels || hpgain)
            context.botl = 1;
        snprintf(body, sizeof body,
                 "\"kind\":\"lifesave\",\"how\":\"%s\",\"killer\":%s,"
                 "\"count\":%ld,\"hpmax\":%d,\"xl\":%d,"
                 "\"restored_attrs\":%d,\"restored_levels\":%d,"
                 "\"restored_hpmax\":%d",
                 end_names[how], kname, a_count_lifesave, u.uhpmax, u.ulevel,
                 restored, levels, hpgain);
    }
    assist_emit(body);
    return TRUE; /* caller runs savelife() */
}

/* called when a mind flayer would kill by brain eating; TRUE = prevented */
boolean
assist_brainsave()
{
    char body[BUFSZ];

    assist_init();
    if (!a_invincible)
        return FALSE;
    a_count_brain++;
    /* logged sparingly: one line per 20 prevented deaths */
    if (a_count_brain % 20 == 1) {
        snprintf(body, sizeof body,
                 "\"kind\":\"brainsave\",\"count\":%ld", a_count_brain);
        assist_emit(body);
    }
    return TRUE;
}

/* called from newuhs(); TRUE = nutrition was restored */
boolean
assist_nostarve()
{
    char body[BUFSZ];

    assist_init();
    if (!a_nostarve || u.uhunger >= a_nostarve_at)
        return FALSE;
    a_count_feed++;
    snprintf(body, sizeof body,
             "\"kind\":\"feed\",\"nutrition_before\":%d,\"count\":%ld",
             u.uhunger, a_count_feed);
    u.uhunger = 900;
    assist_emit(body);
    return TRUE;
}

/* called from choke() on the fatal branch; TRUE = death prevented */
boolean
assist_nochoke(food)
struct obj *food;
{
    char body[BUFSZ * 2], fname[BUFSZ];

    assist_init();
    if (!a_nostarve)
        return FALSE;
    a_count_choke++;
    jstr(fname, sizeof fname, food ? killer_xname(food) : "");
    snprintf(body, sizeof body,
             "\"kind\":\"nochoke\",\"food\":%s,\"count\":%ld", fname,
             a_count_choke);
    assist_emit(body);
    return TRUE;
}

/* called when the sliming countdown runs out, before the hero is turned
   into a green slime (which destroys worn armor that a later lifesave
   would not give back); TRUE = sliming cured instead */
boolean
assist_noslime()
{
    char body[BUFSZ];

    assist_init();
    if (!a_invincible)
        return FALSE;
    a_count_slime++;
    snprintf(body, sizeof body, "\"kind\":\"noslime\",\"count\":%ld",
             a_count_slime);
    assist_emit(body);
    return TRUE;
}

static void
kit_wear(obj)
struct obj *obj;
{
    if (obj->oclass == ARMOR_CLASS) {
        if (is_shield(obj) && !uarms && !(uwep && bimanual(uwep)))
            setworn(obj, W_ARMS);
        else if (is_helmet(obj) && !uarmh)
            setworn(obj, W_ARMH);
        else if (is_gloves(obj) && !uarmg)
            setworn(obj, W_ARMG);
        else if (is_shirt(obj) && !uarmu)
            setworn(obj, W_ARMU);
        else if (is_cloak(obj) && !uarmc)
            setworn(obj, W_ARMC);
        else if (is_boots(obj) && !uarmf)
            setworn(obj, W_ARMF);
        else if (is_suit(obj) && !uarm && !uarmc)
            setworn(obj, W_ARM);
    } else if (obj->oclass == AMULET_CLASS && !uamul) {
        setworn(obj, W_AMUL);
    } else if (obj->oclass == RING_CLASS) {
        if (!uleft)
            setworn(obj, W_RINGL);
        else if (!uright)
            setworn(obj, W_RINGR);
    }
}

void
assist_kit()
{
    FILE *fp;
    char line[BUFSZ], body[BUFSZ * 3], oname[BUFSZ * 2], *p, *what;
    boolean save_debug;

    assist_init();
    if (!a_kit)
        return;
    if (!(fp = fopen(a_kit, "r"))) {
        snprintf(body, sizeof body, "\"kind\":\"kit-error\",\"file\":\"%s\"",
                 "unreadable");
        assist_emit(body);
        return;
    }
    while (fgets(line, sizeof line, fp)) {
        struct obj *otmp;
        int mode = 0; /* 0 inv, 1 wear, 2 wield */

        if ((p = index(line, '\n')) != 0)
            *p = '\0';
        for (p = line; *p == ' ' || *p == '\t'; p++)
            ;
        if (!*p || *p == '#')
            continue;
        if (!strncmp(p, "wear ", 5))
            mode = 1, what = p + 5;
        else if (!strncmp(p, "wield ", 6))
            mode = 2, what = p + 6;
        else if (!strncmp(p, "inv ", 4))
            mode = 0, what = p + 4;
        else
            what = p;

        save_debug = flags.debug;
        flags.debug = TRUE; /* no enchantment/artifact wish limits */
        program_state.wizkit_wishing = 1;
        otmp = readobjnam(what, (struct obj *) 0);
        program_state.wizkit_wishing = 0;
        flags.debug = save_debug;

        if (!otmp || otmp == &zeroobj) {
            jstr(oname, sizeof oname, what);
            snprintf(body, sizeof body, "\"kind\":\"kit-error\",\"item\":%s",
                     oname);
            assist_emit(body);
            continue;
        }
        fully_identify_obj(otmp);
        otmp = addinv(otmp);
        if (mode == 1)
            kit_wear(otmp);
        else if (mode == 2 && otmp->oclass == WEAPON_CLASS)
            setuwep(otmp);
        jstr(oname, sizeof oname, doname(otmp));
        snprintf(body, sizeof body,
                 "\"kind\":\"kit\",\"item\":%s,\"mode\":\"%s\"", oname,
                 mode == 1 ? "wear" : mode == 2 ? "wield" : "inv");
        assist_emit(body);
    }
    (void) fclose(fp);
}

/* engine verdict, written before the end-of-game sequence runs */
void
assist_gameover(how)
int how;
{
    char buf[BUFSZ * 6], kname[BUFSZ], dname[BUFSZ], lvl[BUFSZ];
    s_level *sl = Is_special(&u.uz);

    assist_init();
    jstr(kname, sizeof kname, killer.name);
    jstr(dname, sizeof dname, dungeons[u.uz.dnum].dname);
    jstr(lvl, sizeof lvl, sl ? sl->proto : "");
    snprintf(buf, sizeof buf,
             "{\"t\":\"end\",\"how\":%d,\"how_s\":\"%s\",\"killer\":%s,"
             "\"turns\":%ld,\"depth\":%d,\"deepest\":%d,\"dnum\":%d,"
             "\"dname\":%s,\"special\":%s,\"xl\":%d,\"hp\":%d,\"hpmax\":%d,"
             "\"ascended\":%d,\"uevent_ascended\":%d,\"wizard\":%d,"
             "\"explore\":%d,\"lifesaves\":%ld,\"feeds\":%ld,"
             "\"nochoke\":%ld,\"brainsave\":%ld,\"noslime\":%ld,"
             "\"have_amulet\":%d,"
             "\"astral\":%d,"
             "\"ach\":{\"amulet\":%d,\"bell\":%d,\"book\":%d,\"menorah\":%d,"
             "\"gehennom\":%d,\"luckstone\":%d,\"sokoban\":%d,"
             "\"medusa\":%d,\"invoked\":%d,\"qcompleted\":%d}}",
             how, (how >= 0 && how <= ASCENDED) ? end_names[how] : "?",
             kname, moves, depth(&u.uz), (int) deepest_lev_reached(FALSE),
             (int) u.uz.dnum, dname, lvl, u.ulevel, u.uhp, u.uhpmax,
             how == ASCENDED ? 1 : 0, u.uevent.ascended ? 1 : 0,
             wizard ? 1 : 0, discover ? 1 : 0, a_count_lifesave,
             a_count_feed, a_count_choke, a_count_brain, a_count_slime,
             u.uhave.amulet ? 1 : 0,
             Is_astralevel(&u.uz) ? 1 : 0, u.uachieve.amulet,
             u.uachieve.bell, u.uachieve.book, u.uachieve.menorah,
             u.uachieve.enter_gehennom, u.uachieve.mines_luckstone,
             u.uachieve.finish_sokoban, u.uachieve.killed_medusa,
             u.uevent.invoked, u.uevent.qcompleted);
#ifdef BOT_GRAPHICS
    botwin_send_now(buf);
#endif
    if (a_logpath) {
        FILE *fp = fopen(a_logpath, "a");

        if (fp) {
            fprintf(fp, "%s\n", buf);
            fclose(fp);
        }
    }
}
