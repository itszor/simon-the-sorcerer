/* Simon the Sorcerer (Adventure Soft, 1993; the Archimedes version by
 * James Callin and Rob Wyatt for GamesWare, 1994): what libroger needs to
 * know about the game.
 *
 * !Run: Set Simon$Dir <Obey$Dir> ; IconSprites ; WimpSlot 64K ; Run
 * Execute.Banner (a title picture) ; RMRun Execute.DDT -ac (Desktop
 * Tracker, on RISC OS 3.0/3.1; PlayModR on a Risc PC) ; RMRun
 * Execute.!RunImage, the front end: an icon bar icon whose click does
 * *Run <Simon$Dir>.execute.!Runner <Simon$Dir>.execute.gamebase 0, which
 * game.c does directly. !Runner is the game: the engine in ARM code, with
 * Acorn's C library linked in.
 *
 * The files are as the floppies have them, the nine discs merged
 * (../tools/images.py): with no <Simon$Dir>.00.0000 (the hard disc
 * installer's marker) the game reads the rooms from ADFS::0.$.!Simon,
 * still compressed, asking for each disc in turn. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <roger.h>

extern const struct roger_image recomp_image;      /* gen/simon/entries.c */
#include "gen/modules.inc"                         /* Desktop Tracker */

static const char *const prefixes[] = {"<Obey$Dir>.", "ADFS::0.$.", NULL};
static const char *const variables[] = {"Simon$Dir", "!Simon", NULL};
static const char *const loaders[] = {"../game/!Simon/Execute/Banner,ff8", NULL};

/* Code built at run time on the C library's stack (above the image and its
 * zero-initialised data): _kernel_swi's SWI instruction */
static const uint32_t interpreted[] = {0x44CD4, 0x8000 + 640 * 1024, 0, 0};

static void game_init(void)
{
    roger_cli("IconSprites <Simon$Dir>.!Sprites");
}

static struct roger_config config = {
    .title = "Simon the Sorcerer (recompiled)",
    .image_path = "../game/!Simon/Execute/!Runner,ff8",
    .image = &recomp_image,
    .modules = modules,
    .loader_programs = loaders,
    .appdir = "../game",
    .dir_prefixes = prefixes,
    .variables = variables,
    .command_line = "<Simon$Dir>.execute.!Runner <Simon$Dir>.execute.gamebase 0",
    .initial_mode = 12,                 /* a desktop mode: the game sets its own */
    .wimpslot = 640 * 1024,             /* the front end checks for 640K */
    /* headless runs: an ARM3's speed. The script waits for syncs its
     * animations (run from a ticker event) send; at libroger's default 2
     * MIPS the script falls behind, misses them and sits out each wait's
     * 20 second timeout (the intro's goblin scene). Interactive runs are
     * unthrottled */
    .headless_mips = 16,
    .interpreted = interpreted,
    .init = game_init,
};

int main(int argc, char **argv) { roger_main(argc, argv, &config); }
