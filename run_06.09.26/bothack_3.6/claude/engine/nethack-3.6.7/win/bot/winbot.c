/* NetHack 3.6.7  winbot.c
 *
 * "bot" window port: a structured, synchronous JSON-lines protocol for
 * programs that play NetHack.  It replaces screen scraping entirely.
 *
 * Transport: the game writes one JSON object per line to the file
 * descriptor named by NH_BOT_OUT_FD (default 4) and reads one response line
 * per input request from NH_BOT_IN_FD (default 3).
 *
 * Every time the game needs input it sends a "req" object that carries
 *   - kind:   cmd | key | yn | line | ext | menu | pos
 *   - ev:     the ordered events since the previous request (messages,
 *             text windows, non-selectable menus, assist interventions ...)
 *   - map:    changed map cells [x, y, glyph, ch, color, special]
 *   - st:     the status line values
 *   - inv:    the inventory, only when it changed
 *   - u:      hero position
 *   - priv:   evaluation-only engine data (achievements, luck, alignment
 *             record ...).  The client harness must strip it before handing
 *             the observation to a policy; it exists for logging/verdicts.
 * and the client answers with exactly one line:
 *   k <code>              key (cmd/key requests)
 *   y <code> [<number>]   yn_function answer (number for '#' answers)
 *   l <text>              getlin text
 *   x <name>              extended command name
 *   m [<id>[:<count>]...] menu selection (ids from the request)
 *   p <x> <y>             getpos answer
 *   e                     escape / cancel, valid for every kind
 *
 * Object glyphs of unidentified types are masked (glyph -1): the numeric
 * glyph would otherwise reveal the object's real identity.
 */

#include "hack.h"
#include "func_tab.h"
#include "winbot.h"

#include "patchlevel.h"

#include <errno.h>
#include <stdarg.h>
#include <unistd.h>

#ifdef BOT_GRAPHICS

/* ------------------------------------------------------------------ state */

#define BOT_MAXWIN 64
#define BOT_LINE_MAX 8192

struct bot_menu_item {
    int glyph;
    anything identifier;
    char acc, gacc;
    int attr;
    char *text;
    boolean presel;
};

struct bot_win {
    boolean used;
    int type;
    char **lines;
    int nlines, maxlines;
    struct bot_menu_item *items;
    int nitems, maxitems;
    char *prompt;
};

struct bot_cell {
    int glyph, ch, color;
    unsigned special;
};

static struct bot_win bwins[BOT_MAXWIN];
static struct bot_cell disp[ROWNO][COLNO], sent[ROWNO][COLNO];
static boolean map_force_full = TRUE;
static FILE *bot_out = (FILE *) 0;
static FILE *bot_in = (FILE *) 0;
static long req_seq = 0;
static int cursx, cursy;

/* pending events serialized as JSON array elements */
static char *evbuf = (char *) 0;
static size_t evlen = 0, evcap = 0;

/* last inventory sent (serialized) */
static char *last_inv = (char *) 0;

boolean botwin_active = FALSE;
long botwin_parse_serial = 0L; /* incremented by cmd.c:parse() */
static long last_parse_serial = -1L;

struct window_procs bot_procs = {
    "bot",
    WC_COLOR | WC_HILITE_PET | WC_INVERSE,
    0L,
    { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 },
    bot_init_nhwindows, bot_player_selection, bot_askname,
    bot_get_nh_event, bot_exit_nhwindows, bot_suspend_nhwindows,
    bot_resume_nhwindows, bot_create_nhwindow, bot_clear_nhwindow,
    bot_display_nhwindow, bot_destroy_nhwindow, bot_curs, bot_putstr,
    genl_putmixed, bot_display_file, bot_start_menu, bot_add_menu,
    bot_end_menu, bot_select_menu, genl_message_menu, bot_update_inventory,
    bot_mark_synch, bot_wait_synch,
#ifdef CLIPPING
    bot_cliparound,
#endif
#ifdef POSITIONBAR
    bot_update_positionbar,
#endif
    bot_print_glyph, bot_raw_print, bot_raw_print_bold, bot_nhgetch,
    bot_nh_poskey, bot_nhbell, bot_doprev_message, bot_yn_function,
    bot_getlin, bot_get_ext_cmd, bot_number_pad, bot_delay_output,
#ifdef CHANGE_COLOR
    bot_change_color,
#ifdef MAC
    bot_change_background, bot_set_font_name,
#endif
    bot_get_color_string,
#endif
    bot_start_screen, bot_end_screen, genl_outrip,
    genl_preference_update, genl_getmsghistory, genl_putmsghistory,
    genl_status_init, genl_status_finish, genl_status_enablefield,
    genl_status_update, genl_can_suspend_no,
};

/* ----------------------------------------------------------- JSON output */

struct sbuf {
    char *s;
    size_t len, cap;
};

static void
sb_grow(sb, need)
struct sbuf *sb;
size_t need;
{
    if (sb->len + need + 1 > sb->cap) {
        size_t ncap = sb->cap ? sb->cap : 1024;

        while (sb->len + need + 1 > ncap)
            ncap *= 2;
        sb->s = (char *) realloc(sb->s, ncap);
        if (!sb->s) {
            fprintf(stderr, "winbot: out of memory\n");
            exit(EXIT_FAILURE);
        }
        sb->cap = ncap;
    }
}

