"""dvara's vim keys, as data. The modes, counts, sequences, which-key strip,
help (?) and palette (Space Space) are Vyom's (vyom/keys.py, vyom/modal.py;
Vyom ADR 0008); this file is only what dvara adds. Space groups follow
Vayu's shared letters (y copy, d delete, o open outside, r refresh); b (the
dock bar) and x (an app's own actions) are dvara's.

An action "verb:arg" runs Plugin.v_<verb>(count, arg) in dvara/__init__.py,
or Vyom's own (activate, insert, moved...).
"""
from vyom.keys import Bind

B = Bind

GROUPS = {" b": "dock", " x": "app action"}

INSERT = [
    ("Enter", "Open the selected app (switches to it when it's already running)"),
    ("Ctrl+Enter", "Open a new window of the selected app"),
    ("Shift+Enter", "Run what you typed as a command (in a terminal)"),
    ("1..8", "Open that app from the dock (empty search box only; not when an app's name starts with that digit)"),
]

NORMAL = [
    B("<CR>", "open", "Open the selected app (switches to it when it's already running)"),
    B("o", "open", "Open the selected app (switches to it when it's already running)"),
    B("O", "open:new", "Open a new window of the selected app"),
    B("<C-CR>", "open:new", "", hidden=True),
    B("<S-CR>", "term", "", hidden=True),
]

BOTH = [("Alt+1..9", "Run that numbered action of the selected app")]

# Shown in which-key, help and the palette; documented as one range each below.
DIGITS = [B(f" b{i}", f"dock:{i}", f"Open dock app {i}") for i in range(1, 9)]
DIGITS += [B(f" x{i}", f"action:{i}", f"Run the selected app's action {i}") for i in range(1, 10)]

LEADER = [
    ("Space b 1..8", "Open that app from the dock"),
    ("Space x 1..9", "Run that numbered action of the selected app"),
]
LEADER += [
    B(" ot", "term", "Run what you typed as a command in a terminal"),
    B(" oe", "edit", "Open the selected app's .desktop file in $EDITOR"),
    B(" yn", "copy:name", "Copy the selected app's name"),
    B(" yc", "copy:cmd", "Copy the selected app's command"),
    B(" dd", "forget", "Forget the selected app's usage (it leaves the dock; asks first)"),
    B(" r", "rescan", "Rescan the installed apps"),
]


def keys(tab):
    return NORMAL + DIGITS + [b for b in LEADER if isinstance(b, Bind)]


SECTIONS = [
    ("dvara", "insert", "Insert mode (typing; dvara opens in it)", INSERT),
    ("dvara", "normal", "Normal mode", NORMAL),
    ("dvara", "any", "Both modes", BOTH),
    ("dvara leader", "normal", "Leader (Space)", LEADER),
]
