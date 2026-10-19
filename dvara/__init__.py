"""dvara (द्वार, "gateway"): the app launcher for Vyom.

Every installed app (.desktop files), ranked by how often and how
recently you open each one; with an empty search, your frequent apps
come first. The preview shows what the app is, its windows that are
already open, and its own actions (New window, Private window...).
"""
import json
import os
import shlex
import shutil
import subprocess
import time

import gi
from gi.repository import Gdk, Gio, Gtk

try:  # GLib >= 2.86 moved DesktopAppInfo to GioUnix
    gi.require_version("GioUnix", "2.0")
    from gi.repository import GioUnix
    DesktopAppInfo = GioUnix.DesktopAppInfo
except (ValueError, ImportError):
    DesktopAppInfo = Gio.DesktopAppInfo

from vyom import Hint, Row, Section, ui, util
from vyom import Plugin as Base

# keybind: Vyom/apps | Enter | Open the selected app
# keybind: Vyom/apps | Ctrl+Enter | Run the selected app's first action (e.g. a new window)
# keybind: Vyom/apps | Shift+Enter | Run what you typed as a command (in a terminal)
# keybind: Vyom/apps | Ctrl+1..9 | Run that numbered action of the selected app

STATE = "dvara-usage"


def windows():
    """app_id / class -> number of open windows (sway / i3 IPC)."""
    if not shutil.which("swaymsg"):
        return {}
    code, out = util.run(["swaymsg", "-t", "get_tree"], timeout=2)
    if code:
        return {}
    counts = {}

    def walk(n):
        if n.get("type") in ("con", "floating_con") and n.get("pid"):
            key = n.get("app_id") or (n.get("window_properties") or {}).get("class")
            if key:
                counts[key.lower()] = counts.get(key.lower(), 0) + 1
        for c in n.get("nodes", []) + n.get("floating_nodes", []):
            walk(c)
    try:
        walk(json.loads(out))
    except ValueError:
        return {}
    return counts


class App:
    def __init__(self, info):
        self.info = info
        self.id = info.get_id() or ""
        self.name = info.get_display_name() or info.get_name() or self.id
        self.desc = info.get_description() or ""
        self.generic = info.get_generic_name() or "" if hasattr(info, "get_generic_name") else ""
        self.keywords = " ".join(info.get_keywords() or []) if hasattr(info, "get_keywords") else ""
        self.exe = info.get_executable() or ""
        self.wmclass = (info.get_startup_wm_class() or "").lower() if hasattr(info, "get_startup_wm_class") else ""
        self.actions = [(a, info.get_action_name(a)) for a in info.list_actions()] if hasattr(info, "list_actions") else []
        self.icon = info.get_icon()

    def window_keys(self):
        base = self.id[:-8] if self.id.endswith(".desktop") else self.id
        return {k for k in (base.lower(), self.wmclass, os.path.basename(self.exe).lower()) if k}