static void
sb_add(sb, str)
struct sbuf *sb;
const char *str;
{
    size_t n = strlen(str);

    sb_grow(sb, n);
    memcpy(sb->s + sb->len, str, n);
    sb->len += n;
    sb->s[sb->len] = '\0';
}

static void
sb_addc(sb, c)
struct sbuf *sb;
char c;
{
    sb_grow(sb, 1);
    sb->s[sb->len++] = c;
    sb->s[sb->len] = '\0';
}

static void
sb_printf(struct sbuf *sb, const char *fmt, ...)
{
    char tmp[512];
    va_list ap;

    va_start(ap, fmt);
    vsnprintf(tmp, sizeof tmp, fmt, ap);
    va_end(ap);
    sb_add(sb, tmp);
}

static void
sb_str(sb, str)
struct sbuf *sb;
const char *str;
{
    const unsigned char *p;
    char tmp[8];

    sb_addc(sb, '"');
    if (str)
        for (p = (const unsigned char *) str; *p; p++) {
            if (*p == '"' || *p == '\\') {
                sb_addc(sb, '\\');
                sb_addc(sb, (char) *p);
            } else if (*p < 0x20 || *p >= 0x7f) {
                Sprintf(tmp, "\\u%04x", (unsigned) *p);
                sb_add(sb, tmp);
            } else {
                sb_addc(sb, (char) *p);
            }
        }
    sb_addc(sb, '"');
}

static void
sb_free(sb)
struct sbuf *sb;
{
    free(sb->s);
    sb->s = 0;
    sb->len = sb->cap = 0;
}

/* append a serialized event (already a JSON value) to the pending list */
static void
ev_push(json)
const char *json;
{
    size_t n = strlen(json);

    if (evlen + n + 2 > evcap) {
        size_t ncap = evcap ? evcap : 4096;

        while (evlen + n + 2 > ncap)
            ncap *= 2;
        evbuf = (char *) realloc(evbuf, ncap);
        if (!evbuf) {
            fprintf(stderr, "winbot: out of memory\n");
            exit(EXIT_FAILURE);
        }
        evcap = ncap;
    }
    if (evlen)
        evbuf[evlen++] = ',';
    memcpy(evbuf + evlen, json, n);
    evlen += n;
    evbuf[evlen] = '\0';
}

static void
ev_simple(kind, text)
const char *kind, *text;
{
    struct sbuf sb = { 0, 0, 0 };

    sb_addc(&sb, '[');
    sb_str(&sb, kind);
    if (text) {
        sb_addc(&sb, ',');
        sb_str(&sb, text);
    }
    sb_addc(&sb, ']');
    ev_push(sb.s);
    sb_free(&sb);
}

/* public: write a complete JSON line right now (engine verdict) */
void
botwin_send_now(json)
const char *json;
{
    if (botwin_active && bot_out) {
        fputs(json, bot_out);
        fputc('\n', bot_out);
        fflush(bot_out);
    }
}

/* public: used by botassist.c and end.c hooks */
void
botwin_event_json(json)
const char *json;
{
    if (botwin_active)
        ev_push(json);
}

static void
bot_write_line(s)
const char *s;
{
    if (!bot_out)
        return;
    fputs(s, bot_out);
    fputc('\n', bot_out);
    fflush(bot_out);
}

/* ------------------------------------------------------------ serializers */

static void
ser_status(sb)
struct sbuf *sb;
{
    char lvl[BUFSZ];
    int hp = Upolyd ? u.mh : u.uhp, hpmax = Upolyd ? u.mhmax : u.uhpmax;
    long cond = 0L;

    lvl[0] = '\0';
    (void) describe_level(lvl);
    /* condition bits, same meaning as botl.c BL_MASK_* */
    if (Stoned) cond |= 0x0001L;
    if (Slimed) cond |= 0x0002L;
    if (Strangled) cond |= 0x0004L;
    if (Sick && (u.usick_type & SICK_VOMITABLE)) cond |= 0x0008L;
    if (Sick && (u.usick_type & SICK_NONVOMITABLE)) cond |= 0x0010L;
    if (Blind) cond |= 0x0020L;
    if (Deaf) cond |= 0x0040L;
    if (Stunned) cond |= 0x0080L;
    if (Confusion) cond |= 0x0100L;
    if (Hallucination) cond |= 0x0200L;
    if (Levitation) cond |= 0x0400L;
    if (Flying) cond |= 0x0800L;
    if (u.usteed) cond |= 0x1000L;

