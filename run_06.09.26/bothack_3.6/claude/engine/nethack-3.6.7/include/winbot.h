/* NetHack 3.6.7  winbot.h - structured bot window port + assist hooks */
#ifndef WINBOT_H
#define WINBOT_H

#ifdef BOT_GRAPHICS
extern struct window_procs bot_procs;
extern boolean botwin_active;
extern long botwin_parse_serial;

extern void FDECL(bot_init_nhwindows, (int *, char **));
extern void NDECL(bot_player_selection);
extern void NDECL(bot_askname);
extern void NDECL(bot_get_nh_event);
extern void FDECL(bot_exit_nhwindows, (const char *));
extern void FDECL(bot_suspend_nhwindows, (const char *));
extern void NDECL(bot_resume_nhwindows);
extern winid FDECL(bot_create_nhwindow, (int));
extern void FDECL(bot_clear_nhwindow, (winid));
extern void FDECL(bot_display_nhwindow, (winid, BOOLEAN_P));
extern void FDECL(bot_destroy_nhwindow, (winid));
extern void FDECL(bot_curs, (winid, int, int));
extern void FDECL(bot_putstr, (winid, int, const char *));
extern void FDECL(bot_display_file, (const char *, BOOLEAN_P));
extern void FDECL(bot_start_menu, (winid));
extern void FDECL(bot_add_menu, (winid, int, const ANY_P *, CHAR_P, CHAR_P, int,
                            const char *, BOOLEAN_P));
extern void FDECL(bot_end_menu, (winid, const char *));
extern int FDECL(bot_select_menu, (winid, int, MENU_ITEM_P **));
extern void NDECL(bot_update_inventory);
extern void NDECL(bot_mark_synch);
extern void NDECL(bot_wait_synch);
#ifdef CLIPPING
extern void FDECL(bot_cliparound, (int, int));
#endif
#ifdef POSITIONBAR
extern void FDECL(bot_update_positionbar, (char *));
#endif
extern void FDECL(bot_print_glyph, (winid, XCHAR_P, XCHAR_P, int, int));
extern void FDECL(bot_raw_print, (const char *));
extern void FDECL(bot_raw_print_bold, (const char *));
extern int NDECL(bot_nhgetch);
extern int FDECL(bot_nh_poskey, (int *, int *, int *));
extern void NDECL(bot_nhbell);
extern int NDECL(bot_doprev_message);
extern char FDECL(bot_yn_function, (const char *, const char *, CHAR_P));
extern void FDECL(bot_getlin, (const char *, char *));
extern int NDECL(bot_get_ext_cmd);
extern void FDECL(bot_number_pad, (int));
extern void NDECL(bot_delay_output);
#ifdef CHANGE_COLOR
extern void FDECL(bot_change_color, (int, long, int));
#ifdef MAC
extern void FDECL(bot_change_background, (int));
extern short FDECL(bot_set_font_name, (winid, char *));
#endif
extern char *NDECL(bot_get_color_string);
#endif
extern void NDECL(bot_start_screen);
extern void NDECL(bot_end_screen);

extern void FDECL(botwin_event_json, (const char *));
extern void FDECL(botwin_send_now, (const char *));
extern int FDECL(botwin_getpos, (coord *, BOOLEAN_P, const char *));
#endif /* BOT_GRAPHICS */

/* botassist.c - optional, logged test assistance (always compiled) */
extern void NDECL(assist_init);
extern boolean FDECL(assist_lifesave, (int));
extern boolean NDECL(assist_nostarve);
extern boolean FDECL(assist_nochoke, (struct obj *));
extern boolean NDECL(assist_brainsave);
extern boolean NDECL(assist_noslime);
extern void NDECL(assist_track);
extern void NDECL(assist_kit);
extern void FDECL(assist_gameover, (int));
extern unsigned long NDECL(assist_seed);
extern boolean NDECL(assist_seed_set);

#endif /* WINBOT_H */
