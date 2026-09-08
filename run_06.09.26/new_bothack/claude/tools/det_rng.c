/* Pin NetHack's RNG seed so that a whole game is reproducible.
 *
 * The nethack.alt.org patchset seeds from time() + /dev/urandom at start-up
 * *and* re-seeds every 10-710 rn2() calls (src/rnd.c, check_reseed).  A game
 * is therefore not reproducible even with a fixed start seed, which makes a
 * byte-for-byte comparison of two bots playing "the same game" impossible.
 *
 * This shim is LD_PRELOADed around an unmodified NetHack binary: the first
 * srandom() seeds from $NETHACK_FIXED_SEED, every later one is ignored, so the
 * game runs one normal, uninterrupted RNG stream that is identical from run to
 * run.  This is not wizard mode - nothing about the rules, the binary or the
 * bot changes, only where the entropy comes from.
 *
 *   gcc -shared -fPIC -o det_rng.so tools/det_rng.c -ldl
 *   NETHACK_FIXED_SEED=42 LD_PRELOAD=/path/det_rng.so nethack ...
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdlib.h>

static int seeded = 0;

void srandom(unsigned int ignored)
{
    (void) ignored;
    if (!seeded) {
        const char *s = getenv("NETHACK_FIXED_SEED");
        unsigned int seed = s ? (unsigned int) strtoul(s, 0, 10) : 1;
        void (*real)(unsigned int);
        seeded = 1;
        real = (void (*)(unsigned int)) dlsym(RTLD_NEXT, "srandom");
        if (real) real(seed);
    }
}

void srand(unsigned int ignored) { srandom(ignored); }