    sb_add(sb, "\"st\":{");
    sb_printf(sb, "\"hp\":%d,\"hpmax\":%d,\"pw\":%d,\"pwmax\":%d,", hp, hpmax,
              u.uen, u.uenmax);
    sb_printf(sb, "\"ac\":%d,\"xl\":%d,\"exp\":%ld,\"gold\":%ld,",
              u.uac, Upolyd ? mons[u.umonnum].mlevel : u.ulevel, u.uexp,
              money_cnt(invent));
    sb_printf(sb, "\"turn\":%ld,\"hunger\":%d,\"enc\":%d,\"cond\":%ld,",
              moves, (int) u.uhs, near_capacity(), cond);
    sb_printf(sb,
              "\"str\":%d,\"dex\":%d,\"con\":%d,\"int\":%d,\"wis\":%d,"
              "\"cha\":%d,",
              ACURR(A_STR), ACURR(A_DEX), ACURR(A_CON), ACURR(A_INT),
              ACURR(A_WIS), ACURR(A_CHA));
    sb_printf(sb, "\"align\":%d,\"depth\":%d,\"dnum\":%d,\"dlevel\":%d,",
              (int) u.ualign.type, depth(&u.uz), (int) u.uz.dnum,
              (int) u.uz.dlevel);
    sb_printf(sb, "\"poly\":%d,\"score\":%ld,", Upolyd ? 1 : 0,
#ifndef SCORE_ON_BOTL
              0L
#else
              botl_score()
#endif
              );
    sb_add(sb, "\"lvl\":");
    sb_str(sb, lvl);
    sb_add(sb, ",\"title\":");
    /* like the tty status line: the monster form replaces the rank title
       while polymorphed (BotHack reads the form from it) */
    sb_str(sb, Upolyd ? mons[u.umonnum].mname
                      : rank_of(u.ulevel, Role_switch, flags.female));
    sb_add(sb, ",\"dname\":");
    sb_str(sb, dungeons[u.uz.dnum].dname);
    sb_add(sb, "}");
}

static void
ser_priv(sb)
struct sbuf *sb;
{
    s_level *sl = Is_special(&u.uz);

    sb_add(sb, "\"priv\":{");
    sb_printf(sb, "\"luck\":%d,\"align_rec\":%ld,\"pray_timeout\":%ld,",
              (int) Luck, (long) u.ualign.record, (long) u.ublesscnt);
    sb_printf(sb, "\"ugangr\":%d,\"deepest\":%d,\"mortality\":%ld,",
              (int) u.ugangr, (int) deepest_lev_reached(FALSE),
              (long) u.umortality);
    sb_printf(sb,
              "\"ach\":{\"amulet\":%d,\"bell\":%d,\"book\":%d,"
              "\"menorah\":%d,\"gehennom\":%d,\"ascended\":%d,"
              "\"luckstone\":%d,\"sokoban\":%d,\"medusa\":%d},",
              u.uachieve.amulet, u.uachieve.bell, u.uachieve.book,
              u.uachieve.menorah, u.uachieve.enter_gehennom,
              u.uachieve.ascended, u.uachieve.mines_luckstone,
              u.uachieve.finish_sokoban, u.uachieve.killed_medusa);
    sb_printf(sb,
              "\"evt\":{\"qcalled\":%d,\"qexpelled\":%d,\"qcompleted\":%d,"
              "\"invoked\":%d,\"udemigod\":%d,\"uvibrated\":%d,"
              "\"minor_oracle\":%d,\"major_oracle\":%d},",
              u.uevent.qcalled, u.uevent.qexpelled, u.uevent.qcompleted,
              u.uevent.invoked, u.uevent.udemigod, u.uevent.uvibrated,
              u.uevent.minor_oracle, u.uevent.major_oracle);
    sb_printf(sb, "\"endgame\":%d,\"astral\":%d,\"inhell\":%d,",
              In_endgame(&u.uz) ? 1 : 0, Is_astralevel(&u.uz) ? 1 : 0,
              Inhell ? 1 : 0);
    sb_printf(sb, "\"have_amulet\":%d,\"wizard\":%d,\"explore\":%d,",
              u.uhave.amulet ? 1 : 0, wizard ? 1 : 0, discover ? 1 : 0);
    sb_add(sb, "\"special\":");
    sb_str(sb, sl ? sl->proto : "");
    sb_add(sb, "}");
}

static char *
ser_inventory()
{
    struct sbuf sb = { 0, 0, 0 };
    struct obj *otmp;
    boolean first = TRUE;
    char let[2];

    sb_addc(&sb, '[');
    for (otmp = invent; otmp; otmp = otmp->nobj) {
        if (!first)
            sb_addc(&sb, ',');
        first = FALSE;
        let[0] = otmp->invlet;
        let[1] = '\0';
        sb_add(&sb, "[");
        sb_str(&sb, let);
        sb_addc(&sb, ',');
        sb_str(&sb, doname(otmp));
        sb_printf(&sb, ",%d,%ld,%ld]", (int) def_oc_syms[(int) otmp->oclass].sym,
                  otmp->quan, otmp->owornmask);
    }
    sb_addc(&sb, ']');
    return sb.s;
}

static void
ser_map(sb)
struct sbuf *sb;
{
    int x, y;
    boolean first = TRUE;

    sb_add(sb, "\"map\":[");
    for (y = 0; y < ROWNO; y++)
        for (x = 1; x < COLNO; x++) {
            struct bot_cell *c = &disp[y][x], *s = &sent[y][x];

            if (!map_force_full && c->glyph == s->glyph && c->ch == s->ch
                && c->color == s->color && c->special == s->special)
                continue;
            *s = *c;
            if (!first)
                sb_addc(sb, ',');
            first = FALSE;
            sb_printf(sb, "[%d,%d,%d,%d,%d,%u]", x, y, c->glyph, c->ch,
                      c->color, c->special);
        }
    sb_addc(sb, ']');
    map_force_full = FALSE;
}

