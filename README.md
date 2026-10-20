Simon the Sorcerer (Adventure Soft, 1993; Archimedes version GamesWare, 1994) - static recompilation
====================================================================================================

A recipe: this repository holds no game data. It rebuilds the game as a
native executable from your own copy of the floppies, recognised by content
(recipe.json), so it can be shared without distributing the game.

    ./build.sh "Simon The Sorcerer (1994)(Gamesware)(Disk 01 of 10).adf" ... \
               "Simon The Sorcerer (1994)(Gamesware)(Disk 09 of 10).adf"
    cd recomp && ./simon

build.sh runs recipe.json's steps with SuperSpider's tools/weave.py
(~/stuff/superspider, or $SUPERSPIDER; $SS below): it finds the nine discs
among the inputs, extracts them, merges them into one !Simon, unpacks the
program, analyses and translates the machine code and links it with
libroger (~/stuff/libroger, or make ROGER=...). Needs python3, OCaml/dune,
gcc and SDL3.

Inputs: the TOSEC set's disc images (ADFS E format, 800K; the dumps stop
short of the last track, which ADFSlib pads). Discs 1 to 9 are the game;
disc 10 is an updater (!Update, December 1994) whose !Runner is older than
the one disc 1 already has (April 1995) and whose disc 6 files disc 6
already has, so it isn't used. The CD (1995) is a different build - a
demo of the talkie version, on the Shared C Library, with STSMusic - and
isn't covered.

