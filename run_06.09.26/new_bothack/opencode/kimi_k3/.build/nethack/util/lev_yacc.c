/* A Bison parser, made by GNU Bison 3.8.2.  */

/* Bison implementation for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015, 2018-2021 Free Software Foundation,
   Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

/* C LALR(1) parser skeleton written by Richard Stallman, by
   simplifying the original so-called "semantic" parser.  */

/* DO NOT RELY ON FEATURES THAT ARE NOT DOCUMENTED in the manual,
   especially those whose name start with YY_ or yy_.  They are
   private implementation details that can be changed or removed.  */

/* All symbols defined below should begin with yy or YY, to avoid
   infringing on user name space.  This should be done even for local
   variables, as they might otherwise be expanded by user macros.
   There are some unavoidable exceptions within include files to
   define necessary library symbols; they are noted "INFRINGES ON
   USER NAME SPACE" below.  */

/* Identify Bison output, and Bison version.  */
#define YYBISON 30802

/* Bison version string.  */
#define YYBISON_VERSION "3.8.2"

/* Skeleton name.  */
#define YYSKELETON_NAME "yacc.c"

/* Pure parsers.  */
#define YYPURE 0

/* Push parsers.  */
#define YYPUSH 0

/* Pull parsers.  */
#define YYPULL 1




/* First part of user prologue.  */
#line 1 "lev_comp.y"

/*	SCCS Id: @(#)lev_yacc.c	3.4	2000/01/17	*/
/*	Copyright (c) 1989 by Jean-Christophe Collet */
/* NetHack may be freely redistributed.  See license for details. */

/*
 * This file contains the Level Compiler code
 * It may handle special mazes & special room-levels
 */

/* In case we're using bison in AIX.  This definition must be
 * placed before any other C-language construct in the file
 * excluding comments and preprocessor directives (thanks IBM
 * for this wonderful feature...).
 *
 * Note: some cpps barf on this 'undefined control' (#pragma).
 * Addition of the leading space seems to prevent barfage for now,
 * and AIX will still see the directive.
 */
#ifdef _AIX
 #pragma alloca		/* keep leading space! */
#endif

#include "hack.h"
#include "sp_lev.h"

#define MAX_REGISTERS	10
#define ERR		(-1)
/* many types of things are put in chars for transference to NetHack.
 * since some systems will use signed chars, limit everybody to the
 * same number for portability.
 */
#define MAX_OF_TYPE	128

#define New(type)		\
	(type *) memset((genericptr_t)alloc(sizeof(type)), 0, sizeof(type))
#define NewTab(type, size)	(type **) alloc(sizeof(type *) * size)
#define Free(ptr)		free((genericptr_t)ptr)

extern void FDECL(yyerror, (const char *));
extern void FDECL(yywarning, (const char *));
extern int NDECL(yylex);
int NDECL(yyparse);

extern int FDECL(get_floor_type, (CHAR_P));
extern int FDECL(get_room_type, (char *));
extern int FDECL(get_trap_type, (char *));
extern int FDECL(get_monster_id, (char *,CHAR_P));
extern int FDECL(get_object_id, (char *,CHAR_P));
extern boolean FDECL(check_monster_char, (CHAR_P));
extern boolean FDECL(check_object_char, (CHAR_P));
extern char FDECL(what_map_char, (CHAR_P));
extern void FDECL(scan_map, (char *));
extern void NDECL(wallify_map);
extern boolean NDECL(check_subrooms);
extern void FDECL(check_coord, (int,int,const char *));
extern void NDECL(store_part);
extern void NDECL(store_room);
extern boolean FDECL(write_level_file, (char *,splev *,specialmaze *));
extern void FDECL(free_rooms, (splev *));

static struct reg {
	int x1, y1;
	int x2, y2;
}		current_region;

static struct coord {
	int x;
	int y;
}		current_coord, current_align;

static struct size {
	int height;
	int width;
}		current_size;

char tmpmessage[256];
digpos *tmppass[32];
char *tmpmap[ROWNO];

digpos *tmpdig[MAX_OF_TYPE];
region *tmpreg[MAX_OF_TYPE];
lev_region *tmplreg[MAX_OF_TYPE];
door *tmpdoor[MAX_OF_TYPE];
drawbridge *tmpdb[MAX_OF_TYPE];
walk *tmpwalk[MAX_OF_TYPE];

room_door *tmprdoor[MAX_OF_TYPE];
trap *tmptrap[MAX_OF_TYPE];
monster *tmpmonst[MAX_OF_TYPE];
object *tmpobj[MAX_OF_TYPE];
altar *tmpaltar[MAX_OF_TYPE];
lad *tmplad[MAX_OF_TYPE];
stair *tmpstair[MAX_OF_TYPE];
gold *tmpgold[MAX_OF_TYPE];
engraving *tmpengraving[MAX_OF_TYPE];
fountain *tmpfountain[MAX_OF_TYPE];
sink *tmpsink[MAX_OF_TYPE];
pool *tmppool[MAX_OF_TYPE];

mazepart *tmppart[10];
room *tmproom[MAXNROFROOMS*2];
corridor *tmpcor[MAX_OF_TYPE];

static specialmaze maze;
static splev special_lev;
static lev_init init_lev;

static char olist[MAX_REGISTERS], mlist[MAX_REGISTERS];
static struct coord plist[MAX_REGISTERS];

int n_olist = 0, n_mlist = 0, n_plist = 0;

unsigned int nlreg = 0, nreg = 0, ndoor = 0, ntrap = 0, nmons = 0, nobj = 0;
unsigned int ndb = 0, nwalk = 0, npart = 0, ndig = 0, nlad = 0, nstair = 0;
unsigned int naltar = 0, ncorridor = 0, nrooms = 0, ngold = 0, nengraving = 0;
unsigned int nfountain = 0, npool = 0, nsink = 0, npass = 0;

static int lev_flags = 0;

unsigned int max_x_map, max_y_map;

static xchar in_room;

extern int fatal_error;
extern int want_warnings;
extern const char *fname;


#line 201 "y.tab.c"

# ifndef YY_CAST
#  ifdef __cplusplus
#   define YY_CAST(Type, Val) static_cast<Type> (Val)
#   define YY_REINTERPRET_CAST(Type, Val) reinterpret_cast<Type> (Val)
#  else
#   define YY_CAST(Type, Val) ((Type) (Val))
#   define YY_REINTERPRET_CAST(Type, Val) ((Type) (Val))
#  endif
# endif
# ifndef YY_NULLPTR
#  if defined __cplusplus
#   if 201103L <= __cplusplus
#    define YY_NULLPTR nullptr
#   else
#    define YY_NULLPTR 0
#   endif
#  else
#   define YY_NULLPTR ((void*)0)
#  endif
# endif

/* Use api.header.include to #include this header
   instead of duplicating it here.  */
#ifndef YY_YY_Y_TAB_H_INCLUDED
# define YY_YY_Y_TAB_H_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif
#if YYDEBUG
extern int yydebug;
#endif

/* Token kinds.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    YYEMPTY = -2,
    YYEOF = 0,                     /* "end of file"  */
    YYerror = 256,                 /* error  */
    YYUNDEF = 257,                 /* "invalid token"  */
    CHAR = 258,                    /* CHAR  */
    INTEGER = 259,                 /* INTEGER  */
    BOOLEAN = 260,                 /* BOOLEAN  */
    PERCENT = 261,                 /* PERCENT  */
    MESSAGE_ID = 262,              /* MESSAGE_ID  */
    MAZE_ID = 263,                 /* MAZE_ID  */
    LEVEL_ID = 264,                /* LEVEL_ID  */
    LEV_INIT_ID = 265,             /* LEV_INIT_ID  */
    GEOMETRY_ID = 266,             /* GEOMETRY_ID  */
    NOMAP_ID = 267,                /* NOMAP_ID  */
    OBJECT_ID = 268,               /* OBJECT_ID  */
    COBJECT_ID = 269,              /* COBJECT_ID  */
    MONSTER_ID = 270,              /* MONSTER_ID  */
    TRAP_ID = 271,                 /* TRAP_ID  */
    DOOR_ID = 272,                 /* DOOR_ID  */
    DRAWBRIDGE_ID = 273,           /* DRAWBRIDGE_ID  */
    MAZEWALK_ID = 274,             /* MAZEWALK_ID  */
    WALLIFY_ID = 275,              /* WALLIFY_ID  */
    REGION_ID = 276,               /* REGION_ID  */
    FILLING = 277,                 /* FILLING  */
    RANDOM_OBJECTS_ID = 278,       /* RANDOM_OBJECTS_ID  */
    RANDOM_MONSTERS_ID = 279,      /* RANDOM_MONSTERS_ID  */
    RANDOM_PLACES_ID = 280,        /* RANDOM_PLACES_ID  */
    ALTAR_ID = 281,                /* ALTAR_ID  */
    LADDER_ID = 282,               /* LADDER_ID  */
    STAIR_ID = 283,                /* STAIR_ID  */
    NON_DIGGABLE_ID = 284,         /* NON_DIGGABLE_ID  */
    NON_PASSWALL_ID = 285,         /* NON_PASSWALL_ID  */
    ROOM_ID = 286,                 /* ROOM_ID  */
    PORTAL_ID = 287,               /* PORTAL_ID  */
    TELEPRT_ID = 288,              /* TELEPRT_ID  */
    BRANCH_ID = 289,               /* BRANCH_ID  */
    LEV = 290,                     /* LEV  */
    CHANCE_ID = 291,               /* CHANCE_ID  */
    CORRIDOR_ID = 292,             /* CORRIDOR_ID  */
    GOLD_ID = 293,                 /* GOLD_ID  */
    ENGRAVING_ID = 294,            /* ENGRAVING_ID  */
    FOUNTAIN_ID = 295,             /* FOUNTAIN_ID  */
    POOL_ID = 296,                 /* POOL_ID  */
    SINK_ID = 297,                 /* SINK_ID  */
    NONE = 298,                    /* NONE  */
    RAND_CORRIDOR_ID = 299,        /* RAND_CORRIDOR_ID  */
    DOOR_STATE = 300,              /* DOOR_STATE  */
    LIGHT_STATE = 301,             /* LIGHT_STATE  */
    CURSE_TYPE = 302,              /* CURSE_TYPE  */
    ENGRAVING_TYPE = 303,          /* ENGRAVING_TYPE  */
    DIRECTION = 304,               /* DIRECTION  */
    RANDOM_TYPE = 305,             /* RANDOM_TYPE  */
    O_REGISTER = 306,              /* O_REGISTER  */
    M_REGISTER = 307,              /* M_REGISTER  */
    P_REGISTER = 308,              /* P_REGISTER  */
    A_REGISTER = 309,              /* A_REGISTER  */
    ALIGNMENT = 310,               /* ALIGNMENT  */
    LEFT_OR_RIGHT = 311,           /* LEFT_OR_RIGHT  */
    CENTER = 312,                  /* CENTER  */
    TOP_OR_BOT = 313,              /* TOP_OR_BOT  */
    ALTAR_TYPE = 314,              /* ALTAR_TYPE  */
    UP_OR_DOWN = 315,              /* UP_OR_DOWN  */
    SUBROOM_ID = 316,              /* SUBROOM_ID  */
    NAME_ID = 317,                 /* NAME_ID  */
    FLAGS_ID = 318,                /* FLAGS_ID  */
    FLAG_TYPE = 319,               /* FLAG_TYPE  */
    MON_ATTITUDE = 320,            /* MON_ATTITUDE  */
    MON_ALERTNESS = 321,           /* MON_ALERTNESS  */
    MON_APPEARANCE = 322,          /* MON_APPEARANCE  */
    CONTAINED = 323,               /* CONTAINED  */
    STRING = 324,                  /* STRING  */
    MAP_ID = 325                   /* MAP_ID  */
  };
  typedef enum yytokentype yytoken_kind_t;
#endif
/* Token kinds.  */
#define YYEMPTY -2
#define YYEOF 0
#define YYerror 256
#define YYUNDEF 257
#define CHAR 258
#define INTEGER 259
#define BOOLEAN 260
#define PERCENT 261
#define MESSAGE_ID 262
#define MAZE_ID 263
#define LEVEL_ID 264
#define LEV_INIT_ID 265
#define GEOMETRY_ID 266
#define NOMAP_ID 267
#define OBJECT_ID 268
#define COBJECT_ID 269
#define MONSTER_ID 270
#define TRAP_ID 271
#define DOOR_ID 272
#define DRAWBRIDGE_ID 273
#define MAZEWALK_ID 274
#define WALLIFY_ID 275
#define REGION_ID 276
#define FILLING 277
#define RANDOM_OBJECTS_ID 278
#define RANDOM_MONSTERS_ID 279
#define RANDOM_PLACES_ID 280
#define ALTAR_ID 281
#define LADDER_ID 282
#define STAIR_ID 283
#define NON_DIGGABLE_ID 284
#define NON_PASSWALL_ID 285
#define ROOM_ID 286
#define PORTAL_ID 287
#define TELEPRT_ID 288
#define BRANCH_ID 289
#define LEV 290
#define CHANCE_ID 291
#define CORRIDOR_ID 292
#define GOLD_ID 293
#define ENGRAVING_ID 294
#define FOUNTAIN_ID 295
#define POOL_ID 296
#define SINK_ID 297
#define NONE 298
#define RAND_CORRIDOR_ID 299
#define DOOR_STATE 300
#define LIGHT_STATE 301
#define CURSE_TYPE 302
#define ENGRAVING_TYPE 303
#define DIRECTION 304
#define RANDOM_TYPE 305
#define O_REGISTER 306
#define M_REGISTER 307
#define P_REGISTER 308
#define A_REGISTER 309
#define ALIGNMENT 310
#define LEFT_OR_RIGHT 311
#define CENTER 312
#define TOP_OR_BOT 313
#define ALTAR_TYPE 314
#define UP_OR_DOWN 315
#define SUBROOM_ID 316
#define NAME_ID 317
#define FLAGS_ID 318
#define FLAG_TYPE 319
#define MON_ATTITUDE 320
#define MON_ALERTNESS 321
#define MON_APPEARANCE 322
#define CONTAINED 323
#define STRING 324
#define MAP_ID 325

/* Value type.  */
#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
union YYSTYPE
{
#line 132 "lev_comp.y"

	int	i;
	char*	map;
	struct {
		xchar room;
		xchar wall;
		xchar door;
	} corpos;

#line 404 "y.tab.c"

};
typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif


extern YYSTYPE yylval;


int yyparse (void);