/* ------------------------------------------------------------ request I/O */

static char inbuf[BOT_LINE_MAX];

static void
bot_hangup()
{
    /* the controller went away: terminate without saving */
    if (bot_out) {
        fclose(bot_out);
        bot_out = 0;
    }
    fprintf(stderr, "winbot: controller closed the input channel\n");
    nh_terminate(EXIT_FAILURE);
}

/* Build and send a request; read the reply into inbuf.  `extra` is a JSON
   fragment (without surrounding braces) describing the request kind. */
static const char *
bot_request(kind, extra)
const char *kind;
const char *extra;
{
    struct sbuf sb = { 0, 0, 0 };
    char *inv;
    size_t n;

    if (!bot_out || !bot_in)
        bot_hangup();
    assist_track();

    sb_printf(&sb, "{\"t\":\"req\",\"seq\":%ld,\"kind\":", ++req_seq);
    sb_str(&sb, kind);
    if (extra && *extra) {
        sb_addc(&sb, ',');
        sb_add(&sb, extra);
    }
    sb_add(&sb, ",\"ev\":[");
    if (evlen)
        sb_add(&sb, evbuf);
    sb_add(&sb, "],");
    evlen = 0;
    if (evbuf)
        evbuf[0] = '\0';

    if (program_state.in_moveloop || u.ux) {
        ser_map(&sb);
        sb_addc(&sb, ',');
        ser_status(&sb);
        sb_addc(&sb, ',');
        ser_priv(&sb);
        inv = ser_inventory();
        if (!last_inv || strcmp(inv, last_inv)) {
            sb_add(&sb, ",\"inv\":");
            sb_add(&sb, inv);
            free(last_inv);
            last_inv = inv;
        } else {
            free(inv);
        }
        sb_printf(&sb, ",\"u\":[%d,%d],\"curs\":[%d,%d]", u.ux, u.uy, cursx,
                  cursy);
    } else {
        sb_add(&sb, "\"pregame\":1");
    }
    sb_addc(&sb, '}');
    bot_write_line(sb.s);
    sb_free(&sb);

    if (!fgets(inbuf, sizeof inbuf, bot_in))
        bot_hangup();
    n = strlen(inbuf);
    while (n && (inbuf[n - 1] == '\n' || inbuf[n - 1] == '\r'))
        inbuf[--n] = '\0';
    return inbuf;
}

static void
ev_protoerr(what, got)
const char *what, *got;
{
    struct sbuf sb = { 0, 0, 0 };

    sb_add(&sb, "[\"protoerr\",");
    sb_str(&sb, what);
    sb_addc(&sb, ',');
    sb_str(&sb, got);
    sb_addc(&sb, ']');
    ev_push(sb.s);
    sb_free(&sb);
}

/* ---------------------------------------------------------- window procs */

void
bot_init_nhwindows(argcp, argv)
int *argcp;
char **argv;
{
    const char *s;
    int infd = 3, outfd = 4, i;
    struct sbuf sb = { 0, 0, 0 };

    nhUse(argcp);
    nhUse(argv);
    if ((s = nh_getenv("NH_BOT_IN_FD")) != 0)
        infd = atoi(s);
    if ((s = nh_getenv("NH_BOT_OUT_FD")) != 0)
        outfd = atoi(s);
    bot_in = fdopen(infd, "r");
    bot_out = fdopen(outfd, "w");
    if (!bot_in || !bot_out) {
        fprintf(stderr, "winbot: cannot open protocol fds %d/%d: %s\n", infd,
                outfd, strerror(errno));
        exit(EXIT_FAILURE);
    }
    botwin_active = TRUE;
    for (i = 0; i < BOT_MAXWIN; i++)
        bwins[i].used = FALSE;

    /* static data the client needs to decode glyphs */
    sb_add(&sb, "{\"t\":\"hello\",\"proto\":1,");
    sb_printf(&sb,
              "\"version\":\"%d.%d.%d\",\"nummons\":%d,\"numobj\":%d,"
              "\"maxpchars\":%d,",
              VERSION_MAJOR, VERSION_MINOR, PATCHLEVEL, NUMMONS, NUM_OBJECTS,
              MAXPCHARS);
    sb_printf(&sb,
              "\"off\":{\"mon\":%d,\"pet\":%d,\"invis\":%d,\"detect\":%d,"
              "\"body\":%d,\"ridden\":%d,\"obj\":%d,\"cmap\":%d,"
              "\"explode\":%d,\"zap\":%d,\"swallow\":%d,\"warning\":%d,"
              "\"statue\":%d,\"max\":%d},",
              GLYPH_MON_OFF, GLYPH_PET_OFF, GLYPH_INVIS_OFF, GLYPH_DETECT_OFF,
              GLYPH_BODY_OFF, GLYPH_RIDDEN_OFF, GLYPH_OBJ_OFF, GLYPH_CMAP_OFF,
              GLYPH_EXPLODE_OFF, GLYPH_ZAP_OFF, GLYPH_SWALLOW_OFF,
              GLYPH_WARNING_OFF, GLYPH_STATUE_OFF, MAX_GLYPH);
    sb_add(&sb, "\"mons\":[");
    for (i = 0; i < NUMMONS; i++) {
        char sym[2];

        sym[0] = def_monsyms[(int) mons[i].mlet].sym;
        sym[1] = '\0';
        if (i)
            sb_addc(&sb, ',');
        sb_addc(&sb, '[');
        sb_str(&sb, mons[i].mname);
        sb_addc(&sb, ',');
        sb_str(&sb, sym);
        sb_printf(&sb, ",%d]", (int) mons[i].mcolor);
    }
    sb_add(&sb, "],\"objs\":[");
    for (i = 0; i < NUM_OBJECTS; i++) {
        char sym[2];

        sym[0] = def_oc_syms[(int) objects[i].oc_class].sym;
        sym[1] = '\0';
        if (i)
            sb_addc(&sb, ',');
        sb_addc(&sb, '[');
        /* obj_descr[] is the static (unshuffled) table; OBJ_NAME() is not
           usable yet, init_objects() has not run when hello is sent */
        sb_str(&sb, obj_descr[i].oc_name ? obj_descr[i].oc_name : "");
        sb_addc(&sb, ',');
        sb_str(&sb, sym);
        sb_addc(&sb, ']');
    }
    sb_add(&sb, "],\"cmap\":[");
    for (i = 0; i < MAXPCHARS; i++) {
        char sym[2];

        sym[0] = defsyms[i].sym;
        sym[1] = '\0';
        if (i)
            sb_addc(&sb, ',');
        sb_addc(&sb, '[');
        sb_str(&sb, sym);
        sb_addc(&sb, ',');
        sb_str(&sb, defsyms[i].explanation);
        sb_printf(&sb, ",%d]", (int) defsyms[i].color);
    }
    sb_add(&sb, "]}");
    bot_write_line(sb.s);
    sb_free(&sb);
    iflags.window_inited = TRUE;
}