What it makes:

    extracted/disc01-09      $SS/tools/adf_extract.py's output, via weave.py
    game/!Simon              the nine discs' !Simon merged (each holds different
                             rooms), libroger's appdir; Execute.!Runner unpacked
    analysis/*.json          SuperSpider's analyses (the program, Desktop Tracker)
    recomp/gen/              their C translations
    recomp/simon             the game

Committed: recipe.json, build.sh, tools/ (images.py, unpack.c), analysis/*.roots,
recomp/ (Makefile, game.c, simon.ini), this file.

Playing
-------

The copy protection comes first, as on the original: "Click on compass
point where <symbol> appears on page N". Each page of the manual has a
compass with a symbol at each of its eight points; click that point of the
compass on the screen. Three right answers are needed (a wrong one gives
one more chance). You need the manual.

Then the mouse, as the manual describes: a verb, then an object. The right
button skips the intro (from the goblins' clearing on). M and S turn the
music and sound effects off and on; F1-F3 the text speed (the manual's
keys). Saving and loading (the postcard) haven't been tried yet: the game
asks for a floppy to save on and writes ADFS::0.$.!Simon.Saved, which
libroger redirects to recomp/savedata/.

How the game is put together
----------------------------

!Run: Set Simon$Dir; Run Execute.Banner (a title picture); RMRun
Execute.DDT -ac (Desktop Tracker 1.11, the music player, on RISC OS 3.0/3.1;
PlayModR, Desktop Tracker 1.12, on a Risc PC); RMRun Execute.!RunImage, the
front end: an icon bar icon that runs Execute.!Runner Execute.GameBase 0.
game.c does the last directly (command line as the front end's).

- Execute.!Runner (tools/images.py: simon) is squeezed: a decoder stub that
  copies itself above the image, decodes it downwards to &8000 and branches
  there. tools/unpack runs it under libroger's interpreter and keeps the
  image (an AIF: &3B9B4 bytes of code, &1320 of data). The engine is ARM
  code converted from the PC's (a script interpreter with a 63-entry
  opcode table at &F97C, its animation in a ticker event and a transient
  callback), linked with Acorn's C library (ANSILib 3.10, static: no
  Shared C Library) and C routines of the port's (text, tables, files).
- Execute.DDT (ddt) is translated at &1840000. It drives the sound
  hardware itself: device 9 (the sound DMA interrupt), MEMC's Sstart/SendN
  and VIDC's sound frequency and stereo registers, the OS's sound page at
  &1F00000 (found with OS_ReadMemMapEntries), the kernel's centisecond
  counter in zero page and IOC timer 0's latch for its clock. Its mixer
  runs in USR mode with interrupts on, using r13/r14 as working registers
  (saved with stm ^), and gets back to SVC mode through a branch it puts
  in the undefined instruction vector (&4). It patches its mixers' output
  stores for the tune's channel count (str r0,[r12],#8 becomes #4 for a
  4-channel tune, as Simon's are): libroger interprets those words as
  they now are.
- Files: there is no <Simon$Dir>.00.0000 (the hard disc installer's
  marker), so the game reads ADFS::0.$.!Simon - the floppies - with the
  rooms still compressed, as the installer would have unpacked them. All
  nine discs' files are in game/!Simon, so the disc it asks for is always
  there.

Not done, and differences
-------------------------

- DDT's -a option (!Run gives -ac): it times the machine by pointing the
  ARM's IRQ vector (&18) at its own code and waiting for interrupts there,
  and then picks its clock from what it measured. libroger doesn't deliver
  interrupts through a program's own &18 vector, so DDT is loaded without
  options and keeps its default clock (tools/images.py MODULE_ARGS).
- Headless runs (--limit) run the CPU at 16 MIPS (game.c headless_mips),
  an ARM3's speed, not libroger's default 2: the game's script waits for
  syncs that its animations (run from a ticker event) send, and at 2 MIPS
  (or an ARM2's 4.5) it falls behind, misses them and sits out each wait's
  20 second timeout - the intro's goblin scene showed no text and crawled.
  Interactive runs are unthrottled. Scale --limit to match: 16M
  instructions a second of the game.
- Headless, a scripted click is taken or ignored depending on when it
  lands (at 8 MIPS a click at 22s answers the protection, at 25s it
  doesn't). At 16 MIPS the answers used in testing (clicks at 20, 26 and
  30 seconds) are taken. Not looked into further; interactive clicks work.
- Roots: the program's (analysis/simon.roots) are calls through a table of
  script handlers ORed with a mode word, and returns into its callers from
  interpreted code; DDT's (analysis/ddt.roots) are where its trap through
  the undefined instruction vector returns to (&1842DF4, the branch it
  puts at &4) and the code that follows on from there. Its
  mixers no longer need roots (SuperSpider finds them, below): with the
  two the first tune uses as roots and the other thirteen untranslated,
  the next tune (Tunes.8tune, outside the blacksmith's) branched to an
  untranslated mixer inside the sound interrupt, which libroger ends, so
  the DMA buffer was never refilled and played the same 10ms over and
  over - a monotone buzz from the fourth screen on.

What it needed
--------------

SuperSpider (src/s1.ml, src/arm2.ml, src/gen.ml):
- the C library linked into the image (ANSILib): _kernel_init's block
  found at the start-up's branch (language descriptions: Init and the
  other procedures), APCS function entries as candidates, and stack checks
  (cmp sp,sl ; bllt __rt_stkovf_split) as calls that return; code built on
  the stack (_kernel_swi's SWI instruction, mov pc,sp) returning to the
  caller as an APCS function
- an ORR of a table entry with constants that only touch PSR bits; a null
  first table slot (opcode 0 handled before the jump); -1 as an unset
  pointer (SIG_ERR in the signal table)
- an unconditional instruction from the undefined space as a trap that
  carries on after it, when code runs into it
- LDM/STM ^ without the PC: the user bank (gen: LDM_RU, user_reg)
- a table of branches after add pc,pc,rX,lsl #2 with rX unknown (DDT's
  mixers: rX the mask of the active channels, 1-15, built with orrne's
  the analysis widens away; slot 0, never used, isn't an instruction)
- runs of identical blocks of up to 16 words entered backwards (sub
  pc,sp,r0,lsl #3 into DDT's mixer loops: ten-word blocks, a sample from
  each of two channels), not only up to 4
- a guarded computed jump's index (cmp rX,#n ; addls pc,pc,rX,lsl #2)
  bounded by the guard whatever else is known of it, a field loaded from
  memory too (this also finds more of Elite's and Star Fighter 3000's
  cases)

libroger:
- OS_ChangeEnvironment 0 and 14 (MemoryLimit, ApplicationSpace) read the
  end of the application slot until set (the C library's heap)
- transient callbacks also when an interrupt returns to USR mode
- the interpreter: LDM/STM ^ (user bank), the undefined instruction space
  (op 011, bit 4), a program's branch at &4 for undefined instructions
- OS_UpdateMEMC and MEMC's control register (bit 11 starts and stops the
  sound DMA); VIDC1's sound frequency and stereo image registers for a
  program driving the DMA; OS_ReadMemMapEntries
- IOC timer 0's latch command and count, and the centisecond counter at
  &A38 (RISC OS 3's zero page)
- module parameters in R10 at initialisation (roger_module.args, *RMLoad's)
- self-modified code in modules too (Desktop Tracker's mixer strides:
  without them the mixers wrote 8 bytes a frame into 4-byte frames, so
  only the first half of each 5ms mix was in the DMA buffer, spread over
  all of it, and the rest went past its end - a 200Hz buzz over broken
  notes); the DMA buffer interrupt when the buffer ends
- ROGER_INTERPRET=1: interpret everything (debugging a translation)

Regression: the other games' headless runs (30M instructions) are
byte-identical with libroger before and after; their make regen output is
unchanged except where an stm has ^ (Saloon Cars' stmfd sp!,{lr}^, one of
Zool's: now user_reg(), the same in USR mode); those two runs are identical
too. phase3/eval_s1b.py's scores are unchanged.