#endif /* !YY_YY_Y_TAB_H_INCLUDED  */
/* Symbol kind.  */
enum yysymbol_kind_t
{
  YYSYMBOL_YYEMPTY = -2,
  YYSYMBOL_YYEOF = 0,                      /* "end of file"  */
  YYSYMBOL_YYerror = 1,                    /* error  */
  YYSYMBOL_YYUNDEF = 2,                    /* "invalid token"  */
  YYSYMBOL_CHAR = 3,                       /* CHAR  */
  YYSYMBOL_INTEGER = 4,                    /* INTEGER  */
  YYSYMBOL_BOOLEAN = 5,                    /* BOOLEAN  */
  YYSYMBOL_PERCENT = 6,                    /* PERCENT  */
  YYSYMBOL_MESSAGE_ID = 7,                 /* MESSAGE_ID  */
  YYSYMBOL_MAZE_ID = 8,                    /* MAZE_ID  */
  YYSYMBOL_LEVEL_ID = 9,                   /* LEVEL_ID  */
  YYSYMBOL_LEV_INIT_ID = 10,               /* LEV_INIT_ID  */
  YYSYMBOL_GEOMETRY_ID = 11,               /* GEOMETRY_ID  */
  YYSYMBOL_NOMAP_ID = 12,                  /* NOMAP_ID  */
  YYSYMBOL_OBJECT_ID = 13,                 /* OBJECT_ID  */
  YYSYMBOL_COBJECT_ID = 14,                /* COBJECT_ID  */
  YYSYMBOL_MONSTER_ID = 15,                /* MONSTER_ID  */
  YYSYMBOL_TRAP_ID = 16,                   /* TRAP_ID  */
  YYSYMBOL_DOOR_ID = 17,                   /* DOOR_ID  */
  YYSYMBOL_DRAWBRIDGE_ID = 18,             /* DRAWBRIDGE_ID  */
  YYSYMBOL_MAZEWALK_ID = 19,               /* MAZEWALK_ID  */
  YYSYMBOL_WALLIFY_ID = 20,                /* WALLIFY_ID  */
  YYSYMBOL_REGION_ID = 21,                 /* REGION_ID  */
  YYSYMBOL_FILLING = 22,                   /* FILLING  */
  YYSYMBOL_RANDOM_OBJECTS_ID = 23,         /* RANDOM_OBJECTS_ID  */
  YYSYMBOL_RANDOM_MONSTERS_ID = 24,        /* RANDOM_MONSTERS_ID  */
  YYSYMBOL_RANDOM_PLACES_ID = 25,          /* RANDOM_PLACES_ID  */
  YYSYMBOL_ALTAR_ID = 26,                  /* ALTAR_ID  */
  YYSYMBOL_LADDER_ID = 27,                 /* LADDER_ID  */
  YYSYMBOL_STAIR_ID = 28,                  /* STAIR_ID  */
  YYSYMBOL_NON_DIGGABLE_ID = 29,           /* NON_DIGGABLE_ID  */
  YYSYMBOL_NON_PASSWALL_ID = 30,           /* NON_PASSWALL_ID  */
  YYSYMBOL_ROOM_ID = 31,                   /* ROOM_ID  */
  YYSYMBOL_PORTAL_ID = 32,                 /* PORTAL_ID  */
  YYSYMBOL_TELEPRT_ID = 33,                /* TELEPRT_ID  */
  YYSYMBOL_BRANCH_ID = 34,                 /* BRANCH_ID  */
  YYSYMBOL_LEV = 35,                       /* LEV  */
  YYSYMBOL_CHANCE_ID = 36,                 /* CHANCE_ID  */
  YYSYMBOL_CORRIDOR_ID = 37,               /* CORRIDOR_ID  */
  YYSYMBOL_GOLD_ID = 38,                   /* GOLD_ID  */
  YYSYMBOL_ENGRAVING_ID = 39,              /* ENGRAVING_ID  */
  YYSYMBOL_FOUNTAIN_ID = 40,               /* FOUNTAIN_ID  */
  YYSYMBOL_POOL_ID = 41,                   /* POOL_ID  */
  YYSYMBOL_SINK_ID = 42,                   /* SINK_ID  */
  YYSYMBOL_NONE = 43,                      /* NONE  */
  YYSYMBOL_RAND_CORRIDOR_ID = 44,          /* RAND_CORRIDOR_ID  */
  YYSYMBOL_DOOR_STATE = 45,                /* DOOR_STATE  */
  YYSYMBOL_LIGHT_STATE = 46,               /* LIGHT_STATE  */
  YYSYMBOL_CURSE_TYPE = 47,                /* CURSE_TYPE  */
  YYSYMBOL_ENGRAVING_TYPE = 48,            /* ENGRAVING_TYPE  */
  YYSYMBOL_DIRECTION = 49,                 /* DIRECTION  */
  YYSYMBOL_RANDOM_TYPE = 50,               /* RANDOM_TYPE  */
  YYSYMBOL_O_REGISTER = 51,                /* O_REGISTER  */
  YYSYMBOL_M_REGISTER = 52,                /* M_REGISTER  */
  YYSYMBOL_P_REGISTER = 53,                /* P_REGISTER  */
  YYSYMBOL_A_REGISTER = 54,                /* A_REGISTER  */
  YYSYMBOL_ALIGNMENT = 55,                 /* ALIGNMENT  */
  YYSYMBOL_LEFT_OR_RIGHT = 56,             /* LEFT_OR_RIGHT  */
  YYSYMBOL_CENTER = 57,                    /* CENTER  */
  YYSYMBOL_TOP_OR_BOT = 58,                /* TOP_OR_BOT  */
  YYSYMBOL_ALTAR_TYPE = 59,                /* ALTAR_TYPE  */
  YYSYMBOL_UP_OR_DOWN = 60,                /* UP_OR_DOWN  */
  YYSYMBOL_SUBROOM_ID = 61,                /* SUBROOM_ID  */
  YYSYMBOL_NAME_ID = 62,                   /* NAME_ID  */
  YYSYMBOL_FLAGS_ID = 63,                  /* FLAGS_ID  */
  YYSYMBOL_FLAG_TYPE = 64,                 /* FLAG_TYPE  */
  YYSYMBOL_MON_ATTITUDE = 65,              /* MON_ATTITUDE  */
  YYSYMBOL_MON_ALERTNESS = 66,             /* MON_ALERTNESS  */
  YYSYMBOL_MON_APPEARANCE = 67,            /* MON_APPEARANCE  */
  YYSYMBOL_CONTAINED = 68,                 /* CONTAINED  */
  YYSYMBOL_69_ = 69,                       /* ','  */
  YYSYMBOL_70_ = 70,                       /* ':'  */
  YYSYMBOL_71_ = 71,                       /* '('  */
  YYSYMBOL_72_ = 72,                       /* ')'  */
  YYSYMBOL_73_ = 73,                       /* '['  */
  YYSYMBOL_74_ = 74,                       /* ']'  */
  YYSYMBOL_STRING = 75,                    /* STRING  */
  YYSYMBOL_MAP_ID = 76,                    /* MAP_ID  */
  YYSYMBOL_YYACCEPT = 77,                  /* $accept  */
  YYSYMBOL_file = 78,                      /* file  */
  YYSYMBOL_levels = 79,                    /* levels  */
  YYSYMBOL_level = 80,                     /* level  */
  YYSYMBOL_maze_level = 81,                /* maze_level  */
  YYSYMBOL_room_level = 82,                /* room_level  */
  YYSYMBOL_level_def = 83,                 /* level_def  */
  YYSYMBOL_lev_init = 84,                  /* lev_init  */
  YYSYMBOL_walled = 85,                    /* walled  */
  YYSYMBOL_flags = 86,                     /* flags  */
  YYSYMBOL_flag_list = 87,                 /* flag_list  */
  YYSYMBOL_messages = 88,                  /* messages  */
  YYSYMBOL_message = 89,                   /* message  */
  YYSYMBOL_rreg_init = 90,                 /* rreg_init  */
  YYSYMBOL_init_rreg = 91,                 /* init_rreg  */
  YYSYMBOL_rooms = 92,                     /* rooms  */
  YYSYMBOL_roomlist = 93,                  /* roomlist  */
  YYSYMBOL_corridors_def = 94,             /* corridors_def  */
  YYSYMBOL_random_corridors = 95,          /* random_corridors  */
  YYSYMBOL_corridors = 96,                 /* corridors  */
  YYSYMBOL_corridor = 97,                  /* corridor  */
  YYSYMBOL_corr_spec = 98,                 /* corr_spec  */
  YYSYMBOL_aroom = 99,                     /* aroom  */
  YYSYMBOL_subroom_def = 100,              /* subroom_def  */
  YYSYMBOL_room_def = 101,                 /* room_def  */
  YYSYMBOL_roomfill = 102,                 /* roomfill  */
  YYSYMBOL_room_pos = 103,                 /* room_pos  */
  YYSYMBOL_subroom_pos = 104,              /* subroom_pos  */
  YYSYMBOL_room_align = 105,               /* room_align  */
  YYSYMBOL_room_size = 106,                /* room_size  */
  YYSYMBOL_room_details = 107,             /* room_details  */
  YYSYMBOL_room_detail = 108,              /* room_detail  */
  YYSYMBOL_room_name = 109,                /* room_name  */
  YYSYMBOL_room_chance = 110,              /* room_chance  */
  YYSYMBOL_room_door = 111,                /* room_door  */
  YYSYMBOL_secret = 112,                   /* secret  */
  YYSYMBOL_door_wall = 113,                /* door_wall  */
  YYSYMBOL_door_pos = 114,                 /* door_pos  */
  YYSYMBOL_maze_def = 115,                 /* maze_def  */
  YYSYMBOL_filling = 116,                  /* filling  */
  YYSYMBOL_regions = 117,                  /* regions  */
  YYSYMBOL_aregion = 118,                  /* aregion  */
  YYSYMBOL_map_definition = 119,           /* map_definition  */
  YYSYMBOL_map_geometry = 120,             /* map_geometry  */
  YYSYMBOL_h_justif = 121,                 /* h_justif  */
  YYSYMBOL_v_justif = 122,                 /* v_justif  */
  YYSYMBOL_reg_init = 123,                 /* reg_init  */
  YYSYMBOL_init_reg = 124,                 /* init_reg  */
  YYSYMBOL_object_list = 125,              /* object_list  */
  YYSYMBOL_monster_list = 126,             /* monster_list  */
  YYSYMBOL_place_list = 127,               /* place_list  */
  YYSYMBOL_128_1 = 128,                    /* $@1  */
  YYSYMBOL_map_details = 129,              /* map_details  */
  YYSYMBOL_map_detail = 130,               /* map_detail  */
  YYSYMBOL_monster_detail = 131,           /* monster_detail  */
  YYSYMBOL_132_2 = 132,                    /* $@2  */
  YYSYMBOL_monster_infos = 133,            /* monster_infos  */
  YYSYMBOL_monster_info = 134,             /* monster_info  */
  YYSYMBOL_object_detail = 135,            /* object_detail  */
  YYSYMBOL_object_desc = 136,              /* object_desc  */
  YYSYMBOL_137_3 = 137,                    /* $@3  */
  YYSYMBOL_object_where = 138,             /* object_where  */
  YYSYMBOL_object_infos = 139,             /* object_infos  */
  YYSYMBOL_curse_state = 140,              /* curse_state  */
  YYSYMBOL_monster_id = 141,               /* monster_id  */
  YYSYMBOL_enchantment = 142,              /* enchantment  */
  YYSYMBOL_optional_name = 143,            /* optional_name  */
  YYSYMBOL_door_detail = 144,              /* door_detail  */
  YYSYMBOL_trap_detail = 145,              /* trap_detail  */
  YYSYMBOL_drawbridge_detail = 146,        /* drawbridge_detail  */
  YYSYMBOL_mazewalk_detail = 147,          /* mazewalk_detail  */
  YYSYMBOL_wallify_detail = 148,           /* wallify_detail  */
  YYSYMBOL_ladder_detail = 149,            /* ladder_detail  */
  YYSYMBOL_stair_detail = 150,             /* stair_detail  */
  YYSYMBOL_stair_region = 151,             /* stair_region  */
  YYSYMBOL_152_4 = 152,                    /* $@4  */
  YYSYMBOL_portal_region = 153,            /* portal_region  */
  YYSYMBOL_154_5 = 154,                    /* $@5  */
  YYSYMBOL_teleprt_region = 155,           /* teleprt_region  */
  YYSYMBOL_156_6 = 156,                    /* $@6  */
  YYSYMBOL_157_7 = 157,                    /* $@7  */
  YYSYMBOL_branch_region = 158,            /* branch_region  */
  YYSYMBOL_159_8 = 159,                    /* $@8  */
  YYSYMBOL_teleprt_detail = 160,           /* teleprt_detail  */
  YYSYMBOL_lev_region = 161,               /* lev_region  */
  YYSYMBOL_fountain_detail = 162,          /* fountain_detail  */
  YYSYMBOL_sink_detail = 163,              /* sink_detail  */
  YYSYMBOL_pool_detail = 164,              /* pool_detail  */
  YYSYMBOL_diggable_detail = 165,          /* diggable_detail  */
  YYSYMBOL_passwall_detail = 166,          /* passwall_detail  */
  YYSYMBOL_region_detail = 167,            /* region_detail  */
  YYSYMBOL_altar_detail = 168,             /* altar_detail  */
  YYSYMBOL_gold_detail = 169,              /* gold_detail  */
  YYSYMBOL_engraving_detail = 170,         /* engraving_detail  */
  YYSYMBOL_monster_c = 171,                /* monster_c  */
  YYSYMBOL_object_c = 172,                 /* object_c  */
  YYSYMBOL_m_name = 173,                   /* m_name  */
  YYSYMBOL_o_name = 174,                   /* o_name  */
  YYSYMBOL_trap_name = 175,                /* trap_name  */
  YYSYMBOL_room_type = 176,                /* room_type  */
  YYSYMBOL_prefilled = 177,                /* prefilled  */
  YYSYMBOL_coordinate = 178,               /* coordinate  */
  YYSYMBOL_door_state = 179,               /* door_state  */
  YYSYMBOL_light_state = 180,              /* light_state  */
  YYSYMBOL_alignment = 181,                /* alignment  */
  YYSYMBOL_altar_type = 182,               /* altar_type  */
  YYSYMBOL_p_register = 183,               /* p_register  */
  YYSYMBOL_o_register = 184,               /* o_register  */
  YYSYMBOL_m_register = 185,               /* m_register  */
  YYSYMBOL_a_register = 186,               /* a_register  */
  YYSYMBOL_place = 187,                    /* place  */
  YYSYMBOL_monster = 188,                  /* monster  */
  YYSYMBOL_object = 189,                   /* object  */
  YYSYMBOL_string = 190,                   /* string  */
  YYSYMBOL_amount = 191,                   /* amount  */
  YYSYMBOL_chance = 192,                   /* chance  */
  YYSYMBOL_engraving_type = 193,           /* engraving_type  */
  YYSYMBOL_coord = 194,                    /* coord  */
  YYSYMBOL_region = 195                    /* region  */
};
typedef enum yysymbol_kind_t yysymbol_kind_t;




#ifdef short
# undef short
#endif

/* On compilers that do not define __PTRDIFF_MAX__ etc., make sure
   <limits.h> and (if available) <stdint.h> are included
   so that the code can choose integer types of a good width.  */

#ifndef __PTRDIFF_MAX__
# include <limits.h> /* INFRINGES ON USER NAME SPACE */
# if defined __STDC_VERSION__ && 199901 <= __STDC_VERSION__
#  include <stdint.h> /* INFRINGES ON USER NAME SPACE */
#  define YY_STDINT_H
# endif
#endif

/* Narrow types that promote to a signed type and that can represent a
   signed or unsigned integer of at least N bits.  In tables they can
   save space and decrease cache pressure.  Promoting to a signed type
   helps avoid bugs in integer arithmetic.  */

#ifdef __INT_LEAST8_MAX__
typedef __INT_LEAST8_TYPE__ yytype_int8;
#elif defined YY_STDINT_H
typedef int_least8_t yytype_int8;
#else
typedef signed char yytype_int8;
#endif

#ifdef __INT_LEAST16_MAX__
typedef __INT_LEAST16_TYPE__ yytype_int16;
#elif defined YY_STDINT_H
typedef int_least16_t yytype_int16;
#else
typedef short yytype_int16;
#endif

/* Work around bug in HP-UX 11.23, which defines these macros
   incorrectly for preprocessor constants.  This workaround can likely
   be removed in 2023, as HPE has promised support for HP-UX 11.23
   (aka HP-UX 11i v2) only through the end of 2022; see Table 2 of
   <https://h20195.www2.hpe.com/V2/getpdf.aspx/4AA4-7673ENW.pdf>.  */
#ifdef __hpux
# undef UINT_LEAST8_MAX
# undef UINT_LEAST16_MAX
# define UINT_LEAST8_MAX 255
# define UINT_LEAST16_MAX 65535
#endif

#if defined __UINT_LEAST8_MAX__ && __UINT_LEAST8_MAX__ <= __INT_MAX__
typedef __UINT_LEAST8_TYPE__ yytype_uint8;
#elif (!defined __UINT_LEAST8_MAX__ && defined YY_STDINT_H \
       && UINT_LEAST8_MAX <= INT_MAX)
typedef uint_least8_t yytype_uint8;
#elif !defined __UINT_LEAST8_MAX__ && UCHAR_MAX <= INT_MAX
typedef unsigned char yytype_uint8;
#else
typedef short yytype_uint8;
#endif

#if defined __UINT_LEAST16_MAX__ && __UINT_LEAST16_MAX__ <= __INT_MAX__
typedef __UINT_LEAST16_TYPE__ yytype_uint16;
#elif (!defined __UINT_LEAST16_MAX__ && defined YY_STDINT_H \
       && UINT_LEAST16_MAX <= INT_MAX)
typedef uint_least16_t yytype_uint16;
#elif !defined __UINT_LEAST16_MAX__ && USHRT_MAX <= INT_MAX
typedef unsigned short yytype_uint16;
#else
typedef int yytype_uint16;
#endif

#ifndef YYPTRDIFF_T
# if defined __PTRDIFF_TYPE__ && defined __PTRDIFF_MAX__
#  define YYPTRDIFF_T __PTRDIFF_TYPE__
#  define YYPTRDIFF_MAXIMUM __PTRDIFF_MAX__
# elif defined PTRDIFF_MAX
#  ifndef ptrdiff_t
#   include <stddef.h> /* INFRINGES ON USER NAME SPACE */
#  endif
#  define YYPTRDIFF_T ptrdiff_t
#  define YYPTRDIFF_MAXIMUM PTRDIFF_MAX
# else
#  define YYPTRDIFF_T long
#  define YYPTRDIFF_MAXIMUM LONG_MAX
# endif
#endif

#ifndef YYSIZE_T
# ifdef __SIZE_TYPE__
#  define YYSIZE_T __SIZE_TYPE__
# elif defined size_t
#  define YYSIZE_T size_t
# elif defined __STDC_VERSION__ && 199901 <= __STDC_VERSION__
#  include <stddef.h> /* INFRINGES ON USER NAME SPACE */
#  define YYSIZE_T size_t
# else
#  define YYSIZE_T unsigned
# endif
#endif

#define YYSIZE_MAXIMUM                                  \
  YY_CAST (YYPTRDIFF_T,                                 \
           (YYPTRDIFF_MAXIMUM < YY_CAST (YYSIZE_T, -1)  \
            ? YYPTRDIFF_MAXIMUM                         \
            : YY_CAST (YYSIZE_T, -1)))

#define YYSIZEOF(X) YY_CAST (YYPTRDIFF_T, sizeof (X))


/* Stored state numbers (used for stacks). */
typedef yytype_int16 yy_state_t;

/* State numbers in computations.  */
typedef int yy_state_fast_t;

#ifndef YY_
# if defined YYENABLE_NLS && YYENABLE_NLS
#  if ENABLE_NLS
#   include <libintl.h> /* INFRINGES ON USER NAME SPACE */
#   define YY_(Msgid) dgettext ("bison-runtime", Msgid)
#  endif
# endif
# ifndef YY_
#  define YY_(Msgid) Msgid
# endif
#endif


#ifndef YY_ATTRIBUTE_PURE
# if defined __GNUC__ && 2 < __GNUC__ + (96 <= __GNUC_MINOR__)
#  define YY_ATTRIBUTE_PURE __attribute__ ((__pure__))
# else
#  define YY_ATTRIBUTE_PURE
# endif
#endif

#ifndef YY_ATTRIBUTE_UNUSED
# if defined __GNUC__ && 2 < __GNUC__ + (7 <= __GNUC_MINOR__)
#  define YY_ATTRIBUTE_UNUSED __attribute__ ((__unused__))
# else
#  define YY_ATTRIBUTE_UNUSED
# endif
#endif

/* Suppress unused-variable warnings by "using" E.  */
#if ! defined lint || defined __GNUC__
# define YY_USE(E) ((void) (E))
#else
# define YY_USE(E) /* empty */
#endif

/* Suppress an incorrect diagnostic about yylval being uninitialized.  */
#if defined __GNUC__ && ! defined __ICC && 406 <= __GNUC__ * 100 + __GNUC_MINOR__
# if __GNUC__ * 100 + __GNUC_MINOR__ < 407
#  define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN                           \
    _Pragma ("GCC diagnostic push")                                     \
    _Pragma ("GCC diagnostic ignored \"-Wuninitialized\"")
# else
#  define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN                           \
    _Pragma ("GCC diagnostic push")                                     \
    _Pragma ("GCC diagnostic ignored \"-Wuninitialized\"")              \
    _Pragma ("GCC diagnostic ignored \"-Wmaybe-uninitialized\"")
# endif
# define YY_IGNORE_MAYBE_UNINITIALIZED_END      \
    _Pragma ("GCC diagnostic pop")
#else
# define YY_INITIAL_VALUE(Value) Value
#endif
#ifndef YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
# define YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
# define YY_IGNORE_MAYBE_UNINITIALIZED_END
#endif
#ifndef YY_INITIAL_VALUE
# define YY_INITIAL_VALUE(Value) /* Nothing. */
#endif

#if defined __cplusplus && defined __GNUC__ && ! defined __ICC && 6 <= __GNUC__
# define YY_IGNORE_USELESS_CAST_BEGIN                          \
    _Pragma ("GCC diagnostic push")                            \
    _Pragma ("GCC diagnostic ignored \"-Wuseless-cast\"")
# define YY_IGNORE_USELESS_CAST_END            \
    _Pragma ("GCC diagnostic pop")
#endif
#ifndef YY_IGNORE_USELESS_CAST_BEGIN
# define YY_IGNORE_USELESS_CAST_BEGIN
# define YY_IGNORE_USELESS_CAST_END
#endif


#define YY_ASSERT(E) ((void) (0 && (E)))

#if !defined yyoverflow

/* The parser invokes alloca or malloc; define the necessary symbols.  */

# ifdef YYSTACK_USE_ALLOCA
#  if YYSTACK_USE_ALLOCA
#   ifdef __GNUC__
#    define YYSTACK_ALLOC __builtin_alloca
#   elif defined __BUILTIN_VA_ARG_INCR
#    include <alloca.h> /* INFRINGES ON USER NAME SPACE */
#   elif defined _AIX
#    define YYSTACK_ALLOC __alloca
#   elif defined _MSC_VER
#    include <malloc.h> /* INFRINGES ON USER NAME SPACE */
#    define alloca _alloca
#   else
#    define YYSTACK_ALLOC alloca
#    if ! defined _ALLOCA_H && ! defined EXIT_SUCCESS
#     include <stdlib.h> /* INFRINGES ON USER NAME SPACE */
      /* Use EXIT_SUCCESS as a witness for stdlib.h.  */
#     ifndef EXIT_SUCCESS
#      define EXIT_SUCCESS 0
#     endif
#    endif
#   endif
#  endif
# endif

# ifdef YYSTACK_ALLOC
   /* Pacify GCC's 'empty if-body' warning.  */
#  define YYSTACK_FREE(Ptr) do { /* empty */; } while (0)
#  ifndef YYSTACK_ALLOC_MAXIMUM
    /* The OS might guarantee only one guard page at the bottom of the stack,
       and a page size can be as small as 4096 bytes.  So we cannot safely
       invoke alloca (N) if N exceeds 4096.  Use a slightly smaller number
       to allow for a few compiler-allocated temporary stack slots.  */