void
bot_player_selection()
{
    rigid_role_checks();
    if (flags.initrole < 0)
        flags.initrole = pick_role(flags.initrace, flags.initgend,
                                   flags.initalign, PICK_RANDOM);
    if (flags.initrole < 0)
        flags.initrole = randrole(FALSE);
    if (flags.initrace < 0)
        flags.initrace = pick_race(flags.initrole, flags.initgend,
                                   flags.initalign, PICK_RANDOM);
    if (flags.initrace < 0)
        flags.initrace = randrace(flags.initrole);
    if (flags.initalign < 0)
        flags.initalign = pick_align(flags.initrole, flags.initrace,
                                     flags.initgend, PICK_RANDOM);
    if (flags.initalign < 0)
        flags.initalign = randalign(flags.initrole, flags.initrace);
    if (flags.initgend < 0)
        flags.initgend = pick_gend(flags.initrole, flags.initrace,
                                   flags.initalign, PICK_RANDOM);
    if (flags.initgend < 0)
        flags.initgend = randgend(flags.initrole, flags.initrace);
}

void
bot_askname()
{
    if (!*plname)
        Strcpy(plname, "bot");
}

void
bot_get_nh_event()
{
    return;
}

void
bot_exit_nhwindows(str)
const char *str;
{
    struct sbuf sb = { 0, 0, 0 };

    if (!bot_out)
        return;
    sb_add(&sb, "{\"t\":\"bye\",\"ev\":[");
    if (evlen)
        sb_add(&sb, evbuf);
    evlen = 0;
    sb_add(&sb, "],\"msg\":");
    sb_str(&sb, str ? str : "");
    sb_addc(&sb, '}');
    bot_write_line(sb.s);
    sb_free(&sb);
    iflags.window_inited = FALSE;
}

void
bot_suspend_nhwindows(str)
const char *str;
{
    nhUse(str);
}

void
bot_resume_nhwindows()
{
    return;
}

winid
bot_create_nhwindow(type)
int type;
{
    int i;

    for (i = 0; i < BOT_MAXWIN; i++)
        if (!bwins[i].used)
            break;
    if (i == BOT_MAXWIN)
        panic("winbot: out of windows");
    memset(&bwins[i], 0, sizeof bwins[i]);
    bwins[i].used = TRUE;
    bwins[i].type = type;
    return (winid) i;
}

static void
win_reset(w)
struct bot_win *w;
{
    int i;

    for (i = 0; i < w->nlines; i++)
        free(w->lines[i]);
    w->nlines = 0;
    for (i = 0; i < w->nitems; i++)
        free(w->items[i].text);
    w->nitems = 0;
    free(w->prompt);
    w->prompt = 0;
}

void
bot_clear_nhwindow(window)
winid window;
{
    int x, y;

    if (window < 0 || window >= BOT_MAXWIN || !bwins[window].used)
        return;
    if (bwins[window].type == NHW_MAP) {
        for (y = 0; y < ROWNO; y++)
            for (x = 0; x < COLNO; x++) {
                disp[y][x].glyph = cmap_to_glyph(S_stone);
                disp[y][x].ch = ' ';
                disp[y][x].color = NO_COLOR;
                disp[y][x].special = 0;
            }
        ev_simple("clear_map", (char *) 0);
    } else if (bwins[window].type != NHW_MESSAGE
               && bwins[window].type != NHW_STATUS) {
        win_reset(&bwins[window]);
    }
}