class Plugin(Base):
    name, title, icon, color = "dvara", "Apps", "\U000f003b", "mauve"
    placeholder = "Search apps…   (⇧↵ runs what you type)"
    preview = True
    preview_width = 340
    width = 900
    height = 520
    hints = [Hint("↵", "open"), Hint("⌃↵", "action"), Hint("⇧↵", "run command")]

    def __init__(self, vyom, conf):
        super().__init__(vyom, conf)
        self.apps = []
        self.loaded = 0
        self.wins = {}
        self.terminal = self.conf.get("terminal") or os.environ.get("TERMINAL") or \
            next((t for t in ("kitty", "foot", "alacritty", "wezterm") if shutil.which(t)), "xterm")

    def load(self):
        # Re-read installed apps at most every 30 s (cheap, catches installs).
        if time.time() - self.loaded > 30:
            self.apps = [App(a) for a in Gio.AppInfo.get_all() if a.should_show()]
            self.loaded = time.time()

    def opened(self, args):
        super().opened(args)
        self.wins = windows()

    def score(self, app, q, usage):
        best = None
        for text, weight in ((app.name, 3), (app.generic, 2), (app.keywords, 1.5), (os.path.basename(app.exe), 1.2),
                             (app.desc, 0.6)):
            s = util.fuzzy(q, text) if text else None
            if s is not None:
                best = max(best or 0, s * weight)
        if best is None:
            return None
        u = usage.get(app.id, {})
        return best + min(u.get("count", 0), 50) * 2

    def search(self, q):
        self.load()
        usage = util.load_state(STATE, {})
        rows = []
        if not q:
            freq = sorted((a for a in self.apps if a.id in usage),
                          key=lambda a: (-usage[a.id].get("count", 0), -usage[a.id].get("last", 0)))[:6]
            if freq:
                rows.append(Section("Frequent"))
                rows += [self.row(a) for a in freq]
            rows.append(Section("All apps"))
            rows += [self.row(a) for a in sorted(self.apps, key=lambda a: a.name.lower())]
            return rows
        scored = [(s, a) for a in self.apps if (s := self.score(a, q, usage)) is not None]
        scored.sort(key=lambda t: (-t[0], t[1].name.lower()))
        rows = [self.row(a) for _, a in scored]
        rows.append(Section("Run"))
        rows.append(Row(f"Run “{q}” in a terminal", self.terminal, icon="", color="green",
                        meta="⇧↵", data=("term", q)))
        rows.append(Row(f"Run “{q}”", "as a command, without a terminal", icon="\U000f0e1e", color="peach",
                        data=("cmd", q)))
        return rows

    def row(self, app):
        n = sum(self.wins.get(k, 0) for k in app.window_keys())
        return Row(app.name, app.generic or app.desc or app.exe, icon=app.icon or "\U000f003b",
                   meta=f"{n} open" if n else "", data=app)

    # ------------------------------------------------------------ preview
    def build_preview(self, row):
        if not isinstance(row.data, App):
            what, cmd = row.data
            return ui.vbox(ui.title(row.title), ui.meta("Shift+Enter from anywhere in the list runs what you typed."),
                           ui.mono(cmd), spacing=10)
        app = row.data
        head = ui.hbox(ui.tile(app.icon or "\U000f003b", "mauve", size=26, cls="tile"),
                       ui.vbox(ui.title(app.name), ui.meta(app.generic or app.id), spacing=2), spacing=12)
        head.get_first_child().add_css_class("big")
        n = sum(self.wins.get(k, 0) for k in app.window_keys())
        parts = [head]
        if app.desc:
            parts.append(ui.body(app.desc))
        facts = [("Command", os.path.basename(app.exe) or "-")]
        if n:
            facts.insert(0, ("Running", f"{n} window{'s' if n > 1 else ''}"))
        usage = util.load_state(STATE, {}).get(app.id)
        if usage:
            facts.append(("Opened", f"{usage['count']} time{'s' if usage['count'] > 1 else ''}"))
        parts.append(ui.kv(facts))
        btns = ui.vbox(spacing=6)
        btns.append(ui.button("Open", lambda: self.launch(app), "primary", "\U000f040a"))
        for i, (aid, aname) in enumerate(app.actions[:6], 1):
            btns.append(ui.button(f"{aname}   ⌃{i}", lambda a=aid: self.launch(app, a)))
        parts.append(btns)
        return ui.vbox(*parts, spacing=12)

    # ------------------------------------------------------------ actions
    def launch(self, app, action=None):
        usage = util.load_state(STATE, {})
        u = usage.setdefault(app.id, {"count": 0, "last": 0})
        u["count"] += 1
        u["last"] = time.time()
        util.save_state(STATE, usage)
        ctx = Gdk.Display.get_default().get_app_launch_context()
        try:
            if action:
                app.info.launch_action(action, ctx)
            else:
                app.info.launch([], ctx)
        except Exception as e:
            util.notify("Couldn't open " + app.name, str(e), icon="dialog-error")
        self.close()

    def run_command(self, cmd, terminal):
        if terminal:
            util.spawn([self.terminal, "-e", os.environ.get("SHELL", "sh"), "-c", f"{cmd}; exec {os.environ.get('SHELL', 'sh')}"])
        else:
            util.spawn(cmd)
        self.close()

    def activate(self, row, mods):
        q = self.panel.query().strip() if self.panel else ""
        if "shift" in mods and q:
            self.run_command(q, terminal=True)
            return False
        if isinstance(row.data, App):
            if "ctrl" in mods and row.data.actions:
                self.launch(row.data, row.data.actions[0][0])
            else:
                self.launch(row.data)
            return False
        what, cmd = row.data
        self.run_command(cmd, terminal=(what == "term"))
        return False

    def key(self, name, row, mods):
        if "ctrl" in mods and name.isdigit() and name != "0" and row is not None and isinstance(row.data, App):
            i = int(name) - 1
            if i < len(row.data.actions):
                self.launch(row.data, row.data.actions[i][0])
            return True
        return False