#   define YYSTACK_ALLOC_MAXIMUM 4032 /* reasonable circa 2006 */
#  endif
# else
#  define YYSTACK_ALLOC YYMALLOC
#  define YYSTACK_FREE YYFREE
#  ifndef YYSTACK_ALLOC_MAXIMUM
#   define YYSTACK_ALLOC_MAXIMUM YYSIZE_MAXIMUM
#  endif
#  if (defined __cplusplus && ! defined EXIT_SUCCESS \
       && ! ((defined YYMALLOC || defined malloc) \
             && (defined YYFREE || defined free)))
#   include <stdlib.h> /* INFRINGES ON USER NAME SPACE */
#   ifndef EXIT_SUCCESS
#    define EXIT_SUCCESS 0
#   endif
#  endif
#  ifndef YYMALLOC
#   define YYMALLOC malloc
#   if ! defined malloc && ! defined EXIT_SUCCESS
void *malloc (YYSIZE_T); /* INFRINGES ON USER NAME SPACE */
#   endif
#  endif
#  ifndef YYFREE
#   define YYFREE free
#   if ! defined free && ! defined EXIT_SUCCESS
void free (void *); /* INFRINGES ON USER NAME SPACE */
#   endif
#  endif
# endif
#endif /* !defined yyoverflow */

#if (! defined yyoverflow \
     && (! defined __cplusplus \
         || (defined YYSTYPE_IS_TRIVIAL && YYSTYPE_IS_TRIVIAL)))

/* A type that is properly aligned for any stack member.  */
union yyalloc
{
  yy_state_t yyss_alloc;
  YYSTYPE yyvs_alloc;
};

/* The size of the maximum gap between one aligned stack and the next.  */
# define YYSTACK_GAP_MAXIMUM (YYSIZEOF (union yyalloc) - 1)

/* The size of an array large to enough to hold all stacks, each with
   N elements.  */
# define YYSTACK_BYTES(N) \
     ((N) * (YYSIZEOF (yy_state_t) + YYSIZEOF (YYSTYPE)) \
      + YYSTACK_GAP_MAXIMUM)

# define YYCOPY_NEEDED 1

/* Relocate STACK from its old location to the new one.  The
   local variables YYSIZE and YYSTACKSIZE give the old and new number of
   elements in the stack, and YYPTR gives the new location of the
   stack.  Advance YYPTR to a properly aligned location for the next
   stack.  */
# define YYSTACK_RELOCATE(Stack_alloc, Stack)                           \
    do                                                                  \
      {                                                                 \
        YYPTRDIFF_T yynewbytes;                                         \
        YYCOPY (&yyptr->Stack_alloc, Stack, yysize);                    \
        Stack = &yyptr->Stack_alloc;                                    \
        yynewbytes = yystacksize * YYSIZEOF (*Stack) + YYSTACK_GAP_MAXIMUM; \
        yyptr += yynewbytes / YYSIZEOF (*yyptr);                        \
      }                                                                 \
    while (0)

#endif

#if defined YYCOPY_NEEDED && YYCOPY_NEEDED
/* Copy COUNT objects from SRC to DST.  The source and destination do
   not overlap.  */
# ifndef YYCOPY
#  if defined __GNUC__ && 1 < __GNUC__
#   define YYCOPY(Dst, Src, Count) \
      __builtin_memcpy (Dst, Src, YY_CAST (YYSIZE_T, (Count)) * sizeof (*(Src)))
#  else
#   define YYCOPY(Dst, Src, Count)              \
      do                                        \
        {                                       \
          YYPTRDIFF_T yyi;                      \
          for (yyi = 0; yyi < (Count); yyi++)   \
            (Dst)[yyi] = (Src)[yyi];            \
        }                                       \
      while (0)
#  endif
# endif
#endif /* !YYCOPY_NEEDED */

/* YYFINAL -- State number of the termination state.  */
#define YYFINAL  12
/* YYLAST -- Last index in YYTABLE.  */
#define YYLAST   448

/* YYNTOKENS -- Number of terminals.  */
#define YYNTOKENS  77
/* YYNNTS -- Number of nonterminals.  */
#define YYNNTS  119
/* YYNRULES -- Number of rules.  */
#define YYNRULES  223
/* YYNSTATES -- Number of states.  */
#define YYNSTATES  476

/* YYMAXUTOK -- Last valid token kind.  */
#define YYMAXUTOK   325


/* YYTRANSLATE(TOKEN-NUM) -- Symbol number corresponding to TOKEN-NUM
   as returned by yylex, with out-of-bounds checking.  */
#define YYTRANSLATE(YYX)                                \
  (0 <= (YYX) && (YYX) <= YYMAXUTOK                     \
   ? YY_CAST (yysymbol_kind_t, yytranslate[YYX])        \
   : YYSYMBOL_YYUNDEF)

/* YYTRANSLATE[TOKEN-NUM] -- Symbol number corresponding to TOKEN-NUM
   as returned by yylex.  */
static const yytype_int8 yytranslate[] =
{
       0,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
      71,    72,     2,     2,    69,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,    70,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,    73,     2,    74,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     2,     2,     2,     2,
       2,     2,     2,     2,     2,     2,     1,     2,     3,     4,
       5,     6,     7,     8,     9,    10,    11,    12,    13,    14,
      15,    16,    17,    18,    19,    20,    21,    22,    23,    24,
      25,    26,    27,    28,    29,    30,    31,    32,    33,    34,
      35,    36,    37,    38,    39,    40,    41,    42,    43,    44,
      45,    46,    47,    48,    49,    50,    51,    52,    53,    54,
      55,    56,    57,    58,    59,    60,    61,    62,    63,    64,
      65,    66,    67,    68,    75,    76
};

#if YYDEBUG
/* YYRLINE[YYN] -- Source line where rule number YYN was defined.  */
static const yytype_int16 yyrline[] =
{
       0,   169,   169,   170,   173,   174,   177,   178,   181,   208,
     245,   258,   266,   286,   287,   291,   294,   301,   305,   311,
     312,   315,   332,   333,   336,   347,   361,   375,   378,   379,
     382,   383,   386,   394,   395,   398,   413,   429,   439,   443,
     449,   467,   486,   489,   495,   505,   511,   520,   526,   531,
     537,   542,   548,   549,   552,   553,   554,   555,   556,   557,
     558,   559,   560,   561,   562,   563,   564,   567,   576,   589,
     609,   610,   613,   614,   617,   618,   621,   634,   638,   644,
     645,   648,   654,   670,   683,   689,   690,   693,   694,   697,
     698,   701,   712,   727,   740,   747,   756,   763,   772,   780,
     779,   789,   790,   793,   794,   795,   796,   797,   798,   799,
     800,   801,   802,   803,   804,   805,   806,   807,   808,   809,
     810,   811,   812,   816,   815,   851,   852,   855,   859,   863,
     867,   871,   878,   881,   891,   890,   918,   927,   937,   946,
     949,   952,   957,   961,   967,   978,   982,   988,   989,   992,
     998,  1016,  1033,  1075,  1089,  1095,  1112,  1130,  1129,  1159,
    1158,  1185,  1194,  1184,  1218,  1217,  1244,  1247,  1253,  1257,
    1277,  1293,  1306,  1319,  1334,  1349,  1415,  1433,  1450,  1468,
    1469,  1473,  1476,  1477,  1481,  1484,  1485,  1491,  1492,  1498,
    1506,  1509,  1519,  1523,  1526,  1530,  1536,  1537,  1538,  1544,
    1545,  1548,  1549,  1552,  1553,  1554,  1560,  1561,  1564,  1573,
    1582,  1591,  1600,  1603,  1614,  1626,  1629,  1630,  1634,  1637,
    1645,  1646,  1649,  1660
};
#endif

/** Accessing symbol of state STATE.  */
#define YY_ACCESSING_SYMBOL(State) YY_CAST (yysymbol_kind_t, yystos[State])

#if YYDEBUG || 0
/* The user-facing name of the symbol whose (internal) number is
   YYSYMBOL.  No bounds checking.  */
static const char *yysymbol_name (yysymbol_kind_t yysymbol) YY_ATTRIBUTE_UNUSED;

/* YYTNAME[SYMBOL-NUM] -- String name of the symbol SYMBOL-NUM.
   First, the terminals, then, starting at YYNTOKENS, nonterminals.  */
static const char *const yytname[] =
{
  "\"end of file\"", "error", "\"invalid token\"", "CHAR", "INTEGER",
  "BOOLEAN", "PERCENT", "MESSAGE_ID", "MAZE_ID", "LEVEL_ID", "LEV_INIT_ID",
  "GEOMETRY_ID", "NOMAP_ID", "OBJECT_ID", "COBJECT_ID", "MONSTER_ID",
  "TRAP_ID", "DOOR_ID", "DRAWBRIDGE_ID", "MAZEWALK_ID", "WALLIFY_ID",
  "REGION_ID", "FILLING", "RANDOM_OBJECTS_ID", "RANDOM_MONSTERS_ID",
  "RANDOM_PLACES_ID", "ALTAR_ID", "LADDER_ID", "STAIR_ID",
  "NON_DIGGABLE_ID", "NON_PASSWALL_ID", "ROOM_ID", "PORTAL_ID",
  "TELEPRT_ID", "BRANCH_ID", "LEV", "CHANCE_ID", "CORRIDOR_ID", "GOLD_ID",
  "ENGRAVING_ID", "FOUNTAIN_ID", "POOL_ID", "SINK_ID", "NONE",
  "RAND_CORRIDOR_ID", "DOOR_STATE", "LIGHT_STATE", "CURSE_TYPE",
  "ENGRAVING_TYPE", "DIRECTION", "RANDOM_TYPE", "O_REGISTER", "M_REGISTER",
  "P_REGISTER", "A_REGISTER", "ALIGNMENT", "LEFT_OR_RIGHT", "CENTER",
  "TOP_OR_BOT", "ALTAR_TYPE", "UP_OR_DOWN", "SUBROOM_ID", "NAME_ID",
  "FLAGS_ID", "FLAG_TYPE", "MON_ATTITUDE", "MON_ALERTNESS",
  "MON_APPEARANCE", "CONTAINED", "','", "':'", "'('", "')'", "'['", "']'",
  "STRING", "MAP_ID", "$accept", "file", "levels", "level", "maze_level",
  "room_level", "level_def", "lev_init", "walled", "flags", "flag_list",
  "messages", "message", "rreg_init", "init_rreg", "rooms", "roomlist",
  "corridors_def", "random_corridors", "corridors", "corridor",
  "corr_spec", "aroom", "subroom_def", "room_def", "roomfill", "room_pos",
  "subroom_pos", "room_align", "room_size", "room_details", "room_detail",
  "room_name", "room_chance", "room_door", "secret", "door_wall",
  "door_pos", "maze_def", "filling", "regions", "aregion",
  "map_definition", "map_geometry", "h_justif", "v_justif", "reg_init",
  "init_reg", "object_list", "monster_list", "place_list", "$@1",
  "map_details", "map_detail", "monster_detail", "$@2", "monster_infos",
  "monster_info", "object_detail", "object_desc", "$@3", "object_where",
  "object_infos", "curse_state", "monster_id", "enchantment",
  "optional_name", "door_detail", "trap_detail", "drawbridge_detail",
  "mazewalk_detail", "wallify_detail", "ladder_detail", "stair_detail",
  "stair_region", "$@4", "portal_region", "$@5", "teleprt_region", "$@6",
  "$@7", "branch_region", "$@8", "teleprt_detail", "lev_region",
  "fountain_detail", "sink_detail", "pool_detail", "diggable_detail",
  "passwall_detail", "region_detail", "altar_detail", "gold_detail",
  "engraving_detail", "monster_c", "object_c", "m_name", "o_name",
  "trap_name", "room_type", "prefilled", "coordinate", "door_state",
  "light_state", "alignment", "altar_type", "p_register", "o_register",
  "m_register", "a_register", "place", "monster", "object", "string",
  "amount", "chance", "engraving_type", "coord", "region", YY_NULLPTR
};

static const char *
yysymbol_name (yysymbol_kind_t yysymbol)
{
  return yytname[yysymbol];
}
#endif

#define YYPACT_NINF (-416)

#define yypact_value_is_default(Yyn) \
  ((Yyn) == YYPACT_NINF)

#define YYTABLE_NINF (-100)

#define yytable_value_is_error(Yyn) \
  0

/* YYPACT[STATE-NUM] -- Index in YYTABLE of the portion describing
   STATE-NUM.  */
static const yytype_int16 yypact[] =
{
     162,   -15,    34,   115,  -416,   162,  -416,  -416,    72,    72,
      38,    38,  -416,  -416,    90,   155,   155,  -416,   112,  -416,
     119,   114,   175,   175,    23,   120,  -416,   182,   121,  -416,
     175,   113,  -416,  -416,  -416,   119,   123,   111,    25,  -416,
     124,  -416,  -416,   113,  -416,   122,  -416,   184,  -416,   125,
     126,   127,   131,  -416,   144,  -416,     2,  -416,  -416,   117,
    -416,   128,  -416,   133,   187,   190,   -14,   -14,  -416,  -416,
    -416,   163,  -416,     3,     3,  -416,  -416,   136,   137,   138,
     139,  -416,   129,   194,  -416,  -416,   141,  -416,  -416,   142,
    -416,   143,  -416,   145,   146,  -416,   200,   200,   200,   200,
     147,   148,   149,   150,   151,   152,   153,   154,   156,   157,
    -416,  -416,  -416,  -416,  -416,  -416,  -416,  -416,  -416,  -416,
    -416,  -416,  -416,  -416,   118,   187,   190,   158,   160,   164,
     165,  -416,   166,   167,   168,   169,   170,   171,   172,   173,
    -416,  -416,  -416,  -416,  -416,  -416,  -416,  -416,  -416,  -416,
    -416,  -416,  -416,  -416,  -416,  -416,  -416,  -416,  -416,  -416,
    -416,   159,   187,   190,    55,    55,   161,  -416,  -416,   174,
    -416,   176,   177,    29,    41,    41,   209,    24,    41,    41,
      41,    41,    38,  -416,  -416,  -416,  -416,  -416,   211,  -416,
     179,  -416,    86,    41,    41,   178,    41,    16,   178,   178,
      12,    12,    12,   220,  -416,  -416,  -416,  -416,   181,   183,
     229,   185,    21,    18,   -13,  -416,  -416,   186,  -416,   180,
     188,  -416,  -416,   189,  -416,  -416,  -416,   191,   192,  -416,
    -416,  -416,  -416,   193,   195,  -416,  -416,   196,   197,   198,
     241,   199,   201,   202,   247,  -416,  -416,  -416,  -416,  -416,
    -416,  -416,   203,    -4,    45,   205,    11,  -416,   204,   206,
    -416,  -416,  -416,   207,   210,  -416,  -416,  -416,   212,  -416,
      86,   252,    73,   216,    41,   116,   255,   158,    41,   214,
     222,   213,    55,   218,   265,   215,   217,   219,   221,   223,
      55,  -416,   279,   225,  -416,   281,   226,   238,  -416,  -416,
     292,    27,   293,    31,    41,   230,   224,  -416,   227,  -416,
     232,  -416,  -416,  -416,  -416,  -416,   233,   231,  -416,  -416,
     235,  -416,   301,   237,  -416,   239,   303,    12,    12,    12,
      12,   240,   242,    49,   243,    50,   244,   236,  -416,  -416,
    -416,   245,  -416,   246,  -416,  -416,   130,  -416,   310,     0,
      38,  -416,    86,   248,   -14,   312,    65,   249,   251,  -416,
    -416,    30,   317,  -416,   117,   253,   319,  -416,   320,   256,
      26,  -416,   257,  -416,    41,  -416,  -416,   258,   254,  -416,
    -416,  -416,  -416,  -416,   325,   261,   262,   272,    38,   264,
    -416,  -416,  -416,   263,   267,    50,   266,   268,    38,  -416,
    -416,   269,    61,  -416,    26,  -416,   270,   321,  -416,   330,
    -416,  -416,   282,  -416,  -416,   118,   275,  -416,   341,   275,
    -416,  -416,   277,  -416,  -416,  -416,   343,   280,   283,  -416,
     276,   345,  -416,   284,  -416,    42,  -416,   285,   286,   346,
     349,  -416,  -416,  -416,  -416,  -416,  -416,   288,   290,    43,
    -416,  -416,  -416,   289,    10,    28,  -416,  -416,    38,  -416,
    -416,  -416,  -416,  -416,   291,   294,   294,  -416,    28,     9,
    -416,  -416,   294,  -416,  -416,  -416
};

/* YYDEFACT[STATE-NUM] -- Default reduction number in state STATE-NUM.
   Performed when YYTABLE does not specify something else to do.  Zero
   means the default is an error.  */
static const yytype_uint8 yydefact[] =
{
       2,     0,     0,     0,     3,     4,     6,     7,    15,    15,
       0,     0,     1,     5,     0,    11,    11,   215,     0,    10,
       0,     0,    19,    19,     0,    18,    16,     0,     0,    22,
      19,     0,    77,    78,    76,     0,     0,     0,    26,    20,
       0,    82,     8,    79,    89,     0,    17,     0,    21,     0,
       0,     0,     0,    23,    33,    27,    28,    52,    52,     0,
      80,   101,    83,     0,     0,     0,     0,     0,    32,     9,
      30,    31,    29,    39,    38,    85,    86,     0,     0,     0,
       0,    90,    81,     0,   214,    24,    94,   213,    25,    96,
     192,     0,   191,     0,     0,    34,   218,   218,   218,   218,
       0,     0,     0,     0,     0,     0,     0,     0,     0,     0,
      53,    54,    55,    56,    57,    58,    59,    66,    61,    62,
      63,    60,    64,    65,     0,     0,     0,     0,     0,     0,
       0,   154,     0,     0,     0,     0,     0,     0,     0,     0,
     102,   103,   104,   105,   106,   107,   115,   116,   117,   118,
     109,   110,   111,   112,   114,   121,   122,   108,   113,   119,
     120,     0,     0,     0,     0,     0,     0,   219,   132,     0,
     133,     0,     0,     0,     0,     0,     0,     0,     0,     0,
       0,     0,     0,    88,    87,    84,    91,    93,     0,    92,
      98,   212,     0,     0,     0,     0,     0,     0,     0,     0,
       0,     0,     0,     0,    95,    97,   201,   202,     0,     0,
       0,     0,     0,     0,     0,    70,    71,     0,   198,     0,
       0,   197,   196,     0,    68,   216,   217,     0,     0,   170,
     172,   171,    67,     0,     0,   199,   200,     0,     0,     0,
       0,     0,     0,     0,     0,   157,   168,   173,   174,   159,
     161,   164,     0,     0,     0,     0,     0,   183,     0,     0,
     184,   182,   180,     0,     0,   181,   179,   190,     0,   189,
       0,     0,     0,     0,     0,     0,     0,     0,     0,     0,
       0,     0,     0,     0,     0,     0,     0,     0,     0,     0,
       0,    45,     0,     0,    47,     0,     0,     0,    36,    35,
       0,     0,     0,     0,     0,     0,     0,   205,     0,   203,
       0,   204,   156,   177,   220,   221,     0,     0,   100,   150,
       0,   153,     0,     0,   155,     0,     0,     0,     0,     0,
       0,     0,     0,     0,     0,     0,     0,     0,   188,   134,
     187,     0,   186,     0,   185,   151,     0,   208,     0,     0,
       0,   222,     0,     0,     0,     0,     0,     0,     0,   162,
     165,     0,     0,    49,     0,     0,     0,    51,     0,     0,
       0,   209,     0,   210,     0,    72,    73,     0,     0,   207,
     206,   176,   178,   152,     0,   193,     0,     0,     0,   166,
      13,    14,    12,     0,     0,     0,     0,     0,     0,    74,
      75,     0,     0,   123,     0,   211,     0,     0,   175,     0,
     158,   160,     0,   163,    44,     0,    42,    46,     0,    42,
      37,   137,   138,   136,   125,    69,     0,   194,     0,   167,
       0,     0,    41,     0,    40,     0,   135,   124,     0,     0,
       0,    48,    43,    50,   143,   142,   144,     0,     0,     0,
     126,   223,   195,     0,     0,     0,   128,   129,     0,   130,
     127,   169,   146,   145,     0,   147,   147,   131,     0,     0,
     140,   141,   147,   148,   149,   139
};