static void
ev_lines(kind, w)
const char *kind;
struct bot_win *w;
{
    struct sbuf sb = { 0, 0, 0 };
    int i;

    sb_add(&sb, "[");
    sb_str(&sb, kind);
    sb_add(&sb, ",[");
    for (i = 0; i < w->nlines; i++) {
        if (i)
            sb_addc(&sb, ',');
        sb_str(&sb, w->lines[i]);
    }
    sb_add(&sb, "]]");
    ev_push(sb.s);
    sb_free(&sb);
}

void
bot_display_nhwindow(window, blocking)
winid window;
boolean blocking;
{
    struct bot_win *w;

    nhUse(blocking);
    if (window < 0 || window >= BOT_MAXWIN || !bwins[window].used)
        return;
    w = &bwins[window];
    if (w->type == NHW_TEXT || w->type == NHW_MENU) {
        if (w->nlines) {
            ev_lines("text", w);
            /* displayed text is consumed; a re-display would duplicate it */
            win_reset(w);
        }
    }
}

void
bot_destroy_nhwindow(window)
winid window;
{
    if (window < 0 || window >= BOT_MAXWIN || !bwins[window].used)
        return;
    if (window == WIN_MESSAGE || window == WIN_MAP || window == WIN_STATUS)
        return; /* core windows live for the whole game */
    win_reset(&bwins[window]);
    free(bwins[window].lines);
    free(bwins[window].items);
    memset(&bwins[window], 0, sizeof bwins[window]);
}

void
bot_curs(window, x, y)
winid window;
int x, y;
{
    if (window == WIN_MAP) {
        cursx = x;
        cursy = y;
    }
}

void
bot_putstr(window, attr, str)
winid window;
int attr;
const char *str;
{
    struct bot_win *w;

    nhUse(attr);
    if (!str)
        return;
    if (window == WIN_MESSAGE) {
        ev_simple("msg", str);
        return;
    }
    if (window < 0 || window >= BOT_MAXWIN || !bwins[window].used)
        return;
    w = &bwins[window];
    if (w->type == NHW_STATUS || w->type == NHW_MAP)
        return;
    if (w->nlines == w->maxlines) {
        w->maxlines = w->maxlines ? 2 * w->maxlines : 16;
        w->lines = (char **) realloc(w->lines, w->maxlines * sizeof(char *));
    }
    w->lines[w->nlines++] = dupstr(str);
}

void
bot_display_file(fname, complain)
const char *fname;
boolean complain;
{
    nhUse(complain);
    ev_simple("file", fname);
}

void
bot_start_menu(window)
winid window;
{
    if (window < 0 || window >= BOT_MAXWIN || !bwins[window].used)
        return;
    win_reset(&bwins[window]);
    bwins[window].type = NHW_MENU;
}

void
bot_add_menu(window, glyph, identifier, ch, gch, attr, str, preselected)
winid window;
int glyph;
const anything *identifier;
char ch, gch;
int attr;
const char *str;
boolean preselected;
{
    struct bot_win *w;
    struct bot_menu_item *it;

    if (window < 0 || window >= BOT_MAXWIN || !bwins[window].used)
        return;
    w = &bwins[window];
    if (w->nitems == w->maxitems) {
        w->maxitems = w->maxitems ? 2 * w->maxitems : 32;
        w->items = (struct bot_menu_item *) realloc(
            w->items, w->maxitems * sizeof(struct bot_menu_item));
    }
    it = &w->items[w->nitems++];
    it->glyph = glyph;
    it->identifier = *identifier;
    it->acc = ch;
    it->gacc = gch;
    it->attr = attr;
    it->text = dupstr(str ? str : "");
    it->presel = preselected;
}

void
bot_end_menu(window, prompt)
winid window;
const char *prompt;
{
    struct bot_win *w;
    int i;
    char next = 'a';

    if (window < 0 || window >= BOT_MAXWIN || !bwins[window].used)
        return;
    w = &bwins[window];
    free(w->prompt);
    w->prompt = prompt ? dupstr(prompt) : 0;
    /* assign accelerators like tty does for items that lack one; tty
       restarts on each page, we keep going and wrap after 'Z' */
    for (i = 0; i < w->nitems; i++) {
        struct bot_menu_item *it = &w->items[i];

        if (it->identifier.a_void && !it->acc) {
            it->acc = next;
            if (next == 'z')
                next = 'A';
            else if (next == 'Z')
                next = 'a';
            else
                next++;
        }
    }
}

