#!/usr/bin/env python3
"""The translated images of Simon the Sorcerer and the steps that build them.

    images.py assemble  the nine discs (extracted/disc01..disc09, from
                        SuperSpider's weave.py: recipe.json) -> game/!Simon,
                        libroger's appdir: the discs' !Simon directories
                        merged (each holds different rooms; where two have
                        the same file, disc 1's), as the game finds them on
                        the floppies; Execute.!Runner unpacked (tools/unpack)
    images.py analyse   SuperSpider (superspider analyse --full) on every image:
                        analysis/<name>.json; analysis/<name>.roots, if there,
                        adds entry points
    images.py roots LOG...
                        merges the gap entries of --trace-gaps runs (libroger's
                        untranslated.log) into analysis/<name>.roots
    images.py gen       superspider gen for every image -> recomp/gen/<name>/,
                        plus recomp/gen/modules.inc (game.c's module list)

Images (game/!Simon):
  simon      Execute.!Runner: the game, an AIF image at &8000, squeezed
             (unpacked by running its own unpacker). Its engine is ARM code
             (converted from the PC's), with Acorn's C library linked in
             (ANSILib: no Shared C Library).
  ddt        Execute.DDT: Desktop Tracker 1.11, the music player !Run
             RMRuns on RISC OS 3.0 and 3.1 (PlayModR, Desktop Tracker 1.12,
             is the Risc PC's), translated at a fixed RMA address.
Not translated: Execute.!RunImage (the front end, a module: an icon bar
icon whose click runs !Runner; game.c runs it directly), Execute.Banner
(a title picture !Run shows first: interpreted, a loader program).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
GAME = os.path.join(TOP, 'game')
SS = os.environ.get('SUPERSPIDER', os.path.expanduser('~/stuff/superspider'))
SSBIN = os.path.join(SS, '_build/default/bin/main.exe')

DISCS = ['disc%02d' % k for k in range(1, 10)]
RUNNER = '!Simon/Execute/!Runner,ff8'
RMA_SLOTS = 0x1840000
MODULE_ARGS = {}                                        # (see game.c: !Run gives DDT -ac)

# (name, path relative to game/, base, is module, analyse options)
IMAGES = [
    ('simon', RUNNER, 0x8000, False, ['--with', 'clib']),
    ('ddt', '!Simon/Execute/DDT,ffa', RMA_SLOTS, True, []),
]


def find(top, path):
    """a file or directory by its RISC OS path, ignoring ,load-exec suffixes and case"""
    for part in path.split('/'):
        top = os.path.join(top, next(f for f in os.listdir(top)
                                     if f.split(',')[0].lower() == part.lower()))
    return top


def typed(name):
    """an extracted file's name with its filetype as ,xxx (its ,load-exec suffix
    is a filetype stamp: the exec word is the date, different on each copy)"""
    base, _, suffix = name.partition(',')
    load = int(suffix.split('-')[0], 16)
    assert load >> 20 == 0xFFF, name
    return '%s,%03x' % (base, (load >> 8) & 0xFFF)


def assemble():
    """game/!Simon from the nine discs' !Simon directories"""
    shutil.rmtree(GAME, ignore_errors=True)
    for disc in reversed(DISCS):                        # disc 1's copies last: they win
        src = find(os.path.join(TOP, 'extracted', disc), '!Simon')
        for d, _, fs in os.walk(src):
            rel = os.path.relpath(d, src)
            out = os.path.normpath(os.path.join(GAME, '!Simon', rel))
            os.makedirs(out, exist_ok=True)
            for f in fs:
                shutil.copyfile(os.path.join(d, f), os.path.join(out, typed(f)))
    os.makedirs(os.path.join(GAME, '!Simon', 'Saved'), exist_ok=True)
    # the squeezed program, unpacked by its own code (it ends with a branch
    # to &8000); the AIF header gives the image's extent
    run(['make', '-s', '-C', HERE, 'unpack'])
    packed = os.path.join(GAME, RUNNER)
    raw = os.path.join(GAME, RUNNER + '.unpacked')
    run([os.path.join(HERE, 'unpack'), packed, '--headless', '--limit=50000000',
         '--stop=8000', '--dump=8000:80000', '--write=' + raw])
    import struct
    img = open(raw, 'rb').read()
    ro, rw = struct.unpack_from('<II', img, 0x14)
    assert img[:8] == b'\0\0\0\xfb' * 2 and struct.unpack_from('<I', img, 0x28)[0] == 0x8000
    open(packed, 'wb').write(img[:ro + rw])
    os.remove(raw)


def run(cmd):
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def analyse():
    subprocess.run(['dune', 'build'], cwd=SS, check=True)
    an = os.path.join(TOP, 'analysis')
    for name, path, base, module, opts in IMAGES:
        cmd = [SSBIN, 'analyse', os.path.join(GAME, path), '%x' % base, '--full',
               '-o', os.path.join(an, name + '.json')] + opts
        rf = os.path.join(an, name + '.roots')
        if os.path.exists(rf):
            cmd += ['--roots', rf]
        if module:
            cmd += ['--module']
        run(cmd)


def roots(logs):
    for name, path, base, _, _ in IMAGES:
        run([sys.executable, os.path.join(SS, 'tools/gap_roots.py'), os.path.join(GAME, path), '%x' % base,
             os.path.join(TOP, 'analysis', name + '.roots')] + logs)


def gen():
    rc = os.path.join(TOP, 'recomp')
    for k, (name, path, base, module, _) in enumerate(IMAGES):
        extra = [] if not module else ['--prefix', 'M%d' % k, '--tabprefix', 'recomp_' + name,
                                       '--covtag', chr(ord('a') + k)]
        run([SSBIN, 'gen', os.path.join(GAME, path), '%x' % base, os.path.join(TOP, 'analysis', name + '.json'),
             '--c', os.path.join(rc, 'gen', name)] + extra)
    with open(os.path.join(rc, 'gen', 'modules.inc'), 'w') as f:
        f.write('/* generated by ../tools/images.py - the modules, for game.c */\n')
        for name, _, _, module, _ in IMAGES:
            if module:
                f.write('extern const struct roger_image recomp_%s_image;\n' % name)
        f.write('static const struct roger_module modules[] = {\n')
        for name, path, _, module, _ in IMAGES:
            if module:
                f.write('    {"../game/%s", &recomp_%s_image, 0, "%s"},\n' % (path, name, MODULE_ARGS.get(name, '')))
        f.write('    {NULL, NULL, 0, NULL}};\n')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == 'roots':
        roots(sys.argv[2:])
    else:
        for step in sys.argv[1:]:
            {'assemble': assemble, 'analyse': analyse, 'gen': gen}[step]()