/* YYPGOTO[NTERM-NUM].  */
static const yytype_int16 yypgoto[] =
{
    -416,  -416,   350,  -416,  -416,  -416,  -416,   348,  -416,   353,
     331,    96,  -416,  -416,  -416,  -416,   309,  -416,  -416,  -416,
    -416,   134,  -416,  -416,  -416,   -52,  -416,  -416,  -416,   -27,
     311,  -416,  -416,  -416,  -416,  -416,  -416,   -34,  -416,  -416,
     328,  -416,  -416,  -416,     8,   -42,  -416,  -416,   -98,   -88,
      97,  -416,  -416,  -416,   295,  -416,  -416,  -416,   297,   278,
    -416,  -416,  -416,  -416,   -78,  -415,  -376,  -416,   298,  -416,
    -416,  -416,  -416,   299,  -416,  -416,  -416,  -416,  -416,  -416,
    -416,  -416,  -416,  -416,  -189,   300,  -416,  -416,  -416,  -416,
    -416,   302,   304,   305,  -416,  -416,  -416,  -416,  -416,   -65,
    -416,  -171,  -264,  -160,   -66,  -416,  -416,  -416,  -416,  -416,
    -416,   208,   228,   -10,  -416,    79,  -416,  -123,  -141
};

/* YYDEFGOTO[NTERM-NUM].  */
static const yytype_int16 yydefgoto[] =
{
       0,     3,     4,     5,     6,     7,     8,    22,   392,    15,
      26,    29,    30,    38,    53,    54,    55,    69,    70,    71,
      95,   211,    56,    57,    58,   432,   293,   296,   365,   369,
      73,   110,   111,   112,   113,   217,   377,   401,     9,    34,
      42,    43,    44,    45,    77,   185,    61,    81,    85,    88,
     189,   234,    82,   140,   114,   424,   437,   450,   115,   168,
     372,   422,   436,   447,   448,   465,   470,   143,   116,   145,
     146,   147,   148,   117,   150,   286,   151,   287,   152,   288,
     389,   153,   289,   413,   245,   118,   119,   120,   155,   156,
     157,   121,   122,   123,   264,   259,   343,   339,   268,    91,
     408,   223,   237,   208,   310,   381,   221,   260,   265,   311,
     190,    89,    86,    92,   227,   169,   316,   222,   246
};

/* YYTABLE[YYPACT[STATE-NUM]] -- What to do in state STATE-NUM.  If
   positive, shift that token.  If negative, reduce the rule whose
   number is the opposite.  If YYTABLE_NINF, syntax error.  */
static const yytype_int16 yytable[] =
{
      18,    19,    93,   220,   191,   209,   305,   228,   229,   230,
     231,   249,   250,   251,   462,   298,    96,    97,    98,    99,
     100,    87,   238,   239,    84,   242,    32,   186,   225,   101,
     399,   102,   462,    51,   215,   390,    90,   267,   187,   103,
     466,   104,   105,   106,   107,   108,   291,   243,    49,    50,
     379,   243,   473,   472,   241,    10,    51,   247,   248,   380,
     463,    17,    17,    52,   204,   109,   218,   292,   262,   219,
     263,   257,   258,    33,   226,   205,   400,   338,   463,   216,
     391,   342,   210,   240,   474,   446,    52,   244,   383,   444,
     471,   218,   445,   307,   219,   294,   475,   308,   309,   363,
     367,   206,    17,   313,    11,   207,    17,   319,   456,   457,
     458,   218,   188,    17,   219,    12,   295,   446,    17,    31,
     364,   368,   323,   307,    40,    41,    39,   308,   309,   421,
     331,   235,   188,   345,   384,    14,   236,   351,   357,   358,
     359,   360,    96,    97,    98,    99,   128,   129,   130,   131,
     132,    78,    79,    80,   191,   101,   133,   134,   135,   136,
      20,   137,   138,   139,   314,    21,   315,   104,   105,   106,
       1,     2,   232,    75,    76,   183,   184,   171,   172,   375,
     376,    24,    28,    25,    27,    36,    48,    63,    68,    35,
      84,    37,    47,    87,    59,    64,    65,    66,    62,   161,
      94,    67,    83,   403,   269,   124,   167,   125,   126,   127,
     162,   163,   164,   224,   165,   233,   166,   173,   174,   175,
     176,   177,   178,   179,   180,   252,   181,   182,   203,   188,
     192,   423,   210,   255,   193,   194,   195,   196,   197,   198,
     199,   200,   201,   202,   212,   281,   213,   214,   -99,   240,
     253,   285,   254,   271,   256,   270,   306,   272,   273,   317,
     274,   275,   276,   320,   277,   278,   279,   280,   282,   325,
     283,   321,   290,   284,   297,   301,   312,   300,   324,   303,
     302,   304,   322,   332,   326,   334,   327,   336,   328,   385,
     329,   340,   330,   344,   333,   335,   337,   341,   347,   346,
     348,   349,   350,   351,   352,   353,   354,   356,   355,   361,
     371,   362,   366,   370,   378,   374,   386,   384,   387,   373,
     388,   393,   395,   396,   397,   398,   402,   404,   405,   406,
     407,   409,   410,   412,   428,   414,   415,   418,   417,   426,
     382,   420,   429,   427,   431,   433,   435,   438,   441,   439,
     442,   452,   440,   453,   449,    13,   443,   454,   451,   455,
     468,   461,    16,   469,    23,    72,    46,   434,   416,    74,
     425,    60,   394,   430,   318,   170,   464,   141,   411,   142,
     144,   149,   154,   459,   158,     0,   159,   160,   419,     0,
     299,     0,     0,     0,     0,     0,     0,     0,     0,     0,
       0,     0,     0,     0,     0,     0,     0,     0,     0,     0,
       0,     0,     0,     0,     0,     0,     0,     0,     0,     0,
       0,   266,     0,     0,     0,     0,     0,     0,     0,     0,
       0,     0,     0,     0,     0,     0,     0,     0,     0,   460,
     261,     0,     0,     0,     0,     0,     0,     0,   467
};

static const yytype_int16 yycheck[] =
{
      10,    11,    67,   174,   127,   165,   270,   178,   179,   180,
     181,   200,   201,   202,     4,     4,    13,    14,    15,    16,
      17,     3,   193,   194,     3,   196,     3,   125,     4,    26,
       4,    28,     4,    31,     5,     5,    50,    50,   126,    36,
     455,    38,    39,    40,    41,    42,    50,    35,    23,    24,
      50,    35,    43,   468,   195,    70,    31,   198,   199,    59,
      50,    75,    75,    61,   162,    62,    50,    71,    50,    53,
      52,    50,    51,    50,    50,   163,    50,    50,    50,    50,
      50,    50,    71,    71,    75,    75,    61,    71,   352,    47,
     466,    50,    50,    50,    53,    50,   472,    54,    55,    50,
      50,    46,    75,   274,    70,    50,    75,   278,    65,    66,
      67,    50,    71,    75,    53,     0,    71,    75,    75,    23,
      71,    71,   282,    50,    11,    12,    30,    54,    55,    68,
     290,    45,    71,   304,    69,    63,    50,    72,   327,   328,
     329,   330,    13,    14,    15,    16,    17,    18,    19,    20,
      21,    23,    24,    25,   277,    26,    27,    28,    29,    30,
      70,    32,    33,    34,    48,    10,    50,    38,    39,    40,
       8,     9,   182,    56,    57,    57,    58,    98,    99,    49,
      50,    69,     7,    64,    70,     3,    75,     3,    44,    69,
       3,    70,    69,     3,    70,    70,    70,    70,    76,     5,
      37,    70,    69,   374,   214,    69,     6,    70,    70,    70,
      69,    69,    69,     4,    69,     4,    70,    70,    70,    70,
      70,    70,    70,    70,    70,     5,    70,    70,    69,    71,
      70,   402,    71,     4,    70,    70,    70,    70,    70,    70,
      70,    70,    70,    70,    70,     4,    70,    70,    69,    71,
      69,     4,    69,    73,    69,    69,     4,    69,    69,     4,
      69,    69,    69,    49,    69,    69,    69,    69,    69,     4,
      69,    49,    69,    71,    69,    69,    60,    73,    60,    69,
      73,    69,    69,     4,    69,     4,    69,    49,    69,   354,
      69,   301,    69,   303,    69,    69,     4,     4,    74,    69,
      73,    69,    69,    72,    69,     4,    69,     4,    69,    69,
      74,    69,    69,    69,     4,    69,     4,    69,    69,    74,
      69,     4,    69,     4,     4,    69,    69,    69,    74,     4,
      69,    69,    60,    69,     4,    72,    69,    69,    72,    69,
     350,    72,    60,    22,    69,     4,    69,     4,    72,    69,
       5,     5,    69,     4,    69,     5,    72,    69,    72,    69,
      69,    72,     9,    69,    16,    56,    35,   419,   395,    58,
     404,    43,   364,   415,   277,    97,   454,    82,   388,    82,
      82,    82,    82,   449,    82,    -1,    82,    82,   398,    -1,
     256,    -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,
      -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,
      -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,
      -1,   213,    -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,
      -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,    -1,   449,
     212,    -1,    -1,    -1,    -1,    -1,    -1,    -1,   458
};

/* YYSTOS[STATE-NUM] -- The symbol kind of the accessing symbol of
   state STATE-NUM.  */
static const yytype_uint8 yystos[] =
{
       0,     8,     9,    78,    79,    80,    81,    82,    83,   115,
      70,    70,     0,    79,    63,    86,    86,    75,   190,   190,
      70,    10,    84,    84,    69,    64,    87,    70,     7,    88,
      89,    88,     3,    50,   116,    69,     3,    70,    90,    88,
      11,    12,   117,   118,   119,   120,    87,    69,    75,    23,
      24,    31,    61,    91,    92,    93,    99,   100,   101,    70,
     117,   123,    76,     3,    70,    70,    70,    70,    44,    94,
      95,    96,    93,   107,   107,    56,    57,   121,    23,    24,
      25,   124,   129,    69,     3,   125,   189,     3,   126,   188,
      50,   176,   190,   176,    37,    97,    13,    14,    15,    16,
      17,    26,    28,    36,    38,    39,    40,    41,    42,    62,
     108,   109,   110,   111,   131,   135,   145,   150,   162,   163,
     164,   168,   169,   170,    69,    70,    70,    70,    17,    18,
      19,    20,    21,    27,    28,    29,    30,    32,    33,    34,
     130,   131,   135,   144,   145,   146,   147,   148,   149,   150,
     151,   153,   155,   158,   162,   165,   166,   167,   168,   169,
     170,     5,    69,    69,    69,    69,    70,     6,   136,   192,
     136,   192,   192,    70,    70,    70,    70,    70,    70,    70,
      70,    70,    70,    57,    58,   122,   125,   126,    71,   127,
     187,   194,    70,    70,    70,    70,    70,    70,    70,    70,
      70,    70,    70,    69,   125,   126,    46,    50,   180,   180,
      71,    98,    70,    70,    70,     5,    50,   112,    50,    53,
     178,   183,   194,   178,     4,     4,    50,   191,   178,   178,
     178,   178,   190,     4,   128,    45,    50,   179,   178,   178,
      71,   195,   178,    35,    71,   161,   195,   195,   195,   161,
     161,   161,     5,    69,    69,     4,    69,    50,    51,   172,
     184,   189,    50,    52,   171,   185,   188,    50,   175,   190,
      69,    73,    69,    69,    69,    69,    69,    69,    69,    69,
      69,     4,    69,    69,    71,     4,   152,   154,   156,   159,
      69,    50,    71,   103,    50,    71,   104,    69,     4,    98,
      73,    69,    73,    69,    69,   179,     4,    50,    54,    55,
     181,   186,    60,   178,    48,    50,   193,     4,   127,   178,
      49,    49,    69,   180,    60,     4,    69,    69,    69,    69,
      69,   180,     4,    69,     4,    69,    49,     4,    50,   174,
     190,     4,    50,   173,   190,   178,    69,    74,    73,    69,
      69,    72,    69,     4,    69,    69,     4,   161,   161,   161,
     161,    69,    69,    50,    71,   105,    69,    50,    71,   106,
      69,    74,   137,    74,    69,    49,    50,   113,     4,    50,
      59,   182,   190,   179,    69,   176,     4,    69,    69,   157,
       5,    50,    85,     4,   121,    69,     4,     4,    69,     4,
      50,   114,    69,   178,    69,    74,     4,    69,   177,    69,
      60,   190,    69,   160,    72,    69,   106,    72,    69,   190,
      72,    68,   138,   178,   132,   114,    69,    22,     4,    60,
     122,    69,   102,     4,   102,    69,   139,   133,     4,    69,
      69,    72,     5,    72,    47,    50,    75,   140,   141,    69,
     134,    72,     5,     4,    69,    69,    65,    66,    67,   181,
     190,    72,     4,    50,   141,   142,   142,   190,    69,    69,
     143,   143,   142,    43,    75,   143
};

/* YYR1[RULE-NUM] -- Symbol kind of the left-hand side of rule RULE-NUM.  */
static const yytype_uint8 yyr1[] =
{
       0,    77,    78,    78,    79,    79,    80,    80,    81,    82,
      83,    84,    84,    85,    85,    86,    86,    87,    87,    88,
      88,    89,    90,    90,    91,    91,    92,    92,    93,    93,
      94,    94,    95,    96,    96,    97,    97,    98,    99,    99,
     100,   101,   102,   102,   103,   103,   104,   104,   105,   105,
     106,   106,   107,   107,   108,   108,   108,   108,   108,   108,
     108,   108,   108,   108,   108,   108,   108,   109,   110,   111,
     112,   112,   113,   113,   114,   114,   115,   116,   116,   117,
     117,   118,   119,   119,   120,   121,   121,   122,   122,   123,
     123,   124,   124,   124,   125,   125,   126,   126,   127,   128,
     127,   129,   129,   130,   130,   130,   130,   130,   130,   130,
     130,   130,   130,   130,   130,   130,   130,   130,   130,   130,
     130,   130,   130,   132,   131,   133,   133,   134,   134,   134,
     134,   134,   135,   135,   137,   136,   138,   138,   139,   139,
     139,   139,   140,   140,   141,   142,   142,   143,   143,   143,
     144,   145,   146,   147,   148,   149,   150,   152,   151,   154,
     153,   156,   157,   155,   159,   158,   160,   160,   161,   161,
     162,   163,   164,   165,   166,   167,   168,   169,   170,   171,
     171,   171,   172,   172,   172,   173,   173,   174,   174,   175,
     175,   176,   176,   177,   177,   177,   178,   178,   178,   179,
     179,   180,   180,   181,   181,   181,   182,   182,   183,   184,
     185,   186,   187,   188,   189,   190,   191,   191,   192,   192,
     193,   193,   194,   195
};

/* YYR2[RULE-NUM] -- Number of symbols on the right-hand side of rule RULE-NUM.  */
static const yytype_int8 yyr2[] =
{
       0,     2,     0,     1,     1,     2,     1,     1,     5,     7,
       3,     0,    13,     1,     1,     0,     3,     3,     1,     0,
       2,     3,     0,     2,     3,     3,     0,     1,     1,     2,
       1,     1,     1,     0,     2,     5,     5,     7,     2,     2,
      12,    12,     0,     2,     5,     1,     5,     1,     5,     1,
       5,     1,     0,     2,     1,     1,     1,     1,     1,     1,
       1,     1,     1,     1,     1,     1,     1,     3,     3,     9,
       1,     1,     1,     1,     1,     1,     5,     1,     1,     1,
       2,     3,     1,     2,     5,     1,     1,     1,     1,     0,
       2,     3,     3,     3,     1,     3,     1,     3,     1,     0,
       4,     0,     2,     1,     1,     1,     1,     1,     1,     1,
       1,     1,     1,     1,     1,     1,     1,     1,     1,     1,
       1,     1,     1,     0,    10,     0,     2,     2,     2,     2,
       2,     3,     2,     2,     0,     9,     1,     1,     0,     7,
       5,     5,     1,     1,     1,     1,     1,     0,     2,     2,
       5,     6,     7,     5,     1,     5,     5,     0,     8,     0,
       8,     0,     0,     8,     0,     6,     0,     2,     1,    10,
       3,     3,     3,     3,     3,     8,     7,     5,     7,     1,
       1,     1,     1,     1,     1,     1,     1,     1,     1,     1,
       1,     1,     1,     0,     2,     4,     1,     1,     1,     1,
       1,     1,     1,     1,     1,     1,     1,     1,     4,     4,
       4,     4,     1,     1,     1,     1,     1,     1,     0,     1,
       1,     1,     5,     9
};


enum { YYENOMEM = -2 };

#define yyerrok         (yyerrstatus = 0)
#define yyclearin       (yychar = YYEMPTY)

#define YYACCEPT        goto yyacceptlab
#define YYABORT         goto yyabortlab
#define YYERROR         goto yyerrorlab
#define YYNOMEM         goto yyexhaustedlab


#define YYRECOVERING()  (!!yyerrstatus)

#define YYBACKUP(Token, Value)                                    \
  do                                                              \
    if (yychar == YYEMPTY)                                        \
      {                                                           \
        yychar = (Token);                                         \
        yylval = (Value);                                         \
        YYPOPSTACK (yylen);                                       \
        yystate = *yyssp;                                         \
        goto yybackup;                                            \
      }                                                           \
    else                                                          \
      {                                                           \
        yyerror (YY_("syntax error: cannot back up")); \
        YYERROR;                                                  \
      }                                                           \
  while (0)

/* Backward compatibility with an undocumented macro.
   Use YYerror or YYUNDEF. */
#define YYERRCODE YYUNDEF


/* Enable debugging if requested.  */
#if YYDEBUG

# ifndef YYFPRINTF
#  include <stdio.h> /* INFRINGES ON USER NAME SPACE */
#  define YYFPRINTF fprintf
# endif

# define YYDPRINTF(Args)                        \
do {                                            \
  if (yydebug)                                  \
    YYFPRINTF Args;                             \
} while (0)




# define YY_SYMBOL_PRINT(Title, Kind, Value, Location)                    \
do {                                                                      \
  if (yydebug)                                                            \
    {                                                                     \
      YYFPRINTF (stderr, "%s ", Title);                                   \
      yy_symbol_print (stderr,                                            \
                  Kind, Value); \
      YYFPRINTF (stderr, "\n");                                           \
    }                                                                     \
} while (0)


/*-----------------------------------.
| Print this symbol's value on YYO.  |
`-----------------------------------*/

static void
yy_symbol_value_print (FILE *yyo,
                       yysymbol_kind_t yykind, YYSTYPE const * const yyvaluep)
{
  FILE *yyoutput = yyo;
  YY_USE (yyoutput);
  if (!yyvaluep)
    return;
  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  YY_USE (yykind);
  YY_IGNORE_MAYBE_UNINITIALIZED_END
}