int
bot_select_menu(window, how, menu_list)
winid window;
int how;
menu_item **menu_list;
{
    struct bot_win *w;
    struct sbuf sb = { 0, 0, 0 };
    const char *reply;
    int i, n = 0;
    char acc[2];

    *menu_list = (menu_item *) 0;
    if (window < 0 || window >= BOT_MAXWIN || !bwins[window].used)
        return -1;
    w = &bwins[window];

    if (how == PICK_NONE) {
        /* display only: report it as a text event, no input needed */
        sb_add(&sb, "[\"menu_show\",");
        sb_str(&sb, w->prompt ? w->prompt : "");
        sb_add(&sb, ",[");
        for (i = 0; i < w->nitems; i++) {
            acc[0] = w->items[i].acc;
            acc[1] = '\0';
            if (i)
                sb_addc(&sb, ',');
            sb_printf(&sb, "[%d,", w->items[i].identifier.a_void ? 1 : 0);
            sb_str(&sb, acc);
            sb_addc(&sb, ',');
            sb_str(&sb, w->items[i].text);
            sb_addc(&sb, ']');
        }
        sb_add(&sb, "]]");
        ev_push(sb.s);
        sb_free(&sb);
        return 0;
    }

    sb_add(&sb, "\"prompt\":");
    sb_str(&sb, w->prompt ? w->prompt : "");
    sb_printf(&sb, ",\"how\":%d,\"items\":[", how);
    for (i = 0; i < w->nitems; i++) {
        struct bot_menu_item *it = &w->items[i];

        acc[0] = it->acc;
        acc[1] = '\0';
        if (i)
            sb_addc(&sb, ',');
        sb_printf(&sb, "[%d,%d,", i, it->identifier.a_void ? 1 : 0);
        sb_str(&sb, acc);
        acc[0] = it->gacc;
        sb_addc(&sb, ',');
        sb_str(&sb, acc);
        sb_printf(&sb, ",%d,%d,", it->attr, it->presel ? 1 : 0);
        sb_str(&sb, it->text);
        sb_addc(&sb, ']');
    }
    sb_addc(&sb, ']');
    reply = bot_request("menu", sb.s);
    sb_free(&sb);

    if (reply[0] == 'e' && (!reply[1] || reply[1] == ' '))
        return -1;
    if (reply[0] != 'm') {
        ev_protoerr("menu", reply);
        return -1;
    }
    {
        const char *p = reply + 1;
        menu_item *mi = (menu_item *) alloc(sizeof(menu_item)
                                            * (unsigned) (w->nitems + 1));

        while (*p) {
            long id, cnt = -1L;
            char *endp;

            while (*p == ' ')
                p++;
            if (!*p)
                break;
            id = strtol(p, &endp, 10);
            if (endp == p) {
                ev_protoerr("menu-parse", reply);
                break;
            }
            p = endp;
            if (*p == ':') {
                cnt = strtol(p + 1, &endp, 10);
                p = endp;
            }
            if (id < 0 || id >= w->nitems || !w->items[id].identifier.a_void) {
                ev_protoerr("menu-id", reply);
                continue;
            }
            if (how == PICK_ONE && n >= 1)
                break;
            mi[n].item = w->items[id].identifier;
            mi[n].count = cnt;
            n++;
        }
        if (n == 0) {
            free((genericptr_t) mi);
            return 0;
        }
        *menu_list = mi;
    }
    return n;
}

void
bot_update_inventory()
{
    return; /* inventory is diffed at every request */
}

void
bot_mark_synch()
{
    return;
}

void
bot_wait_synch()
{
    return;
}

#ifdef CLIPPING
void
bot_cliparound(x, y)
int x, y;
{
    nhUse(x);
    nhUse(y);
}
#endif

#ifdef POSITIONBAR
void
bot_update_positionbar(posbar)
char *posbar;
{
    nhUse(posbar);
}
#endif

void
bot_print_glyph(window, x, y, glyph, bkglyph)
winid window;
xchar x, y;
int glyph, bkglyph;
{
    int ch, color;
    unsigned special;
    struct bot_cell *c;

    nhUse(bkglyph);
    if (window != WIN_MAP || x < 0 || x >= COLNO || y < 0 || y >= ROWNO)
        return;
    (void) mapglyph(glyph, &ch, &color, &special, x, y, 0);
    c = &disp[y][x];
    /* do not leak the identity of unidentified object types */
    if (glyph_is_object(glyph)) {
        int otyp = glyph_to_obj(glyph);

        if (OBJ_DESCR(objects[otyp]) && !objects[otyp].oc_name_known)
            glyph = -1;
    }
    c->glyph = glyph;
    c->ch = ch;
    c->color = color;
    c->special = special;
}

void
bot_raw_print(str)
const char *str;
{
    if (str)
        fprintf(stderr, "%s\n", str);
    if (botwin_active && str)
        ev_simple("raw", str);
}

void
bot_raw_print_bold(str)
const char *str;
{
    bot_raw_print(str);
}

static int
bot_key_request(kind)
const char *kind;
{
    const char *reply;
    long v;

    for (;;) {
        reply = bot_request(kind, (char *) 0);
        if (reply[0] == 'e' && (!reply[1] || reply[1] == ' '))
            return '\033';
        if (reply[0] == 'k' && reply[1] == ' ') {
            v = atol(reply + 2);
            if (v > 0 && v < 256)
                return (int) v;
        }
        ev_protoerr(kind, reply);
        /* an invalid answer to a command request is dangerous to guess;
           ask again (the protoerr event tells the client what happened) */
    }
}

int
bot_nhgetch()
{
    /* "cmd": first key of a new command; "cmdcont": count digits and
       prefix continuations read by the same parse(); "key": anything else */
    if (iflags.in_parse) {
        if (botwin_parse_serial != last_parse_serial) {
            last_parse_serial = botwin_parse_serial;
            return bot_key_request("cmd");
        }
        return bot_key_request("cmdcont");
    }
    return bot_key_request("key");
}

