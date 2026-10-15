# PSB Switch Port Kit

A conversion toolkit that turns the Windows fan game **Pokémon Survivor Burst**
(freely distributed on itch.io) into a Nintendo Switch homebrew build using the
[rgss-switch](https://github.com/randygil/rgss-switch) engine — for **personal use**.

[한국어 문서](README.ko.md)

> **This repository contains no game.** Not a single byte of game files, derived
> images, or binaries is distributed here. Users download their own copy from
> itch.io and convert it locally on their machine. This kit only ships conversion
> scripts, a runtime shim, and automated tests.

## Disclaimer

- Unofficial, personal-use conversion tools. Not affiliated with or endorsed by
  Nintendo / GAME FREAK inc. / The Pokémon Company / Capcom or the game's author.
  Provided as-is, with no warranty.
- No Nintendo SDK or proprietary assets are used (engine is built on the
  open-source devkitPro/libnx toolchain).
- The game remains the property of its respective rights holders.
  Redistribution of converted output is prohibited.

## Requirements

- Python 3.10+ (`rubymarshal`, `evbunpack`, `pillow`) — for unpacking and icon generation
- Ruby 3.x — required by the verification gate (`sudo apt-get install ruby-full`)
- rgss-switch v0.1.0 release — extract to `./rgss-switch-0.1.0/` (GPLv2+, see NOTICE.md for the link)
- The Windows release of the game — download from itch.io, unpack with Enigma Virtual Box into `./game/`

## Usage

### Setup (once)

```bash
# Python tooling (unpack + icon generation)
python3 -m venv venv
venv/bin/pip install rubymarshal evbunpack pillow

# Ruby for the verification gate (the build aborts without it)
sudo apt-get install ruby-full        # Debian/Ubuntu
```

### Conversion

```bash
# 1. Get the game: download the PSB release from itch.io (free, with your own account)

# 2. Unpack (Enigma Virtual Box extraction) -> ./game/
venv/bin/evbunpack "GameExecutable.exe" game

# 3. Install the shim: fixes the trainer-name screen (physical-keyboard-only on
#    PC) and centers 4:3 menus on the wide canvas
mkdir -p game/lib && cp lib/nx-psb-fixes.rb game/lib/

# 4. (Optional) Wide 683x384 canvas — default is the original 512x384
venv/bin/python widescreen_patch.py game/Data/Scripts.rxdata 683

# 5. Convert (pre-build verification runs automatically: full .rb syntax check
#    + shim behavioral tests; the build aborts on any failure)
venv/bin/python pack_psb.py
#    Output: out/switch/pokemon-survivor-burst/
```

### Installing on the Switch

```
Copy the out/switch/pokemon-survivor-burst/ folder to
/switch/ (or /homebrew/) on your SD card
-> Hold R over a game (or hbmenu) to launch in title-takeover mode
   (Album applet mode will run out of memory)
A one-time plugin recompile (a few seconds) may run on first boot — normal.
```

### Trainer-name input controls (converted build)

| Button | Action |
|---|---|
| **A / B** | Next step — opens the on-screen keyboard if the name is empty, confirms if entered |
| **X / Y** | Delete one character |
| **L / R** | Reopen the on-screen keyboard (if closed by mistake) |
| Inside the keyboard | Touch typing is supported |

## Runtime shim (`lib/nx-psb-fixes.rb`)

Patches applied as **preload scripts**, so they always run regardless of plugin
recompilation on the device:

| Problem | Fix |
|---|---|
| Name entry assumes a physical keyboard — a dead end on console | A/B = next step (empty name → reopen OSK, entered name → confirm), X/Y = backspace, L/R = reopen keyboard |
| Splash images hug the left edge | Centered |
| Load screen (continue/new game) hugs the left edge | Viewport shifted to center |

Ground truth for buttons (mkxp-z `keybindings.cpp` + SDL layout): East(A)=`Input::B`,
South(B)=`Input::C`, North(X)=`Input::X`, West(Y)=`Input::A`, L/R=`Input::L/R`.
There is no `Input::START`. Touch is not exposed to scripts (it only works inside
the system on-screen keyboard).

## Verification gate

`pack_psb.py` runs, before every build: (1) `ruby -c` syntax checks on every `.rb`
under `lib/` and `Plugins/`, and (2) RGSS-stub behavioral tests
(`tests/nx_shims_test.rb`). Any failure aborts the build.
**Nothing reaches the device without verification** — that is this kit's core rule.

## License

**GPLv2+** (`LICENSE`). rgss-switch (including the `Empaquetar.ps1` packer this kit
ports to Python) is GPLv2+, so this derivative is published under the same terms.
See `NOTICE.md` for credits.