/*---------------------------.
| Print this symbol on YYO.  |
`---------------------------*/

static void
yy_symbol_print (FILE *yyo,
                 yysymbol_kind_t yykind, YYSTYPE const * const yyvaluep)
{
  YYFPRINTF (yyo, "%s %s (",
             yykind < YYNTOKENS ? "token" : "nterm", yysymbol_name (yykind));

  yy_symbol_value_print (yyo, yykind, yyvaluep);
  YYFPRINTF (yyo, ")");
}

/*------------------------------------------------------------------.
| yy_stack_print -- Print the state stack from its BOTTOM up to its |
| TOP (included).                                                   |
`------------------------------------------------------------------*/

static void
yy_stack_print (yy_state_t *yybottom, yy_state_t *yytop)
{
  YYFPRINTF (stderr, "Stack now");
  for (; yybottom <= yytop; yybottom++)
    {
      int yybot = *yybottom;
      YYFPRINTF (stderr, " %d", yybot);
    }
  YYFPRINTF (stderr, "\n");
}

# define YY_STACK_PRINT(Bottom, Top)                            \
do {                                                            \
  if (yydebug)                                                  \
    yy_stack_print ((Bottom), (Top));                           \
} while (0)


/*------------------------------------------------.
| Report that the YYRULE is going to be reduced.  |
`------------------------------------------------*/

static void
yy_reduce_print (yy_state_t *yyssp, YYSTYPE *yyvsp,
                 int yyrule)
{
  int yylno = yyrline[yyrule];
  int yynrhs = yyr2[yyrule];
  int yyi;
  YYFPRINTF (stderr, "Reducing stack by rule %d (line %d):\n",
             yyrule - 1, yylno);
  /* The symbols being reduced.  */
  for (yyi = 0; yyi < yynrhs; yyi++)
    {
      YYFPRINTF (stderr, "   $%d = ", yyi + 1);
      yy_symbol_print (stderr,
                       YY_ACCESSING_SYMBOL (+yyssp[yyi + 1 - yynrhs]),
                       &yyvsp[(yyi + 1) - (yynrhs)]);
      YYFPRINTF (stderr, "\n");
    }
}

# define YY_REDUCE_PRINT(Rule)          \
do {                                    \
  if (yydebug)                          \
    yy_reduce_print (yyssp, yyvsp, Rule); \
} while (0)

/* Nonzero means print parse trace.  It is left uninitialized so that
   multiple parsers can coexist.  */
int yydebug;
#else /* !YYDEBUG */
# define YYDPRINTF(Args) ((void) 0)
# define YY_SYMBOL_PRINT(Title, Kind, Value, Location)
# define YY_STACK_PRINT(Bottom, Top)
# define YY_REDUCE_PRINT(Rule)
#endif /* !YYDEBUG */


/* YYINITDEPTH -- initial size of the parser's stacks.  */
#ifndef YYINITDEPTH
# define YYINITDEPTH 200
#endif

/* YYMAXDEPTH -- maximum size the stacks can grow to (effective only
   if the built-in stack extension method is used).

   Do not make this value too large; the results are undefined if
   YYSTACK_ALLOC_MAXIMUM < YYSTACK_BYTES (YYMAXDEPTH)
   evaluated with infinite-precision integer arithmetic.  */

#ifndef YYMAXDEPTH
# define YYMAXDEPTH 10000
#endif






/*-----------------------------------------------.
| Release the memory associated to this symbol.  |
`-----------------------------------------------*/

static void
yydestruct (const char *yymsg,
            yysymbol_kind_t yykind, YYSTYPE *yyvaluep)
{
  YY_USE (yyvaluep);
  if (!yymsg)
    yymsg = "Deleting";
  YY_SYMBOL_PRINT (yymsg, yykind, yyvaluep, yylocationp);

  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  YY_USE (yykind);
  YY_IGNORE_MAYBE_UNINITIALIZED_END
}


/* Lookahead token kind.  */
int yychar;

/* The semantic value of the lookahead symbol.  */
YYSTYPE yylval;
/* Number of syntax errors so far.  */
int yynerrs;




/*----------.
| yyparse.  |
`----------*/