int
bot_nh_poskey(x, y, mod)
int *x, *y, *mod;
{
    *x = *y = *mod = 0;
    return bot_nhgetch();
}

void
bot_nhbell()
{
    return;
}

int
bot_doprev_message()
{
    return 0;
}

char
bot_yn_function(query, resp, def)
const char *query, *resp;
char def;
{
    struct sbuf sb = { 0, 0, 0 };
    const char *reply;
    char q = 0;
    char dstr[2];

    yn_number = 0L;
    sb_add(&sb, "\"query\":");
    sb_str(&sb, query ? query : "");
    sb_add(&sb, ",\"choices\":");
    if (resp)
        sb_str(&sb, resp);
    else
        sb_add(&sb, "null");
    dstr[0] = def;
    dstr[1] = '\0';
    sb_add(&sb, ",\"default\":");
    sb_str(&sb, dstr);
    reply = bot_request("yn", sb.s);
    sb_free(&sb);

    if (reply[0] == 'e' && (!reply[1] || reply[1] == ' ')) {
        q = '\033';
    } else if (reply[0] == 'y' && reply[1] == ' ') {
        char *endp;
        long v = strtol(reply + 2, &endp, 10);

        q = (v > 0 && v < 256) ? (char) v : '\033';
        if (*endp == ' ')
            yn_number = atol(endp + 1);
    } else {
        ev_protoerr("yn", reply);
        q = '\033';
    }
    if (!resp)
        return q;
    if (q == '\033') {
        if (index(resp, 'q'))
            return 'q';
        if (index(resp, 'n'))
            return 'n';
        return def;
    }
    if (index(quitchars, q))
        return def;
    if (q == '#' && index(resp, '#'))
        return '#';
    if (!index(resp, q)) {
        ev_protoerr("yn-choice", reply);
        if (index(resp, 'q'))
            return 'q';
        if (index(resp, 'n'))
            return 'n';
        return def;
    }
    return q;
}

void
bot_getlin(query, bufp)
const char *query;
char *bufp;
{
    struct sbuf sb = { 0, 0, 0 };
    const char *reply;

    sb_add(&sb, "\"query\":");
    sb_str(&sb, query ? query : "");
    reply = bot_request("line", sb.s);
    sb_free(&sb);
    if (reply[0] == 'l' && (reply[1] == ' ' || !reply[1])) {
        (void) strncpy(bufp, reply[1] ? reply + 2 : "", BUFSZ - 1);
        bufp[BUFSZ - 1] = '\0';
    } else {
        if (!(reply[0] == 'e' && (!reply[1] || reply[1] == ' ')))
            ev_protoerr("line", reply);
        Strcpy(bufp, "\033");
    }
}

int
bot_get_ext_cmd()
{
    const char *reply;
    int i;

    reply = bot_request("ext", (char *) 0);
    if (reply[0] == 'x' && reply[1] == ' ') {
        for (i = 0; extcmdlist[i].ef_txt; i++)
            if (!strcmpi(reply + 2, extcmdlist[i].ef_txt))
                return i;
        ev_protoerr("ext-unknown", reply);
        return -1;
    }
    if (!(reply[0] == 'e' && (!reply[1] || reply[1] == ' ')))
        ev_protoerr("ext", reply);
    return -1;
}

/* called by getpos() in do_name.c; returns 0 on success, -1 on escape.
   Like the tty getpos(), an escape aborts even when `force' is set (force
   only matters for the interactive validation of the picked spot). */
int
botwin_getpos(ccp, force, goal)
coord *ccp;
boolean force;
const char *goal;
{
    struct sbuf sb = { 0, 0, 0 };
    const char *reply;
    int x, y;

    sb_add(&sb, "\"goal\":");
    sb_str(&sb, goal ? goal : "desired location");
    sb_printf(&sb, ",\"cx\":%d,\"cy\":%d,\"force\":%d", ccp->x, ccp->y,
              force ? 1 : 0);
    reply = bot_request("pos", sb.s);
    sb_free(&sb);
    if (reply[0] == 'p' && sscanf(reply + 1, "%d %d", &x, &y) == 2
        && isok(x, y)) {
        ccp->x = x;
        ccp->y = y;
        return 0;
    }
    if (!(reply[0] == 'e' && (!reply[1] || reply[1] == ' ')))
        ev_protoerr("pos", reply);
    ccp->x = ccp->y = -10;
    return -1;
}

void
bot_number_pad(state)
int state;
{
    nhUse(state);
}

void
bot_delay_output()
{
    return;
}

#ifdef CHANGE_COLOR
void
bot_change_color(color, rgb, reverse)
int color;
long rgb;
int reverse;
{
    nhUse(color);
    nhUse(rgb);
    nhUse(reverse);
}

#ifdef MAC
void
bot_change_background(white_or_black)
int white_or_black;
{
    nhUse(white_or_black);
}

short
bot_set_font_name(window, font)
winid window;
char *font;
{
    return 0;
}
#endif

char *
bot_get_color_string()
{
    return (char *) "";
}
#endif

void
bot_start_screen()
{
    return;
}

void
bot_end_screen()
{
    return;
}

#endif /* BOT_GRAPHICS */
