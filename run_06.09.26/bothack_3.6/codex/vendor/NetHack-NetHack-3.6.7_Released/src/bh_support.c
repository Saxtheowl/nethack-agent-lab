/* Local experimental assistance and engine evidence, never goal completion. */
int bh_enabled(const char *key) {
    const char *s = getenv(key);
    return s && !strcmp(s, "1");
}
void bh_event(const char *event, int value) {
    const char *path = getenv("BH_EVENTS");
    FILE *f;
    if (!path || !(f = fopen(path, "a"))) return;
    fprintf(f, "{\"event\":\"%s\",\"value\":%d,\"turn\":%ld,\"dnum\":%d,\"dlevel\":%d,\"x\":%d,\"y\":%d,\"hp\":%d,\"hunger\":%d,\"minetown\":%d,\"amulet\":%d,\"invoked\":%d,\"quest_complete\":%d,\"xp_level\":%d,\"alignment_record\":%d}\n", event, value, moves, u.uz.dnum, u.uz.dlevel, u.ux, u.uy, u.uhp, u.uhunger, (Is_special(&u.uz) && !strncmp(Is_special(&u.uz)->proto, "minetn", 6)), (int) u.uhave.amulet, (int) u.uevent.invoked, (int) u.uevent.qcompleted, u.ulevel, u.ualign.record);
    fclose(f);
}
void bh_kit(void) {
    static const char *kit[] = {
        "blessed +3 gray dragon scale mail", "blessed +3 shield of reflection",
        "blessed +3 speed boots", "blessed +3 gauntlets of power",
        "blessed +3 dwarvish iron helm", "blessed +3 cloak of protection",
        "blessed +5 long sword", "blessed bag of holding",
        "blessed unicorn horn", "blessed skeleton key", "blessed pick-axe",
        "blessed ring of levitation", "blessed ring of free action",
        "blessed wand of death (0:8)", "blessed wand of digging (0:20)",
        "blessed wand of teleportation (0:20)", "blessed wand of fire (0:12)",
        "6 blessed scrolls of remove curse", "6 blessed scrolls of identify",
        "4 blessed potions of full healing", "7 uncursed wax candles", 0
    };
    int i;
    struct obj *o;
    char buf[BUFSZ];
    if (!bh_enabled("BH_KIT")) return;
    for (i=0; kit[i]; i++) {
        Strcpy(buf, kit[i]);
        o = readobjnam(buf, (struct obj *) 0);
        if (o && o != &zeroobj) {
            o->known=o->dknown=o->bknown=o->rknown=1;
            discover_object(o->otyp, TRUE, FALSE);
            addinv(o);
            bh_event("kit_item", i);
        }
    }
}

/* Prepared regression scenes. Never enabled by the campaign launcher. */
void bh_fixture(void) {
    const char *scene = getenv("BH_FIXTURE");
    struct obj *o;
    int x, y;
    d_level target;
    if (!scene || !*scene) return;
    bh_event("fixture", 1);
    if (!strcmp(scene, "hunger")) {
        u.uhunger = 5;
    } else if (!strcmp(scene, "death")) {
        done(DIED);
    } else if (!strcmp(scene, "invocation")) {
        target = sanctum_level;
        target.dlevel--;
        wizard = TRUE;
        goto_level(&target, FALSE, FALSE, FALSE);
        o = mksobj(BELL_OF_OPENING, TRUE, FALSE);
        o->cursed = 0; o->spe = 3; addinv(o);
        o = mksobj(CANDELABRUM_OF_INVOCATION, TRUE, FALSE);
        o->cursed = 0; o->spe = 7; o->age = 500L; addinv(o);
        o = mksobj(SPE_BOOK_OF_THE_DEAD, TRUE, FALSE);
        o->cursed = 0; addinv(o);
        u_on_newpos(inv_pos.x, inv_pos.y);
        vision_recalc(0);
        docrt();
        pline("You feel a strange vibration under your feet.");
        bh_event("fixture_ready", 2);
    } else if (!strcmp(scene, "astral-offer")) {
        o = mksobj(AMULET_OF_YENDOR, TRUE, FALSE);
        o->known = o->dknown = o->bknown = 1;
        addinv(o);
        target = astral_level;
        wizard = TRUE; /* explicitly prepared test, excluded from full runs */
        goto_level(&target, FALSE, FALSE, FALSE);
        for (x = 1; x < COLNO; x++) for (y = 0; y < ROWNO; y++) {
            if (IS_ALTAR(levl[x][y].typ)
                && Amask2align(levl[x][y].altarmask & AM_MASK) == u.ualign.type) {
                /* Fixture position; the test still has to issue #offer. */
                u_on_newpos(x, y);
                vision_recalc(0);
                docrt();
                bh_event("fixture_ready", 1);
                return;
            }
        }
        panic("fixture could not find coaligned altar");
    } else {
        panic("unknown BH_FIXTURE");
    }
}