int
yyparse (void)
{
    yy_state_fast_t yystate = 0;
    /* Number of tokens to shift before error messages enabled.  */
    int yyerrstatus = 0;

    /* Refer to the stacks through separate pointers, to allow yyoverflow
       to reallocate them elsewhere.  */

    /* Their size.  */
    YYPTRDIFF_T yystacksize = YYINITDEPTH;

    /* The state stack: array, bottom, top.  */
    yy_state_t yyssa[YYINITDEPTH];
    yy_state_t *yyss = yyssa;
    yy_state_t *yyssp = yyss;

    /* The semantic value stack: array, bottom, top.  */
    YYSTYPE yyvsa[YYINITDEPTH];
    YYSTYPE *yyvs = yyvsa;
    YYSTYPE *yyvsp = yyvs;

  int yyn;
  /* The return value of yyparse.  */
  int yyresult;
  /* Lookahead symbol kind.  */
  yysymbol_kind_t yytoken = YYSYMBOL_YYEMPTY;
  /* The variables used to return semantic value and location from the
     action routines.  */
  YYSTYPE yyval;



#define YYPOPSTACK(N)   (yyvsp -= (N), yyssp -= (N))

  /* The number of symbols on the RHS of the reduced rule.
     Keep to zero when no symbol should be popped.  */
  int yylen = 0;

  YYDPRINTF ((stderr, "Starting parse\n"));

  yychar = YYEMPTY; /* Cause a token to be read.  */

  goto yysetstate;


/*------------------------------------------------------------.
| yynewstate -- push a new state, which is found in yystate.  |
`------------------------------------------------------------*/
yynewstate:
  /* In all cases, when you get here, the value and location stacks
     have just been pushed.  So pushing a state here evens the stacks.  */
  yyssp++;


/*--------------------------------------------------------------------.
| yysetstate -- set current state (the top of the stack) to yystate.  |
`--------------------------------------------------------------------*/
yysetstate:
  YYDPRINTF ((stderr, "Entering state %d\n", yystate));
  YY_ASSERT (0 <= yystate && yystate < YYNSTATES);
  YY_IGNORE_USELESS_CAST_BEGIN
  *yyssp = YY_CAST (yy_state_t, yystate);
  YY_IGNORE_USELESS_CAST_END
  YY_STACK_PRINT (yyss, yyssp);

  if (yyss + yystacksize - 1 <= yyssp)
#if !defined yyoverflow && !defined YYSTACK_RELOCATE
    YYNOMEM;
#else
    {
      /* Get the current used size of the three stacks, in elements.  */
      YYPTRDIFF_T yysize = yyssp - yyss + 1;

# if defined yyoverflow
      {
        /* Give user a chance to reallocate the stack.  Use copies of
           these so that the &'s don't force the real ones into
           memory.  */
        yy_state_t *yyss1 = yyss;
        YYSTYPE *yyvs1 = yyvs;

        /* Each stack pointer address is followed by the size of the
           data in use in that stack, in bytes.  This used to be a
           conditional around just the two extra args, but that might
           be undefined if yyoverflow is a macro.  */
        yyoverflow (YY_("memory exhausted"),
                    &yyss1, yysize * YYSIZEOF (*yyssp),
                    &yyvs1, yysize * YYSIZEOF (*yyvsp),
                    &yystacksize);
        yyss = yyss1;
        yyvs = yyvs1;
      }
# else /* defined YYSTACK_RELOCATE */
      /* Extend the stack our own way.  */
      if (YYMAXDEPTH <= yystacksize)
        YYNOMEM;
      yystacksize *= 2;
      if (YYMAXDEPTH < yystacksize)
        yystacksize = YYMAXDEPTH;

      {
        yy_state_t *yyss1 = yyss;
        union yyalloc *yyptr =
          YY_CAST (union yyalloc *,
                   YYSTACK_ALLOC (YY_CAST (YYSIZE_T, YYSTACK_BYTES (yystacksize))));
        if (! yyptr)
          YYNOMEM;
        YYSTACK_RELOCATE (yyss_alloc, yyss);
        YYSTACK_RELOCATE (yyvs_alloc, yyvs);
#  undef YYSTACK_RELOCATE
        if (yyss1 != yyssa)
          YYSTACK_FREE (yyss1);
      }
# endif

      yyssp = yyss + yysize - 1;
      yyvsp = yyvs + yysize - 1;

      YY_IGNORE_USELESS_CAST_BEGIN
      YYDPRINTF ((stderr, "Stack size increased to %ld\n",
                  YY_CAST (long, yystacksize)));
      YY_IGNORE_USELESS_CAST_END

      if (yyss + yystacksize - 1 <= yyssp)
        YYABORT;
    }
#endif /* !defined yyoverflow && !defined YYSTACK_RELOCATE */


  if (yystate == YYFINAL)
    YYACCEPT;

  goto yybackup;


/*-----------.
| yybackup.  |
`-----------*/
yybackup:
  /* Do appropriate processing given the current state.  Read a
     lookahead token if we need one and don't already have one.  */

  /* First try to decide what to do without reference to lookahead token.  */
  yyn = yypact[yystate];
  if (yypact_value_is_default (yyn))
    goto yydefault;

  /* Not known => get a lookahead token if don't already have one.  */

  /* YYCHAR is either empty, or end-of-input, or a valid lookahead.  */
  if (yychar == YYEMPTY)
    {
      YYDPRINTF ((stderr, "Reading a token\n"));
      yychar = yylex ();
    }

  if (yychar <= YYEOF)
    {
      yychar = YYEOF;
      yytoken = YYSYMBOL_YYEOF;
      YYDPRINTF ((stderr, "Now at end of input.\n"));
    }
  else if (yychar == YYerror)
    {
      /* The scanner already issued an error message, process directly
         to error recovery.  But do not keep the error token as
         lookahead, it is too special and may lead us to an endless
         loop in error recovery. */
      yychar = YYUNDEF;
      yytoken = YYSYMBOL_YYerror;
      goto yyerrlab1;
    }
  else
    {
      yytoken = YYTRANSLATE (yychar);
      YY_SYMBOL_PRINT ("Next token is", yytoken, &yylval, &yylloc);
    }

  /* If the proper action on seeing token YYTOKEN is to reduce or to
     detect an error, take that action.  */
  yyn += yytoken;
  if (yyn < 0 || YYLAST < yyn || yycheck[yyn] != yytoken)
    goto yydefault;
  yyn = yytable[yyn];
  if (yyn <= 0)
    {
      if (yytable_value_is_error (yyn))
        goto yyerrlab;
      yyn = -yyn;
      goto yyreduce;
    }

  /* Count tokens shifted since error; after three, turn off error
     status.  */
  if (yyerrstatus)
    yyerrstatus--;

  /* Shift the lookahead token.  */
  YY_SYMBOL_PRINT ("Shifting", yytoken, &yylval, &yylloc);
  yystate = yyn;
  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  *++yyvsp = yylval;
  YY_IGNORE_MAYBE_UNINITIALIZED_END

  /* Discard the shifted token.  */
  yychar = YYEMPTY;
  goto yynewstate;


/*-----------------------------------------------------------.
| yydefault -- do the default action for the current state.  |
`-----------------------------------------------------------*/
yydefault:
  yyn = yydefact[yystate];
  if (yyn == 0)
    goto yyerrlab;
  goto yyreduce;


/*-----------------------------.
| yyreduce -- do a reduction.  |
`-----------------------------*/
yyreduce:
  /* yyn is the number of a rule to reduce with.  */
  yylen = yyr2[yyn];

  /* If YYLEN is nonzero, implement the default value of the action:
     '$$ = $1'.

     Otherwise, the following line sets YYVAL to garbage.
     This behavior is undocumented and Bison
     users should not rely upon it.  Assigning to YYVAL
     unconditionally makes the parser a bit smaller, and it avoids a
     GCC warning that YYVAL may be used uninitialized.  */
  yyval = yyvsp[1-yylen];


  YY_REDUCE_PRINT (yyn);
  switch (yyn)
    {
  case 8: /* maze_level: maze_def flags lev_init messages regions  */
#line 182 "lev_comp.y"
                  {
			unsigned i;

			if (fatal_error > 0) {
				(void) fprintf(stderr,
				"%s : %d errors detected. No output created!\n",
					fname, fatal_error);
			} else {
				maze.flags = (yyvsp[-3].i);
				(void) memcpy((genericptr_t)&(maze.init_lev),
						(genericptr_t)&(init_lev),
						sizeof(lev_init));
				maze.numpart = npart;
				maze.parts = NewTab(mazepart, npart);
				for(i=0;i<npart;i++)
				    maze.parts[i] = tmppart[i];
				if (!write_level_file((yyvsp[-4].map), (splev *)0, &maze)) {
					yyerror("Can't write output file!!");
					exit(EXIT_FAILURE);
				}
				npart = 0;
			}
			Free((yyvsp[-4].map));
		  }
#line 1948 "y.tab.c"
    break;

  case 9: /* room_level: level_def flags lev_init messages rreg_init rooms corridors_def  */
#line 209 "lev_comp.y"
                  {
			unsigned i;

			if (fatal_error > 0) {
			    (void) fprintf(stderr,
			      "%s : %d errors detected. No output created!\n",
					fname, fatal_error);
			} else {
				special_lev.flags = (long) (yyvsp[-5].i);
				(void) memcpy(
					(genericptr_t)&(special_lev.init_lev),
					(genericptr_t)&(init_lev),
					sizeof(lev_init));
				special_lev.nroom = nrooms;
				special_lev.rooms = NewTab(room, nrooms);
				for(i=0; i<nrooms; i++)
				    special_lev.rooms[i] = tmproom[i];
				special_lev.ncorr = ncorridor;
				special_lev.corrs = NewTab(corridor, ncorridor);
				for(i=0; i<ncorridor; i++)
				    special_lev.corrs[i] = tmpcor[i];
				if (check_subrooms()) {
				    if (!write_level_file((yyvsp[-6].map), &special_lev,
							  (specialmaze *)0)) {
					yyerror("Can't write output file!!");
					exit(EXIT_FAILURE);
				    }
				}
				free_rooms(&special_lev);
				nrooms = 0;
				ncorridor = 0;
			}
			Free((yyvsp[-6].map));
		  }
#line 1987 "y.tab.c"
    break;

  case 10: /* level_def: LEVEL_ID ':' string  */
#line 246 "lev_comp.y"
                  {
			if (index((yyvsp[0].map), '.'))
			    yyerror("Invalid dot ('.') in level name.");
			if ((int) strlen((yyvsp[0].map)) > 8)
			    yyerror("Level names limited to 8 characters.");
			(yyval.map) = (yyvsp[0].map);
			special_lev.nrmonst = special_lev.nrobjects = 0;
			n_mlist = n_olist = 0;
		  }
#line 2001 "y.tab.c"
    break;

  case 11: /* lev_init: %empty  */
#line 258 "lev_comp.y"
                  {
			/* in case we're processing multiple files,
			   explicitly clear any stale settings */
			(void) memset((genericptr_t) &init_lev, 0,
					sizeof init_lev);
			init_lev.init_present = FALSE;
			(yyval.i) = 0;
		  }
#line 2014 "y.tab.c"
    break;

  case 12: /* lev_init: LEV_INIT_ID ':' CHAR ',' CHAR ',' BOOLEAN ',' BOOLEAN ',' light_state ',' walled  */
#line 267 "lev_comp.y"
                  {
			init_lev.init_present = TRUE;
			init_lev.fg = what_map_char((char) (yyvsp[-10].i));
			if (init_lev.fg == INVALID_TYPE)
			    yyerror("Invalid foreground type.");
			init_lev.bg = what_map_char((char) (yyvsp[-8].i));
			if (init_lev.bg == INVALID_TYPE)
			    yyerror("Invalid background type.");
			init_lev.smoothed = (yyvsp[-6].i);
			init_lev.joined = (yyvsp[-4].i);
			if (init_lev.joined &&
			    init_lev.fg != CORR && init_lev.fg != ROOM)
			    yyerror("Invalid foreground type for joined map.");
			init_lev.lit = (yyvsp[-2].i);
			init_lev.walled = (yyvsp[0].i);
			(yyval.i) = 1;
		  }
#line 2036 "y.tab.c"
    break;

  case 15: /* flags: %empty  */
#line 291 "lev_comp.y"
                  {
			(yyval.i) = 0;
		  }
#line 2044 "y.tab.c"
    break;

  case 16: /* flags: FLAGS_ID ':' flag_list  */
#line 295 "lev_comp.y"
                  {
			(yyval.i) = lev_flags;
			lev_flags = 0;	/* clear for next user */
		  }
#line 2053 "y.tab.c"
    break;

  case 17: /* flag_list: FLAG_TYPE ',' flag_list  */
#line 302 "lev_comp.y"
                  {
			lev_flags |= (yyvsp[-2].i);
		  }
#line 2061 "y.tab.c"
    break;

  case 18: /* flag_list: FLAG_TYPE  */
#line 306 "lev_comp.y"
                  {
			lev_flags |= (yyvsp[0].i);
		  }
#line 2069 "y.tab.c"
    break;

  case 21: /* message: MESSAGE_ID ':' STRING  */
#line 316 "lev_comp.y"
                  {
			int i, j;

			i = (int) strlen((yyvsp[0].map)) + 1;
			j = (int) strlen(tmpmessage);
			if (i + j > 255) {
			   yyerror("Message string too long (>256 characters)");
			} else {
			    if (j) tmpmessage[j++] = '\n';
			    (void) strncpy(tmpmessage+j, (yyvsp[0].map), i - 1);
			    tmpmessage[j + i - 1] = 0;
			}
			Free((yyvsp[0].map));
		  }
#line 2088 "y.tab.c"
    break;

  case 24: /* init_rreg: RANDOM_OBJECTS_ID ':' object_list  */
#line 337 "lev_comp.y"
                  {
			if(special_lev.nrobjects) {
			    yyerror("Object registers already initialized!");
			} else {
			    special_lev.nrobjects = n_olist;
			    special_lev.robjects = (char *) alloc(n_olist);
			    (void) memcpy((genericptr_t)special_lev.robjects,
					  (genericptr_t)olist, n_olist);
			}
		  }
#line 2103 "y.tab.c"
    break;

  case 25: /* init_rreg: RANDOM_MONSTERS_ID ':' monster_list  */
#line 348 "lev_comp.y"
                  {
			if(special_lev.nrmonst) {
			    yyerror("Monster registers already initialized!");
			} else {
			    special_lev.nrmonst = n_mlist;
			    special_lev.rmonst = (char *) alloc(n_mlist);
			    (void) memcpy((genericptr_t)special_lev.rmonst,
					  (genericptr_t)mlist, n_mlist);
			  }
		  }
#line 2118 "y.tab.c"
    break;

  case 26: /* rooms: %empty  */
#line 361 "lev_comp.y"
                  {
			tmproom[nrooms] = New(room);
			tmproom[nrooms]->name = (char *) 0;
			tmproom[nrooms]->parent = (char *) 0;
			tmproom[nrooms]->rtype = 0;
			tmproom[nrooms]->rlit = 0;
			tmproom[nrooms]->xalign = ERR;
			tmproom[nrooms]->yalign = ERR;
			tmproom[nrooms]->x = 0;
			tmproom[nrooms]->y = 0;
			tmproom[nrooms]->w = 2;
			tmproom[nrooms]->h = 2;
			in_room = 1;
		  }
#line 2137 "y.tab.c"
    break;

  case 32: /* random_corridors: RAND_CORRIDOR_ID  */
#line 387 "lev_comp.y"
                  {
			tmpcor[0] = New(corridor);
			tmpcor[0]->src.room = -1;
			ncorridor = 1;
		  }
#line 2147 "y.tab.c"
    break;

  case 35: /* corridor: CORRIDOR_ID ':' corr_spec ',' corr_spec  */
#line 399 "lev_comp.y"
                  {
			tmpcor[ncorridor] = New(corridor);
			tmpcor[ncorridor]->src.room = (yyvsp[-2].corpos).room;
			tmpcor[ncorridor]->src.wall = (yyvsp[-2].corpos).wall;
			tmpcor[ncorridor]->src.door = (yyvsp[-2].corpos).door;
			tmpcor[ncorridor]->dest.room = (yyvsp[0].corpos).room;
			tmpcor[ncorridor]->dest.wall = (yyvsp[0].corpos).wall;
			tmpcor[ncorridor]->dest.door = (yyvsp[0].corpos).door;
			ncorridor++;
			if (ncorridor >= MAX_OF_TYPE) {
				yyerror("Too many corridors in level!");
				ncorridor--;
			}
		  }
#line 2166 "y.tab.c"
    break;

  case 36: /* corridor: CORRIDOR_ID ':' corr_spec ',' INTEGER  */
#line 414 "lev_comp.y"
                  {
			tmpcor[ncorridor] = New(corridor);
			tmpcor[ncorridor]->src.room = (yyvsp[-2].corpos).room;
			tmpcor[ncorridor]->src.wall = (yyvsp[-2].corpos).wall;
			tmpcor[ncorridor]->src.door = (yyvsp[-2].corpos).door;
			tmpcor[ncorridor]->dest.room = -1;
			tmpcor[ncorridor]->dest.wall = (yyvsp[0].i);
			ncorridor++;
			if (ncorridor >= MAX_OF_TYPE) {
				yyerror("Too many corridors in level!");
				ncorridor--;
			}
		  }
#line 2184 "y.tab.c"
    break;

  case 37: /* corr_spec: '(' INTEGER ',' DIRECTION ',' door_pos ')'  */
#line 430 "lev_comp.y"
                  {
			if ((unsigned) (yyvsp[-5].i) >= nrooms)
			    yyerror("Wrong room number!");
			(yyval.corpos).room = (yyvsp[-5].i);
			(yyval.corpos).wall = (yyvsp[-3].i);
			(yyval.corpos).door = (yyvsp[-1].i);
		  }
#line 2196 "y.tab.c"
    break;

  case 38: /* aroom: room_def room_details  */
#line 440 "lev_comp.y"
                  {
			store_room();
		  }
#line 2204 "y.tab.c"
    break;

  case 39: /* aroom: subroom_def room_details  */
#line 444 "lev_comp.y"
                  {
			store_room();
		  }
#line 2212 "y.tab.c"
    break;

  case 40: /* subroom_def: SUBROOM_ID ':' room_type ',' light_state ',' subroom_pos ',' room_size ',' string roomfill  */
#line 450 "lev_comp.y"
                  {
			tmproom[nrooms] = New(room);
			tmproom[nrooms]->parent = (yyvsp[-1].map);
			tmproom[nrooms]->name = (char *) 0;
			tmproom[nrooms]->rtype = (yyvsp[-9].i);
			tmproom[nrooms]->rlit = (yyvsp[-7].i);
			tmproom[nrooms]->filled = (yyvsp[0].i);
			tmproom[nrooms]->xalign = ERR;
			tmproom[nrooms]->yalign = ERR;
			tmproom[nrooms]->x = current_coord.x;
			tmproom[nrooms]->y = current_coord.y;
			tmproom[nrooms]->w = current_size.width;
			tmproom[nrooms]->h = current_size.height;
			in_room = 1;
		  }
#line 2232 "y.tab.c"
    break;

  case 41: /* room_def: ROOM_ID ':' room_type ',' light_state ',' room_pos ',' room_align ',' room_size roomfill  */
#line 468 "lev_comp.y"
                  {
			tmproom[nrooms] = New(room);
			tmproom[nrooms]->name = (char *) 0;
			tmproom[nrooms]->parent = (char *) 0;
			tmproom[nrooms]->rtype = (yyvsp[-9].i);
			tmproom[nrooms]->rlit = (yyvsp[-7].i);
			tmproom[nrooms]->filled = (yyvsp[0].i);
			tmproom[nrooms]->xalign = current_align.x;
			tmproom[nrooms]->yalign = current_align.y;
			tmproom[nrooms]->x = current_coord.x;
			tmproom[nrooms]->y = current_coord.y;
			tmproom[nrooms]->w = current_size.width;
			tmproom[nrooms]->h = current_size.height;
			in_room = 1;
		  }
#line 2252 "y.tab.c"
    break;

  case 42: /* roomfill: %empty  */
#line 486 "lev_comp.y"
                  {
			(yyval.i) = 1;
		  }
#line 2260 "y.tab.c"
    break;

  case 43: /* roomfill: ',' BOOLEAN  */
#line 490 "lev_comp.y"
                  {
			(yyval.i) = (yyvsp[0].i);
		  }
#line 2268 "y.tab.c"
    break;

  case 44: /* room_pos: '(' INTEGER ',' INTEGER ')'  */
#line 496 "lev_comp.y"
                  {
			if ( (yyvsp[-3].i) < 1 || (yyvsp[-3].i) > 5 ||
			    (yyvsp[-1].i) < 1 || (yyvsp[-1].i) > 5 ) {
			    yyerror("Room position should be between 1 & 5!");
			} else {
			    current_coord.x = (yyvsp[-3].i);
			    current_coord.y = (yyvsp[-1].i);
			}
		  }
#line 2282 "y.tab.c"
    break;

  case 45: /* room_pos: RANDOM_TYPE  */
#line 506 "lev_comp.y"
                  {
			current_coord.x = current_coord.y = ERR;
		  }
#line 2290 "y.tab.c"
    break;

  case 46: /* subroom_pos: '(' INTEGER ',' INTEGER ')'  */
#line 512 "lev_comp.y"
                  {
			if ( (yyvsp[-3].i) < 0 || (yyvsp[-1].i) < 0) {
			    yyerror("Invalid subroom position !");
			} else {
			    current_coord.x = (yyvsp[-3].i);
			    current_coord.y = (yyvsp[-1].i);
			}
		  }
#line 2303 "y.tab.c"
    break;

  case 47: /* subroom_pos: RANDOM_TYPE  */
#line 521 "lev_comp.y"
                  {
			current_coord.x = current_coord.y = ERR;
		  }
#line 2311 "y.tab.c"
    break;

  case 48: /* room_align: '(' h_justif ',' v_justif ')'  */
#line 527 "lev_comp.y"
                  {
			current_align.x = (yyvsp[-3].i);
			current_align.y = (yyvsp[-1].i);
		  }
#line 2320 "y.tab.c"
    break;

  case 49: /* room_align: RANDOM_TYPE  */
#line 532 "lev_comp.y"
                  {
			current_align.x = current_align.y = ERR;
		  }
#line 2328 "y.tab.c"
    break;

  case 50: /* room_size: '(' INTEGER ',' INTEGER ')'  */
#line 538 "lev_comp.y"
                  {
			current_size.width = (yyvsp[-3].i);
			current_size.height = (yyvsp[-1].i);
		  }
#line 2337 "y.tab.c"
    break;

  case 51: /* room_size: RANDOM_TYPE  */
#line 543 "lev_comp.y"
                  {
			current_size.height = current_size.width = ERR;
		  }
#line 2345 "y.tab.c"
    break;

  case 67: /* room_name: NAME_ID ':' string  */
#line 568 "lev_comp.y"
                  {
			if (tmproom[nrooms]->name)
			    yyerror("This room already has a name!");
			else
			    tmproom[nrooms]->name = (yyvsp[0].map);
		  }
#line 2356 "y.tab.c"
    break;

  case 68: /* room_chance: CHANCE_ID ':' INTEGER  */
#line 577 "lev_comp.y"
                   {
			if (tmproom[nrooms]->chance)
			    yyerror("This room already assigned a chance!");
			else if (tmproom[nrooms]->rtype == OROOM)
			    yyerror("Only typed rooms can have a chance!");
			else if ((yyvsp[0].i) < 1 || (yyvsp[0].i) > 99)
			    yyerror("The chance is supposed to be percentile.");
			else
			    tmproom[nrooms]->chance = (yyvsp[0].i);
		   }
#line 2371 "y.tab.c"
    break;

  case 69: /* room_door: DOOR_ID ':' secret ',' door_state ',' door_wall ',' door_pos  */
#line 590 "lev_comp.y"
                  {
			/* ERR means random here */
			if ((yyvsp[-2].i) == ERR && (yyvsp[0].i) != ERR) {
		     yyerror("If the door wall is random, so must be its pos!");
			} else {
			    tmprdoor[ndoor] = New(room_door);
			    tmprdoor[ndoor]->secret = (yyvsp[-6].i);
			    tmprdoor[ndoor]->mask = (yyvsp[-4].i);
			    tmprdoor[ndoor]->wall = (yyvsp[-2].i);
			    tmprdoor[ndoor]->pos = (yyvsp[0].i);
			    ndoor++;
			    if (ndoor >= MAX_OF_TYPE) {
				    yyerror("Too many doors in room!");
				    ndoor--;
			    }
			}
		  }
#line 2393 "y.tab.c"
    break;

  case 76: /* maze_def: MAZE_ID ':' string ',' filling  */
#line 622 "lev_comp.y"
                  {
			maze.filling = (schar) (yyvsp[0].i);
			if (index((yyvsp[-2].map), '.'))
			    yyerror("Invalid dot ('.') in level name.");
			if ((int) strlen((yyvsp[-2].map)) > 8)
			    yyerror("Level names limited to 8 characters.");
			(yyval.map) = (yyvsp[-2].map);
			in_room = 0;
			n_plist = n_mlist = n_olist = 0;
		  }
#line 2408 "y.tab.c"
    break;

  case 77: /* filling: CHAR  */
#line 635 "lev_comp.y"
                  {
			(yyval.i) = get_floor_type((char)(yyvsp[0].i));
		  }
#line 2416 "y.tab.c"
    break;

  case 78: /* filling: RANDOM_TYPE  */
#line 639 "lev_comp.y"
                  {
			(yyval.i) = -1;
		  }
#line 2424 "y.tab.c"
    break;

  case 81: /* aregion: map_definition reg_init map_details  */
#line 649 "lev_comp.y"
                  {
			store_part();
		  }
#line 2432 "y.tab.c"
    break;

  case 82: /* map_definition: NOMAP_ID  */
#line 655 "lev_comp.y"
                  {
			tmppart[npart] = New(mazepart);
			tmppart[npart]->halign = 1;
			tmppart[npart]->valign = 1;
			tmppart[npart]->nrobjects = 0;
			tmppart[npart]->nloc = 0;
			tmppart[npart]->nrmonst = 0;
			tmppart[npart]->xsize = 1;
			tmppart[npart]->ysize = 1;
			tmppart[npart]->map = (char **) alloc(sizeof(char *));
			tmppart[npart]->map[0] = (char *) alloc(1);
			tmppart[npart]->map[0][0] = STONE;
			max_x_map = COLNO-1;
			max_y_map = ROWNO;
		  }
#line 2452 "y.tab.c"
    break;

  case 83: /* map_definition: map_geometry MAP_ID  */
#line 671 "lev_comp.y"
                  {
			tmppart[npart] = New(mazepart);
			tmppart[npart]->halign = (yyvsp[-1].i) % 10;
			tmppart[npart]->valign = (yyvsp[-1].i) / 10;
			tmppart[npart]->nrobjects = 0;
			tmppart[npart]->nloc = 0;
			tmppart[npart]->nrmonst = 0;
			scan_map((yyvsp[0].map));
			Free((yyvsp[0].map));
		  }
#line 2467 "y.tab.c"
    break;

  case 84: /* map_geometry: GEOMETRY_ID ':' h_justif ',' v_justif  */
#line 684 "lev_comp.y"
                  {
			(yyval.i) = (yyvsp[-2].i) + ((yyvsp[0].i) * 10);
		  }
#line 2475 "y.tab.c"
    break;

  case 91: /* init_reg: RANDOM_OBJECTS_ID ':' object_list  */
#line 702 "lev_comp.y"
                  {
			if (tmppart[npart]->nrobjects) {
			    yyerror("Object registers already initialized!");
			} else {
			    tmppart[npart]->robjects = (char *)alloc(n_olist);
			    (void) memcpy((genericptr_t)tmppart[npart]->robjects,
					  (genericptr_t)olist, n_olist);
			    tmppart[npart]->nrobjects = n_olist;
			}
		  }
#line 2490 "y.tab.c"
    break;

  case 92: /* init_reg: RANDOM_PLACES_ID ':' place_list  */
#line 713 "lev_comp.y"
                  {
			if (tmppart[npart]->nloc) {
			    yyerror("Location registers already initialized!");
			} else {
			    register int i;
			    tmppart[npart]->rloc_x = (char *) alloc(n_plist);
			    tmppart[npart]->rloc_y = (char *) alloc(n_plist);
			    for(i=0;i<n_plist;i++) {
				tmppart[npart]->rloc_x[i] = plist[i].x;
				tmppart[npart]->rloc_y[i] = plist[i].y;
			    }
			    tmppart[npart]->nloc = n_plist;
			}
		  }
#line 2509 "y.tab.c"
    break;

  case 93: /* init_reg: RANDOM_MONSTERS_ID ':' monster_list  */
#line 728 "lev_comp.y"
                  {
			if (tmppart[npart]->nrmonst) {
			    yyerror("Monster registers already initialized!");
			} else {
			    tmppart[npart]->rmonst = (char *) alloc(n_mlist);
			    (void) memcpy((genericptr_t)tmppart[npart]->rmonst,
					  (genericptr_t)mlist, n_mlist);
			    tmppart[npart]->nrmonst = n_mlist;
			}
		  }
#line 2524 "y.tab.c"
    break;

  case 94: /* object_list: object  */
#line 741 "lev_comp.y"
                  {
			if (n_olist < MAX_REGISTERS)
			    olist[n_olist++] = (yyvsp[0].i);
			else
			    yyerror("Object list too long!");
		  }
#line 2535 "y.tab.c"
    break;

  case 95: /* object_list: object ',' object_list  */
#line 748 "lev_comp.y"
                  {
			if (n_olist < MAX_REGISTERS)
			    olist[n_olist++] = (yyvsp[-2].i);
			else
			    yyerror("Object list too long!");
		  }
#line 2546 "y.tab.c"
    break;

  case 96: /* monster_list: monster  */
#line 757 "lev_comp.y"
                  {
			if (n_mlist < MAX_REGISTERS)
			    mlist[n_mlist++] = (yyvsp[0].i);
			else
			    yyerror("Monster list too long!");
		  }
#line 2557 "y.tab.c"
    break;

  case 97: /* monster_list: monster ',' monster_list  */
#line 764 "lev_comp.y"
                  {
			if (n_mlist < MAX_REGISTERS)
			    mlist[n_mlist++] = (yyvsp[-2].i);
			else
			    yyerror("Monster list too long!");
		  }
#line 2568 "y.tab.c"
    break;

  case 98: /* place_list: place  */
#line 773 "lev_comp.y"
                  {
			if (n_plist < MAX_REGISTERS)
			    plist[n_plist++] = current_coord;
			else
			    yyerror("Location list too long!");
		  }
#line 2579 "y.tab.c"
    break;

  case 99: /* $@1: %empty  */
#line 780 "lev_comp.y"
                  {
			if (n_plist < MAX_REGISTERS)
			    plist[n_plist++] = current_coord;
			else
			    yyerror("Location list too long!");
		  }
#line 2590 "y.tab.c"
    break;

  case 123: /* $@2: %empty  */
#line 816 "lev_comp.y"
                  {
			tmpmonst[nmons] = New(monster);
			tmpmonst[nmons]->x = current_coord.x;
			tmpmonst[nmons]->y = current_coord.y;
			tmpmonst[nmons]->class = (yyvsp[-4].i);
			tmpmonst[nmons]->peaceful = -1; /* no override */
			tmpmonst[nmons]->asleep = -1;
			tmpmonst[nmons]->align = - MAX_REGISTERS - 2;
			tmpmonst[nmons]->name.str = 0;
			tmpmonst[nmons]->appear = 0;
			tmpmonst[nmons]->appear_as.str = 0;
			tmpmonst[nmons]->chance = (yyvsp[-6].i);
			tmpmonst[nmons]->id = NON_PM;
			if (!in_room)
			    check_coord(current_coord.x, current_coord.y,
					"Monster");
			if ((yyvsp[-2].map)) {
			    int token = get_monster_id((yyvsp[-2].map), (char) (yyvsp[-4].i));
			    if (token == ERR)
				yywarning(
			      "Invalid monster name!  Making random monster.");
			    else
				tmpmonst[nmons]->id = token;
			    Free((yyvsp[-2].map));
			}
		  }
#line 2621 "y.tab.c"
    break;

  case 124: /* monster_detail: MONSTER_ID chance ':' monster_c ',' m_name ',' coordinate $@2 monster_infos  */
#line 843 "lev_comp.y"
                  {
			if (++nmons >= MAX_OF_TYPE) {
			    yyerror("Too many monsters in room or mazepart!");
			    nmons--;
			}
		  }
#line 2632 "y.tab.c"
    break;

  case 127: /* monster_info: ',' string  */
#line 856 "lev_comp.y"
                  {
			tmpmonst[nmons]->name.str = (yyvsp[0].map);
		  }
#line 2640 "y.tab.c"
    break;

  case 128: /* monster_info: ',' MON_ATTITUDE  */
#line 860 "lev_comp.y"
                  {
			tmpmonst[nmons]->peaceful = (yyvsp[0].i);
		  }
#line 2648 "y.tab.c"
    break;

  case 129: /* monster_info: ',' MON_ALERTNESS  */
#line 864 "lev_comp.y"
                  {
			tmpmonst[nmons]->asleep = (yyvsp[0].i);
		  }
#line 2656 "y.tab.c"
    break;

  case 130: /* monster_info: ',' alignment  */
#line 868 "lev_comp.y"
                  {
			tmpmonst[nmons]->align = (yyvsp[0].i);
		  }
#line 2664 "y.tab.c"
    break;

  case 131: /* monster_info: ',' MON_APPEARANCE string  */
#line 872 "lev_comp.y"
                  {
			tmpmonst[nmons]->appear = (yyvsp[-1].i);
			tmpmonst[nmons]->appear_as.str = (yyvsp[0].map);
		  }
#line 2673 "y.tab.c"
    break;

  case 132: /* object_detail: OBJECT_ID object_desc  */
#line 879 "lev_comp.y"
                  {
		  }
#line 2680 "y.tab.c"
    break;

  case 133: /* object_detail: COBJECT_ID object_desc  */
#line 882 "lev_comp.y"
                  {
			/* 1: is contents of preceeding object with 2 */
			/* 2: is a container */
			/* 0: neither */
			tmpobj[nobj-1]->containment = 2;
		  }
#line 2691 "y.tab.c"
    break;

  case 134: /* $@3: %empty  */
#line 891 "lev_comp.y"
                  {
			tmpobj[nobj] = New(object);
			tmpobj[nobj]->class = (yyvsp[-2].i);
			tmpobj[nobj]->corpsenm = NON_PM;
			tmpobj[nobj]->curse_state = -1;
			tmpobj[nobj]->name.str = 0;
			tmpobj[nobj]->chance = (yyvsp[-4].i);
			tmpobj[nobj]->id = -1;
			if ((yyvsp[0].map)) {
			    int token = get_object_id((yyvsp[0].map), (yyvsp[-2].i));
			    if (token == ERR)
				yywarning(
				"Illegal object name!  Making random object.");
			     else
				tmpobj[nobj]->id = token;
			    Free((yyvsp[0].map));
			}
		  }
#line 2714 "y.tab.c"
    break;

  case 135: /* object_desc: chance ':' object_c ',' o_name $@3 ',' object_where object_infos  */
#line 910 "lev_comp.y"
                  {
			if (++nobj >= MAX_OF_TYPE) {
			    yyerror("Too many objects in room or mazepart!");
			    nobj--;
			}
		  }
#line 2725 "y.tab.c"
    break;

  case 136: /* object_where: coordinate  */
#line 919 "lev_comp.y"
                  {
			tmpobj[nobj]->containment = 0;
			tmpobj[nobj]->x = current_coord.x;
			tmpobj[nobj]->y = current_coord.y;
			if (!in_room)
			    check_coord(current_coord.x, current_coord.y,
					"Object");
		  }
#line 2738 "y.tab.c"
    break;

  case 137: /* object_where: CONTAINED  */
#line 928 "lev_comp.y"
                  {
			tmpobj[nobj]->containment = 1;
			/* random coordinate, will be overridden anyway */
			tmpobj[nobj]->x = -MAX_REGISTERS-1;
			tmpobj[nobj]->y = -MAX_REGISTERS-1;
		  }
#line 2749 "y.tab.c"
    break;

  case 138: /* object_infos: %empty  */
#line 937 "lev_comp.y"
                  {
			tmpobj[nobj]->spe = -127;
	/* Note below: we're trying to make as many of these optional as
	 * possible.  We clearly can't make curse_state, enchantment, and
	 * monster_id _all_ optional, since ",random" would be ambiguous.
	 * We can't even just make enchantment mandatory, since if we do that
	 * alone, ",random" requires too much lookahead to parse.
	 */
		  }
#line 2763 "y.tab.c"
    break;

  case 139: /* object_infos: ',' curse_state ',' monster_id ',' enchantment optional_name  */
#line 947 "lev_comp.y"
                  {
		  }
#line 2770 "y.tab.c"
    break;

  case 140: /* object_infos: ',' curse_state ',' enchantment optional_name  */
#line 950 "lev_comp.y"
                  {
		  }
#line 2777 "y.tab.c"
    break;

  case 141: /* object_infos: ',' monster_id ',' enchantment optional_name  */
#line 953 "lev_comp.y"
                  {
		  }
#line 2784 "y.tab.c"
    break;

  case 142: /* curse_state: RANDOM_TYPE  */
#line 958 "lev_comp.y"
                  {
			tmpobj[nobj]->curse_state = -1;
		  }
#line 2792 "y.tab.c"
    break;

  case 143: /* curse_state: CURSE_TYPE  */
#line 962 "lev_comp.y"
                  {
			tmpobj[nobj]->curse_state = (yyvsp[0].i);
		  }
#line 2800 "y.tab.c"
    break;

  case 144: /* monster_id: STRING  */
#line 968 "lev_comp.y"
                  {
			int token = get_monster_id((yyvsp[0].map), (char)0);
			if (token == ERR)	/* "random" */
			    tmpobj[nobj]->corpsenm = NON_PM - 1;
			else
			    tmpobj[nobj]->corpsenm = token;
			Free((yyvsp[0].map));
		  }
#line 2813 "y.tab.c"
    break;

  case 145: /* enchantment: RANDOM_TYPE  */
#line 979 "lev_comp.y"
                  {
			tmpobj[nobj]->spe = -127;
		  }
#line 2821 "y.tab.c"
    break;

  case 146: /* enchantment: INTEGER  */
#line 983 "lev_comp.y"
                  {
			tmpobj[nobj]->spe = (yyvsp[0].i);
		  }
#line 2829 "y.tab.c"
    break;

  case 148: /* optional_name: ',' NONE  */
#line 990 "lev_comp.y"
                  {
		  }
#line 2836 "y.tab.c"
    break;

  case 149: /* optional_name: ',' STRING  */
#line 993 "lev_comp.y"
                  {
			tmpobj[nobj]->name.str = (yyvsp[0].map);
		  }
#line 2844 "y.tab.c"
    break;

  case 150: /* door_detail: DOOR_ID ':' door_state ',' coordinate  */
#line 999 "lev_comp.y"
                  {
			tmpdoor[ndoor] = New(door);
			tmpdoor[ndoor]->x = current_coord.x;
			tmpdoor[ndoor]->y = current_coord.y;
			tmpdoor[ndoor]->mask = (yyvsp[-2].i);
			if(current_coord.x >= 0 && current_coord.y >= 0 &&
			   tmpmap[current_coord.y][current_coord.x] != DOOR &&
			   tmpmap[current_coord.y][current_coord.x] != SDOOR)
			    yyerror("Door decl doesn't match the map");
			ndoor++;
			if (ndoor >= MAX_OF_TYPE) {
				yyerror("Too many doors in mazepart!");
				ndoor--;
			}
		  }
#line 2864 "y.tab.c"
    break;

  case 151: /* trap_detail: TRAP_ID chance ':' trap_name ',' coordinate  */
#line 1017 "lev_comp.y"
                  {
			tmptrap[ntrap] = New(trap);
			tmptrap[ntrap]->x = current_coord.x;
			tmptrap[ntrap]->y = current_coord.y;
			tmptrap[ntrap]->type = (yyvsp[-2].i);
			tmptrap[ntrap]->chance = (yyvsp[-4].i);
			if (!in_room)
			    check_coord(current_coord.x, current_coord.y,
					"Trap");
			if (++ntrap >= MAX_OF_TYPE) {
				yyerror("Too many traps in room or mazepart!");
				ntrap--;
			}
		  }
#line 2883 "y.tab.c"
    break;

  case 152: /* drawbridge_detail: DRAWBRIDGE_ID ':' coordinate ',' DIRECTION ',' door_state  */
#line 1034 "lev_comp.y"
                   {
		        int x, y, dir;

			tmpdb[ndb] = New(drawbridge);
			x = tmpdb[ndb]->x = current_coord.x;
			y = tmpdb[ndb]->y = current_coord.y;
			/* convert dir from a DIRECTION to a DB_DIR */
			dir = (yyvsp[-2].i);
			switch(dir) {
			case W_NORTH: dir = DB_NORTH; y--; break;
			case W_SOUTH: dir = DB_SOUTH; y++; break;
			case W_EAST:  dir = DB_EAST;  x++; break;
			case W_WEST:  dir = DB_WEST;  x--; break;
			default:
			    yyerror("Invalid drawbridge direction");
			    break;
			}
			tmpdb[ndb]->dir = dir;
			if (current_coord.x >= 0 && current_coord.y >= 0 &&
			    !IS_WALL(tmpmap[y][x])) {
			    char ebuf[60];
			    Sprintf(ebuf,
				    "Wall needed for drawbridge (%02d, %02d)",
				    current_coord.x, current_coord.y);
			    yyerror(ebuf);
			}

			if ( (yyvsp[0].i) == D_ISOPEN )
			    tmpdb[ndb]->db_open = 1;
			else if ( (yyvsp[0].i) == D_CLOSED )
			    tmpdb[ndb]->db_open = 0;
			else
			    yyerror("A drawbridge can only be open or closed!");
			ndb++;
			if (ndb >= MAX_OF_TYPE) {
				yyerror("Too many drawbridges in mazepart!");
				ndb--;
			}
		   }
#line 2927 "y.tab.c"
    break;

  case 153: /* mazewalk_detail: MAZEWALK_ID ':' coordinate ',' DIRECTION  */
#line 1076 "lev_comp.y"
                  {
			tmpwalk[nwalk] = New(walk);
			tmpwalk[nwalk]->x = current_coord.x;
			tmpwalk[nwalk]->y = current_coord.y;
			tmpwalk[nwalk]->dir = (yyvsp[0].i);
			nwalk++;
			if (nwalk >= MAX_OF_TYPE) {
				yyerror("Too many mazewalks in mazepart!");
				nwalk--;
			}
		  }
#line 2943 "y.tab.c"
    break;

  case 154: /* wallify_detail: WALLIFY_ID  */
#line 1090 "lev_comp.y"
                  {
			wallify_map();
		  }
#line 2951 "y.tab.c"
    break;

  case 155: /* ladder_detail: LADDER_ID ':' coordinate ',' UP_OR_DOWN  */
#line 1096 "lev_comp.y"
                  {
			tmplad[nlad] = New(lad);
			tmplad[nlad]->x = current_coord.x;
			tmplad[nlad]->y = current_coord.y;
			tmplad[nlad]->up = (yyvsp[0].i);
			if (!in_room)
			    check_coord(current_coord.x, current_coord.y,
					"Ladder");
			nlad++;
			if (nlad >= MAX_OF_TYPE) {
				yyerror("Too many ladders in mazepart!");
				nlad--;
			}
		  }
#line 2970 "y.tab.c"
    break;

  case 156: /* stair_detail: STAIR_ID ':' coordinate ',' UP_OR_DOWN  */
#line 1113 "lev_comp.y"
                  {
			tmpstair[nstair] = New(stair);
			tmpstair[nstair]->x = current_coord.x;
			tmpstair[nstair]->y = current_coord.y;
			tmpstair[nstair]->up = (yyvsp[0].i);
			if (!in_room)
			    check_coord(current_coord.x, current_coord.y,
					"Stairway");
			nstair++;
			if (nstair >= MAX_OF_TYPE) {
				yyerror("Too many stairs in room or mazepart!");
				nstair--;
			}
		  }
#line 2989 "y.tab.c"
    break;

  case 157: /* $@4: %empty  */
#line 1130 "lev_comp.y"
                  {
			tmplreg[nlreg] = New(lev_region);
			tmplreg[nlreg]->in_islev = (yyvsp[0].i);
			tmplreg[nlreg]->inarea.x1 = current_region.x1;
			tmplreg[nlreg]->inarea.y1 = current_region.y1;
			tmplreg[nlreg]->inarea.x2 = current_region.x2;
			tmplreg[nlreg]->inarea.y2 = current_region.y2;
		  }
#line 3002 "y.tab.c"
    break;

  case 158: /* stair_region: STAIR_ID ':' lev_region $@4 ',' lev_region ',' UP_OR_DOWN  */
#line 1139 "lev_comp.y"
                  {
			tmplreg[nlreg]->del_islev = (yyvsp[-2].i);
			tmplreg[nlreg]->delarea.x1 = current_region.x1;
			tmplreg[nlreg]->delarea.y1 = current_region.y1;
			tmplreg[nlreg]->delarea.x2 = current_region.x2;
			tmplreg[nlreg]->delarea.y2 = current_region.y2;
			if((yyvsp[0].i))
			    tmplreg[nlreg]->rtype = LR_UPSTAIR;
			else
			    tmplreg[nlreg]->rtype = LR_DOWNSTAIR;
			tmplreg[nlreg]->rname.str = 0;
			nlreg++;
			if (nlreg >= MAX_OF_TYPE) {
				yyerror("Too many levregions in mazepart!");
				nlreg--;
			}
		  }
#line 3024 "y.tab.c"
    break;

  case 159: /* $@5: %empty  */
#line 1159 "lev_comp.y"
                  {
			tmplreg[nlreg] = New(lev_region);
			tmplreg[nlreg]->in_islev = (yyvsp[0].i);
			tmplreg[nlreg]->inarea.x1 = current_region.x1;
			tmplreg[nlreg]->inarea.y1 = current_region.y1;
			tmplreg[nlreg]->inarea.x2 = current_region.x2;
			tmplreg[nlreg]->inarea.y2 = current_region.y2;
		  }
#line 3037 "y.tab.c"
    break;

  case 160: /* portal_region: PORTAL_ID ':' lev_region $@5 ',' lev_region ',' string  */
#line 1168 "lev_comp.y"
                  {
			tmplreg[nlreg]->del_islev = (yyvsp[-2].i);
			tmplreg[nlreg]->delarea.x1 = current_region.x1;
			tmplreg[nlreg]->delarea.y1 = current_region.y1;
			tmplreg[nlreg]->delarea.x2 = current_region.x2;
			tmplreg[nlreg]->delarea.y2 = current_region.y2;
			tmplreg[nlreg]->rtype = LR_PORTAL;
			tmplreg[nlreg]->rname.str = (yyvsp[0].map);
			nlreg++;
			if (nlreg >= MAX_OF_TYPE) {
				yyerror("Too many levregions in mazepart!");
				nlreg--;
			}
		  }
#line 3056 "y.tab.c"
    break;

  case 161: /* $@6: %empty  */
#line 1185 "lev_comp.y"
                  {
			tmplreg[nlreg] = New(lev_region);
			tmplreg[nlreg]->in_islev = (yyvsp[0].i);
			tmplreg[nlreg]->inarea.x1 = current_region.x1;
			tmplreg[nlreg]->inarea.y1 = current_region.y1;
			tmplreg[nlreg]->inarea.x2 = current_region.x2;
			tmplreg[nlreg]->inarea.y2 = current_region.y2;
		  }
#line 3069 "y.tab.c"
    break;

  case 162: /* $@7: %empty  */
#line 1194 "lev_comp.y"
                  {
			tmplreg[nlreg]->del_islev = (yyvsp[0].i);
			tmplreg[nlreg]->delarea.x1 = current_region.x1;
			tmplreg[nlreg]->delarea.y1 = current_region.y1;
			tmplreg[nlreg]->delarea.x2 = current_region.x2;
			tmplreg[nlreg]->delarea.y2 = current_region.y2;
		  }
#line 3081 "y.tab.c"
    break;

  case 163: /* teleprt_region: TELEPRT_ID ':' lev_region $@6 ',' lev_region $@7 teleprt_detail  */
#line 1202 "lev_comp.y"
                  {
			switch((yyvsp[0].i)) {
			case -1: tmplreg[nlreg]->rtype = LR_TELE; break;
			case 0: tmplreg[nlreg]->rtype = LR_DOWNTELE; break;
			case 1: tmplreg[nlreg]->rtype = LR_UPTELE; break;
			}
			tmplreg[nlreg]->rname.str = 0;
			nlreg++;
			if (nlreg >= MAX_OF_TYPE) {
				yyerror("Too many levregions in mazepart!");
				nlreg--;
			}
		  }
#line 3099 "y.tab.c"
    break;

  case 164: /* $@8: %empty  */
#line 1218 "lev_comp.y"
                  {
			tmplreg[nlreg] = New(lev_region);
			tmplreg[nlreg]->in_islev = (yyvsp[0].i);
			tmplreg[nlreg]->inarea.x1 = current_region.x1;
			tmplreg[nlreg]->inarea.y1 = current_region.y1;
			tmplreg[nlreg]->inarea.x2 = current_region.x2;
			tmplreg[nlreg]->inarea.y2 = current_region.y2;
		  }
#line 3112 "y.tab.c"
    break;

  case 165: /* branch_region: BRANCH_ID ':' lev_region $@8 ',' lev_region  */
#line 1227 "lev_comp.y"
                  {
			tmplreg[nlreg]->del_islev = (yyvsp[0].i);
			tmplreg[nlreg]->delarea.x1 = current_region.x1;
			tmplreg[nlreg]->delarea.y1 = current_region.y1;
			tmplreg[nlreg]->delarea.x2 = current_region.x2;
			tmplreg[nlreg]->delarea.y2 = current_region.y2;
			tmplreg[nlreg]->rtype = LR_BRANCH;
			tmplreg[nlreg]->rname.str = 0;
			nlreg++;
			if (nlreg >= MAX_OF_TYPE) {
				yyerror("Too many levregions in mazepart!");
				nlreg--;
			}
		  }
#line 3131 "y.tab.c"
    break;

  case 166: /* teleprt_detail: %empty  */
#line 1244 "lev_comp.y"
                  {
			(yyval.i) = -1;
		  }
#line 3139 "y.tab.c"
    break;

  case 167: /* teleprt_detail: ',' UP_OR_DOWN  */
#line 1248 "lev_comp.y"
                  {
			(yyval.i) = (yyvsp[0].i);
		  }
#line 3147 "y.tab.c"
    break;

  case 168: /* lev_region: region  */
#line 1254 "lev_comp.y"
                  {
			(yyval.i) = 0;
		  }
#line 3155 "y.tab.c"
    break;

  case 169: /* lev_region: LEV '(' INTEGER ',' INTEGER ',' INTEGER ',' INTEGER ')'  */
#line 1258 "lev_comp.y"
                  {
/* This series of if statements is a hack for MSC 5.1.  It seems that its
   tiny little brain cannot compile if these are all one big if statement. */
			if ((yyvsp[-7].i) <= 0 || (yyvsp[-7].i) >= COLNO)
				yyerror("Region out of level range!");
			else if ((yyvsp[-5].i) < 0 || (yyvsp[-5].i) >= ROWNO)
				yyerror("Region out of level range!");
			else if ((yyvsp[-3].i) <= 0 || (yyvsp[-3].i) >= COLNO)
				yyerror("Region out of level range!");
			else if ((yyvsp[-1].i) < 0 || (yyvsp[-1].i) >= ROWNO)
				yyerror("Region out of level range!");
			current_region.x1 = (yyvsp[-7].i);
			current_region.y1 = (yyvsp[-5].i);
			current_region.x2 = (yyvsp[-3].i);
			current_region.y2 = (yyvsp[-1].i);
			(yyval.i) = 1;
		  }
#line 3177 "y.tab.c"
    break;

  case 170: /* fountain_detail: FOUNTAIN_ID ':' coordinate  */
#line 1278 "lev_comp.y"
                  {
			tmpfountain[nfountain] = New(fountain);
			tmpfountain[nfountain]->x = current_coord.x;
			tmpfountain[nfountain]->y = current_coord.y;
			if (!in_room)
			    check_coord(current_coord.x, current_coord.y,
					"Fountain");
			nfountain++;
			if (nfountain >= MAX_OF_TYPE) {
			    yyerror("Too many fountains in room or mazepart!");
			    nfountain--;
			}
		  }
#line 3195 "y.tab.c"
    break;

  case 171: /* sink_detail: SINK_ID ':' coordinate  */
#line 1294 "lev_comp.y"
                  {
			tmpsink[nsink] = New(sink);
			tmpsink[nsink]->x = current_coord.x;
			tmpsink[nsink]->y = current_coord.y;
			nsink++;
			if (nsink >= MAX_OF_TYPE) {
				yyerror("Too many sinks in room!");
				nsink--;
			}
		  }
#line 3210 "y.tab.c"
    break;

  case 172: /* pool_detail: POOL_ID ':' coordinate  */
#line 1307 "lev_comp.y"
                  {
			tmppool[npool] = New(pool);
			tmppool[npool]->x = current_coord.x;
			tmppool[npool]->y = current_coord.y;
			npool++;
			if (npool >= MAX_OF_TYPE) {
				yyerror("Too many pools in room!");
				npool--;
			}
		  }
#line 3225 "y.tab.c"
    break;

  case 173: /* diggable_detail: NON_DIGGABLE_ID ':' region  */
#line 1320 "lev_comp.y"
                  {
			tmpdig[ndig] = New(digpos);
			tmpdig[ndig]->x1 = current_region.x1;
			tmpdig[ndig]->y1 = current_region.y1;
			tmpdig[ndig]->x2 = current_region.x2;
			tmpdig[ndig]->y2 = current_region.y2;
			ndig++;
			if (ndig >= MAX_OF_TYPE) {
				yyerror("Too many diggables in mazepart!");
				ndig--;
			}
		  }
#line 3242 "y.tab.c"
    break;

  case 174: /* passwall_detail: NON_PASSWALL_ID ':' region  */
#line 1335 "lev_comp.y"
                  {
			tmppass[npass] = New(digpos);
			tmppass[npass]->x1 = current_region.x1;
			tmppass[npass]->y1 = current_region.y1;
			tmppass[npass]->x2 = current_region.x2;
			tmppass[npass]->y2 = current_region.y2;
			npass++;
			if (npass >= 32) {
				yyerror("Too many passwalls in mazepart!");
				npass--;
			}
		  }
#line 3259 "y.tab.c"
    break;

  case 175: /* region_detail: REGION_ID ':' region ',' light_state ',' room_type prefilled  */
#line 1350 "lev_comp.y"
                  {
			tmpreg[nreg] = New(region);
			tmpreg[nreg]->x1 = current_region.x1;
			tmpreg[nreg]->y1 = current_region.y1;
			tmpreg[nreg]->x2 = current_region.x2;
			tmpreg[nreg]->y2 = current_region.y2;
			tmpreg[nreg]->rlit = (yyvsp[-3].i);
			tmpreg[nreg]->rtype = (yyvsp[-1].i);
			if((yyvsp[0].i) & 1) tmpreg[nreg]->rtype += MAXRTYPE+1;
			tmpreg[nreg]->rirreg = (((yyvsp[0].i) & 2) != 0);
			if(current_region.x1 > current_region.x2 ||
			   current_region.y1 > current_region.y2)
			   yyerror("Region start > end!");
			if(tmpreg[nreg]->rtype == VAULT &&
			   (tmpreg[nreg]->rirreg ||
			    (tmpreg[nreg]->x2 - tmpreg[nreg]->x1 != 1) ||
			    (tmpreg[nreg]->y2 - tmpreg[nreg]->y1 != 1)))
				yyerror("Vaults must be exactly 2x2!");
			if(want_warnings && !tmpreg[nreg]->rirreg &&
			   current_region.x1 > 0 && current_region.y1 > 0 &&
			   current_region.x2 < (int)max_x_map &&
			   current_region.y2 < (int)max_y_map) {
			    /* check for walls in the room */
			    char ebuf[60];
			    register int x, y, nrock = 0;

			    for(y=current_region.y1; y<=current_region.y2; y++)
				for(x=current_region.x1;
				    x<=current_region.x2; x++)
				    if(IS_ROCK(tmpmap[y][x]) ||
				       IS_DOOR(tmpmap[y][x])) nrock++;
			    if(nrock) {
				Sprintf(ebuf,
					"Rock in room (%02d,%02d,%02d,%02d)?!",
					current_region.x1, current_region.y1,
					current_region.x2, current_region.y2);
				yywarning(ebuf);
			    }
			    if (
		!IS_ROCK(tmpmap[current_region.y1-1][current_region.x1-1]) ||
		!IS_ROCK(tmpmap[current_region.y2+1][current_region.x1-1]) ||
		!IS_ROCK(tmpmap[current_region.y1-1][current_region.x2+1]) ||
		!IS_ROCK(tmpmap[current_region.y2+1][current_region.x2+1])) {
				Sprintf(ebuf,
				"NonRock edge in room (%02d,%02d,%02d,%02d)?!",
					current_region.x1, current_region.y1,
					current_region.x2, current_region.y2);
				yywarning(ebuf);
			    }
			} else if(tmpreg[nreg]->rirreg &&
		!IS_ROOM(tmpmap[current_region.y1][current_region.x1])) {
			    char ebuf[60];
			    Sprintf(ebuf,
				    "Rock in irregular room (%02d,%02d)?!",
				    current_region.x1, current_region.y1);
			    yyerror(ebuf);
			}
			nreg++;
			if (nreg >= MAX_OF_TYPE) {
				yyerror("Too many regions in mazepart!");
				nreg--;
			}
		  }
#line 3327 "y.tab.c"
    break;

  case 176: /* altar_detail: ALTAR_ID ':' coordinate ',' alignment ',' altar_type  */
#line 1416 "lev_comp.y"
                  {
			tmpaltar[naltar] = New(altar);
			tmpaltar[naltar]->x = current_coord.x;
			tmpaltar[naltar]->y = current_coord.y;
			tmpaltar[naltar]->align = (yyvsp[-2].i);
			tmpaltar[naltar]->shrine = (yyvsp[0].i);
			if (!in_room)
			    check_coord(current_coord.x, current_coord.y,
					"Altar");
			naltar++;
			if (naltar >= MAX_OF_TYPE) {
				yyerror("Too many altars in room or mazepart!");
				naltar--;
			}
		  }
#line 3347 "y.tab.c"
    break;

  case 177: /* gold_detail: GOLD_ID ':' amount ',' coordinate  */
#line 1434 "lev_comp.y"
                  {
			tmpgold[ngold] = New(gold);
			tmpgold[ngold]->x = current_coord.x;
			tmpgold[ngold]->y = current_coord.y;
			tmpgold[ngold]->amount = (yyvsp[-2].i);
			if (!in_room)
			    check_coord(current_coord.x, current_coord.y,
					"Gold");
			ngold++;
			if (ngold >= MAX_OF_TYPE) {
				yyerror("Too many golds in room or mazepart!");
				ngold--;
			}
		  }
#line 3366 "y.tab.c"
    break;

  case 178: /* engraving_detail: ENGRAVING_ID ':' coordinate ',' engraving_type ',' string  */
#line 1451 "lev_comp.y"
                  {
			tmpengraving[nengraving] = New(engraving);
			tmpengraving[nengraving]->x = current_coord.x;
			tmpengraving[nengraving]->y = current_coord.y;
			tmpengraving[nengraving]->engr.str = (yyvsp[0].map);
			tmpengraving[nengraving]->etype = (yyvsp[-2].i);
			if (!in_room)
			    check_coord(current_coord.x, current_coord.y,
					"Engraving");
			nengraving++;
			if (nengraving >= MAX_OF_TYPE) {
			    yyerror("Too many engravings in room or mazepart!");
			    nengraving--;
			}
		  }
#line 3386 "y.tab.c"
    break;

  case 180: /* monster_c: RANDOM_TYPE  */
#line 1470 "lev_comp.y"
                  {
			(yyval.i) = - MAX_REGISTERS - 1;
		  }
#line 3394 "y.tab.c"
    break;

  case 183: /* object_c: RANDOM_TYPE  */
#line 1478 "lev_comp.y"
                  {
			(yyval.i) = - MAX_REGISTERS - 1;
		  }
#line 3402 "y.tab.c"
    break;

  case 186: /* m_name: RANDOM_TYPE  */
#line 1486 "lev_comp.y"
                  {
			(yyval.map) = (char *) 0;
		  }
#line 3410 "y.tab.c"
    break;

  case 188: /* o_name: RANDOM_TYPE  */
#line 1493 "lev_comp.y"
                  {
			(yyval.map) = (char *) 0;
		  }
#line 3418 "y.tab.c"
    break;

  case 189: /* trap_name: string  */
#line 1499 "lev_comp.y"
                  {
			int token = get_trap_type((yyvsp[0].map));
			if (token == ERR)
				yyerror("Unknown trap type!");
			(yyval.i) = token;
			Free((yyvsp[0].map));
		  }
#line 3430 "y.tab.c"
    break;

  case 191: /* room_type: string  */
#line 1510 "lev_comp.y"
                  {
			int token = get_room_type((yyvsp[0].map));
			if (token == ERR) {
				yywarning("Unknown room type!  Making ordinary room...");
				(yyval.i) = OROOM;
			} else
				(yyval.i) = token;
			Free((yyvsp[0].map));
		  }
#line 3444 "y.tab.c"
    break;

  case 193: /* prefilled: %empty  */
#line 1523 "lev_comp.y"
                  {
			(yyval.i) = 0;
		  }
#line 3452 "y.tab.c"
    break;

  case 194: /* prefilled: ',' FILLING  */
#line 1527 "lev_comp.y"
                  {
			(yyval.i) = (yyvsp[0].i);
		  }
#line 3460 "y.tab.c"
    break;

  case 195: /* prefilled: ',' FILLING ',' BOOLEAN  */
#line 1531 "lev_comp.y"
                  {
			(yyval.i) = (yyvsp[-2].i) + ((yyvsp[0].i) << 1);
		  }
#line 3468 "y.tab.c"
    break;

  case 198: /* coordinate: RANDOM_TYPE  */
#line 1539 "lev_comp.y"
                  {
			current_coord.x = current_coord.y = -MAX_REGISTERS-1;
		  }
#line 3476 "y.tab.c"
    break;

  case 205: /* alignment: RANDOM_TYPE  */
#line 1555 "lev_comp.y"
                  {
			(yyval.i) = - MAX_REGISTERS - 1;
		  }
#line 3484 "y.tab.c"
    break;

  case 208: /* p_register: P_REGISTER '[' INTEGER ']'  */
#line 1565 "lev_comp.y"
                  {
			if ( (yyvsp[-1].i) >= MAX_REGISTERS )
				yyerror("Register Index overflow!");
			else
				current_coord.x = current_coord.y = - (yyvsp[-1].i) - 1;
		  }
#line 3495 "y.tab.c"
    break;

  case 209: /* o_register: O_REGISTER '[' INTEGER ']'  */
#line 1574 "lev_comp.y"
                  {
			if ( (yyvsp[-1].i) >= MAX_REGISTERS )
				yyerror("Register Index overflow!");
			else
				(yyval.i) = - (yyvsp[-1].i) - 1;
		  }
#line 3506 "y.tab.c"
    break;

  case 210: /* m_register: M_REGISTER '[' INTEGER ']'  */
#line 1583 "lev_comp.y"
                  {
			if ( (yyvsp[-1].i) >= MAX_REGISTERS )
				yyerror("Register Index overflow!");
			else
				(yyval.i) = - (yyvsp[-1].i) - 1;
		  }
#line 3517 "y.tab.c"
    break;

  case 211: /* a_register: A_REGISTER '[' INTEGER ']'  */
#line 1592 "lev_comp.y"
                  {
			if ( (yyvsp[-1].i) >= 3 )
				yyerror("Register Index overflow!");
			else
				(yyval.i) = - (yyvsp[-1].i) - 1;
		  }
#line 3528 "y.tab.c"
    break;

  case 213: /* monster: CHAR  */
#line 1604 "lev_comp.y"
                  {
			if (check_monster_char((char) (yyvsp[0].i)))
				(yyval.i) = (yyvsp[0].i) ;
			else {
				yyerror("Unknown monster class!");
				(yyval.i) = ERR;
			}
		  }
#line 3541 "y.tab.c"
    break;

  case 214: /* object: CHAR  */
#line 1615 "lev_comp.y"
                  {
			char c = (yyvsp[0].i);
			if (check_object_char(c))
				(yyval.i) = c;
			else {
				yyerror("Unknown char class!");
				(yyval.i) = ERR;
			}
		  }
#line 3555 "y.tab.c"
    break;

  case 218: /* chance: %empty  */
#line 1634 "lev_comp.y"
                  {
			(yyval.i) = 100;	/* default is 100% */
		  }
#line 3563 "y.tab.c"
    break;

  case 219: /* chance: PERCENT  */
#line 1638 "lev_comp.y"
                  {
			if ((yyvsp[0].i) <= 0 || (yyvsp[0].i) > 100)
			    yyerror("Expected percentile chance.");
			(yyval.i) = (yyvsp[0].i);
		  }
#line 3573 "y.tab.c"
    break;

  case 222: /* coord: '(' INTEGER ',' INTEGER ')'  */
#line 1650 "lev_comp.y"
                  {
			if (!in_room && !init_lev.init_present &&
			    ((yyvsp[-3].i) < 0 || (yyvsp[-3].i) > (int)max_x_map ||
			     (yyvsp[-1].i) < 0 || (yyvsp[-1].i) > (int)max_y_map))
			    yyerror("Coordinates out of map range!");
			current_coord.x = (yyvsp[-3].i);
			current_coord.y = (yyvsp[-1].i);
		  }
#line 3586 "y.tab.c"
    break;

  case 223: /* region: '(' INTEGER ',' INTEGER ',' INTEGER ',' INTEGER ')'  */
#line 1661 "lev_comp.y"
                  {
/* This series of if statements is a hack for MSC 5.1.  It seems that its
   tiny little brain cannot compile if these are all one big if statement. */
			if ((yyvsp[-7].i) < 0 || (yyvsp[-7].i) > (int)max_x_map)
				yyerror("Region out of map range!");
			else if ((yyvsp[-5].i) < 0 || (yyvsp[-5].i) > (int)max_y_map)
				yyerror("Region out of map range!");
			else if ((yyvsp[-3].i) < 0 || (yyvsp[-3].i) > (int)max_x_map)
				yyerror("Region out of map range!");
			else if ((yyvsp[-1].i) < 0 || (yyvsp[-1].i) > (int)max_y_map)
				yyerror("Region out of map range!");
			current_region.x1 = (yyvsp[-7].i);
			current_region.y1 = (yyvsp[-5].i);
			current_region.x2 = (yyvsp[-3].i);
			current_region.y2 = (yyvsp[-1].i);
		  }
#line 3607 "y.tab.c"
    break;


#line 3611 "y.tab.c"

      default: break;
    }
  /* User semantic actions sometimes alter yychar, and that requires
     that yytoken be updated with the new translation.  We take the
     approach of translating immediately before every use of yytoken.
     One alternative is translating here after every semantic action,
     but that translation would be missed if the semantic action invokes
     YYABORT, YYACCEPT, or YYERROR immediately after altering yychar or
     if it invokes YYBACKUP.  In the case of YYABORT or YYACCEPT, an
     incorrect destructor might then be invoked immediately.  In the
     case of YYERROR or YYBACKUP, subsequent parser actions might lead
     to an incorrect destructor call or verbose syntax error message
     before the lookahead is translated.  */
  YY_SYMBOL_PRINT ("-> $$ =", YY_CAST (yysymbol_kind_t, yyr1[yyn]), &yyval, &yyloc);

  YYPOPSTACK (yylen);
  yylen = 0;

  *++yyvsp = yyval;

  /* Now 'shift' the result of the reduction.  Determine what state
     that goes to, based on the state we popped back to and the rule
     number reduced by.  */
  {
    const int yylhs = yyr1[yyn] - YYNTOKENS;
    const int yyi = yypgoto[yylhs] + *yyssp;
    yystate = (0 <= yyi && yyi <= YYLAST && yycheck[yyi] == *yyssp
               ? yytable[yyi]
               : yydefgoto[yylhs]);
  }

  goto yynewstate;


/*--------------------------------------.
| yyerrlab -- here on detecting error.  |
`--------------------------------------*/
yyerrlab:
  /* Make sure we have latest lookahead translation.  See comments at
     user semantic actions for why this is necessary.  */
  yytoken = yychar == YYEMPTY ? YYSYMBOL_YYEMPTY : YYTRANSLATE (yychar);
  /* If not already recovering from an error, report this error.  */
  if (!yyerrstatus)
    {
      ++yynerrs;
      yyerror (YY_("syntax error"));
    }

  if (yyerrstatus == 3)
    {
      /* If just tried and failed to reuse lookahead token after an
         error, discard it.  */

      if (yychar <= YYEOF)
        {
          /* Return failure if at end of input.  */
          if (yychar == YYEOF)
            YYABORT;
        }
      else
        {
          yydestruct ("Error: discarding",
                      yytoken, &yylval);
          yychar = YYEMPTY;
        }
    }

  /* Else will try to reuse lookahead token after shifting the error
     token.  */
  goto yyerrlab1;


/*---------------------------------------------------.
| yyerrorlab -- error raised explicitly by YYERROR.  |
`---------------------------------------------------*/
yyerrorlab:
  /* Pacify compilers when the user code never invokes YYERROR and the
     label yyerrorlab therefore never appears in user code.  */
  if (0)
    YYERROR;
  ++yynerrs;

  /* Do not reclaim the symbols of the rule whose action triggered
     this YYERROR.  */
  YYPOPSTACK (yylen);
  yylen = 0;
  YY_STACK_PRINT (yyss, yyssp);
  yystate = *yyssp;
  goto yyerrlab1;


/*-------------------------------------------------------------.
| yyerrlab1 -- common code for both syntax error and YYERROR.  |
`-------------------------------------------------------------*/
yyerrlab1:
  yyerrstatus = 3;      /* Each real token shifted decrements this.  */

  /* Pop stack until we find a state that shifts the error token.  */
  for (;;)
    {
      yyn = yypact[yystate];
      if (!yypact_value_is_default (yyn))
        {
          yyn += YYSYMBOL_YYerror;
          if (0 <= yyn && yyn <= YYLAST && yycheck[yyn] == YYSYMBOL_YYerror)
            {
              yyn = yytable[yyn];
              if (0 < yyn)
                break;
            }
        }

      /* Pop the current state because it cannot handle the error token.  */
      if (yyssp == yyss)
        YYABORT;


      yydestruct ("Error: popping",
                  YY_ACCESSING_SYMBOL (yystate), yyvsp);
      YYPOPSTACK (1);
      yystate = *yyssp;
      YY_STACK_PRINT (yyss, yyssp);
    }

  YY_IGNORE_MAYBE_UNINITIALIZED_BEGIN
  *++yyvsp = yylval;
  YY_IGNORE_MAYBE_UNINITIALIZED_END


  /* Shift the error token.  */
  YY_SYMBOL_PRINT ("Shifting", YY_ACCESSING_SYMBOL (yyn), yyvsp, yylsp);

  yystate = yyn;
  goto yynewstate;


/*-------------------------------------.
| yyacceptlab -- YYACCEPT comes here.  |
`-------------------------------------*/
yyacceptlab:
  yyresult = 0;
  goto yyreturnlab;


/*-----------------------------------.
| yyabortlab -- YYABORT comes here.  |
`-----------------------------------*/
yyabortlab:
  yyresult = 1;
  goto yyreturnlab;


/*-----------------------------------------------------------.
| yyexhaustedlab -- YYNOMEM (memory exhaustion) comes here.  |
`-----------------------------------------------------------*/
yyexhaustedlab:
  yyerror (YY_("memory exhausted"));
  yyresult = 2;
  goto yyreturnlab;


/*----------------------------------------------------------.
| yyreturnlab -- parsing is finished, clean up and return.  |
`----------------------------------------------------------*/
yyreturnlab:
  if (yychar != YYEMPTY)
    {
      /* Make sure we have latest lookahead translation.  See comments at
         user semantic actions for why this is necessary.  */
      yytoken = YYTRANSLATE (yychar);
      yydestruct ("Cleanup: discarding lookahead",
                  yytoken, &yylval);
    }
  /* Do not reclaim the symbols of the rule whose action triggered
     this YYABORT or YYACCEPT.  */
  YYPOPSTACK (yylen);
  YY_STACK_PRINT (yyss, yyssp);
  while (yyssp != yyss)
    {
      yydestruct ("Cleanup: popping",
                  YY_ACCESSING_SYMBOL (+*yyssp), yyvsp);
      YYPOPSTACK (1);
    }
#ifndef yyoverflow
  if (yyss != yyssa)
    YYSTACK_FREE (yyss);
#endif

  return yyresult;
}

#line 1679 "lev_comp.y"


/*lev_comp.y*/
