"""dvara (द्वार, "gateway"): the app launcher for Vyom.

Every installed app (.desktop files), ranked by how often and how
recently you open each one. With an empty search, your most-used apps
sit in a dock of big icons above the list (1..8 opens one). The letters
that matched are highlighted. An app that's already open says so
("Running · 2 windows") and Enter switches to it; Ctrl+Enter opens a new
window. The preview shows its open windows (with their workspace) and its
own actions (New window, Private window...) as buttons, Alt+1..9.
"""
import datetime
import json
import logging
import os
import re
import shutil
import time

import gi
from gi.repository import Gdk, Gio, GLib, Gtk, Pango

try:  # GLib >= 2.86 moved DesktopAppInfo to GioUnix
    gi.require_version("GioUnix", "2.0")
    from gi.repository import GioUnix
    DesktopAppInfo = GioUnix.DesktopAppInfo
except (ValueError, ImportError):
    DesktopAppInfo = Gio.DesktopAppInfo

from vyom import Hint, Row, Section, ui, util
from vyom import Plugin as Base

# keybind: Vyom/apps | Enter | Open the selected app (switches to it when it's already running)
# keybind: Vyom/apps | Ctrl+Enter | Open a new window of the selected app
# keybind: Vyom/apps | Shift+Enter | Run what you typed as a command (in a terminal)
# keybind: Vyom/apps | Alt+1..9 | Run that numbered action of the selected app
# keybind: Vyom/apps | 1..8 | Open that app from the dock (empty search box only)

STATE = "dvara-usage"
DOCK = 8
PEACH = "#fab387"

log = logging.getLogger("vyom.dvara")


def theme_peach():
    """The theme's peach (Pango can't read CSS): the last @define-color in
    Vyom's stylesheets, the theme's loading last."""
    try:
        import vyom
        from vyom import config
        paths = [os.path.join(os.path.dirname(vyom.__file__), "style.css"),
                 os.path.join(os.path.dirname(config.PATH), "style.css")]
        extra = config.load().get("vyom", {}).get("css", [])
        paths += [os.path.expanduser(str(p)) for p in ([extra] if isinstance(extra, str) else extra)]
        text = ""
        for p in paths:
            if os.path.exists(p):
                text += open(p).read()
        found = re.findall(r"@define-color\s+peach\s+(#[0-9a-fA-F]{6})\s*;", text)
        return found[-1] if found else PEACH
    except Exception:  # noqa: BLE001 -- the default is fine
        return PEACH


def windows():
    """Open windows from the sway / i3 tree: [{id, key, title, workspace,
    focused}]; [] without swaymsg."""
    if not shutil.which("swaymsg"):
        return []
    code, out = util.run(["swaymsg", "-t", "get_tree", "-r"], timeout=2)
    if code:
        return []
    found = []

    def walk(n, ws):
        if n.get("type") == "workspace":
            ws = n.get("name") or ws
        if n.get("type") in ("con", "floating_con") and n.get("pid"):
            key = n.get("app_id") or (n.get("window_properties") or {}).get("class")
            if key and ws != "__i3_scratch":
                found.append({"id": n.get("id"), "key": key.lower(), "title": n.get("name") or key,
                              "workspace": ws, "focused": bool(n.get("focused"))})
        for c in n.get("nodes", []) + n.get("floating_nodes", []):
            walk(c, ws)
    try:
        walk(json.loads(out), "")
    except ValueError:
        return []
    return found


def match_spans(q, text):
    """Where `q`'s letters are in `text` (the same rule as util.fuzzy):
    the substring if it's there, else each letter in order."""
    q, t = q.lower(), text.lower()
    if not q:
        return []
    i = t.find(q)
    if i >= 0:
        return list(range(i, i + len(q)))
    out, pos = [], 0
    for ch in q:
        j = t.find(ch, pos)
        if j < 0:
            return []
        out.append(j)
        pos = j + 1
    return out


def highlighted(text, spans, color):
    """`text` as Pango markup with the matched letters in peach and
    underlined (the shape says it too, not only the colour)."""
    esc = GLib.markup_escape_text
    marks = set(spans)
    out, run, on = [], "", None
    for i, ch in enumerate(text):
        hit = i in marks
        if on is not None and hit != on:
            out.append(f"<span foreground='{color}' underline='single'>{esc(run)}</span>" if on else esc(run))
            run = ""
        run += ch
        on = hit
    if run:
        out.append(f"<span foreground='{color}' underline='single'>{esc(run)}</span>" if on else esc(run))
    return "".join(out)


def when(t):
    if not t:
        return ""
    a = datetime.datetime.fromtimestamp(t)
    days = (datetime.date.today() - a.date()).days
    if days == 0:
        return "today " + a.strftime("%H:%M")
    if days == 1:
        return "yesterday " + a.strftime("%H:%M")
    if days < 7:
        return a.strftime("%A")
    return "last week" if days < 14 else f"{a.day} {a.strftime('%b')}"


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
        keys = {base.lower(), self.wmclass, os.path.basename(self.exe).lower()}
        keys.add(base.lower().split(".")[-1])          # org.gnome.Nautilus -> nautilus
        return {k for k in keys if k}


class Plugin(Base):
    name, title, icon, color = "dvara", "Apps", "\U000f003b", "blue"
    placeholder = "Search apps…   (Shift+Enter runs what you type)"
    preview = True
    preview_width = 340
    hints = [Hint("Enter", "open / switch"), Hint("Ctrl+Enter", "new window"), Hint("Alt+1..9", "action"),
             Hint("Shift+Enter", "run command")]

    def __init__(self, vyom, conf):
        super().__init__(vyom, conf)
        self.apps = []
        self.loaded = 0
        self.wins = []
        self.dock = []
        self.q = ""
        self.peach = theme_peach()
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

    def windows_of(self, app):
        keys = app.window_keys()
        return [w for w in self.wins if w["key"] in keys]

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
        self.q = q
        usage = util.load_state(STATE, {})
        if not q:
            self.dock = sorted((a for a in self.apps if a.id in usage),
                               key=lambda a: (-usage[a.id].get("count", 0), -usage[a.id].get("last", 0)))[:DOCK]
            rows = []
            running = [a for a in self.apps if self.windows_of(a)]
            if running:
                rows.append(Section("Running", len(running), "Enter switches"))
                rows += [self.row(a, q, usage) for a in sorted(running, key=lambda a: a.name.lower())]
            rows.append(Section("All apps", len(self.apps)))
            rows += [self.row(a, q, usage) for a in sorted(self.apps, key=lambda a: a.name.lower())]
            return rows
        self.dock = []
        scored = [(s, a) for a in self.apps if (s := self.score(a, q, usage)) is not None]
        scored.sort(key=lambda t: (-t[0], t[1].name.lower()))
        rows = []
        if scored:
            rows.append(Section("Apps", len(scored)))
            rows += [self.row(a, q, usage) for _, a in scored]
        esc = GLib.markup_escape_text
        rows.append(Section("Run"))
        rows.append(Row(f"Run “{esc(q)}” as a command", f"in {esc(self.terminal)} · Shift+Enter from any row",
                        icon="", color="peach", markup=True, data=("term", q)))
        rows.append(Row(f"Run “{esc(q)}” without a terminal", "in the background", icon="\U000f0e1e", color="peach",
                        markup=True, data=("cmd", q)))
        return rows

    def row(self, app, q, usage):
        wins = self.windows_of(app)
        title = highlighted(app.name, match_spans(q, app.name), self.peach) if q else GLib.markup_escape_text(app.name)
        sub = app.generic or app.desc or app.exe
        u = usage.get(app.id)
        if q and u and not wins:
            sub += f" · used {when(u.get('last'))}" if u.get("last") else ""
        chips = [(f"● Running · {len(wins)} window{'s' if len(wins) != 1 else ''}", "green")] if wins else None
        return Row(title, GLib.markup_escape_text(sub), icon=app.icon or "\U000f003b", color="gray", markup=True,
                   chips=chips, data=app)

    # ------------------------------------------------------------ the dock
    def build_strip(self):
        if self.q or not self.dock:
            return None
        bar = Gtk.Box(spacing=5, homogeneous=True)
        bar.add_css_class("dock")
        for i, app in enumerate(self.dock, 1):
            b = Gtk.Button()
            b.add_css_class("dock-app")
            b.set_can_focus(False)
            b.set_tooltip_text(f"{app.name} ({i})")
            inner = ui.vbox(spacing=4)
            icon = Gtk.Image.new_from_gicon(app.icon) if isinstance(app.icon, Gio.Icon) else ui.label("\U000f003b", "glyph")
            if isinstance(icon, Gtk.Image):
                icon.set_pixel_size(40)
            inner.append(icon)
            inner.append(ui.label(app.name, "dock-name", ellipsize=Pango.EllipsizeMode.END, max_width_chars=7))
            num = ui.label(str(i), "keycap", halign=Gtk.Align.CENTER)
            if self.windows_of(app):
                num = ui.hbox(num, ui.label("●", "t-green", tooltip_text="running"), spacing=4)
                num.set_halign(Gtk.Align.CENTER)
            inner.append(num)
            b.set_child(inner)
            b.connect("clicked", lambda _b, a=app: self.open_app(a))
            bar.append(b)
        return ui.vbox(ui.section("Most used", "", "1..8 opens"), bar, spacing=2)

    # ------------------------------------------------------------ preview
    def build_preview(self, row):
        if not isinstance(row.data, App):
            what, cmd = row.data
            return ui.vbox(ui.title(row.title.replace("&amp;", "&")),
                           ui.meta(f"In {self.terminal}, which stays open afterwards." if what == "term"
                                   else "In the background: you won't see its output."),
                           ui.mono(cmd), ui.button("Run", lambda: self.run_command(cmd, what == "term"), "primary",
                                                   "", "Shift+Enter" if what == "term" else "Enter"), spacing=10)
        app = row.data
        usage = util.load_state(STATE, {}).get(app.id) or {}
        tile = ui.tile(app.icon or "\U000f003b", "gray", size=26, cls="tile")
        tile.add_css_class("big")
        opened = f"Opened {usage['count']} time{'s' if usage['count'] != 1 else ''}" if usage.get("count") else "Not opened from here yet"
        if usage.get("last"):
            opened += f" · last {when(usage['last'])}"
        head = ui.hbox(tile, ui.vbox(ui.title(app.name), ui.meta(opened), spacing=2), spacing=12)
        parts = [head]
        if app.desc or app.generic:
            parts.append(ui.body(GLib.markup_escape_text(app.desc or app.generic)))
        wins = self.windows_of(app)
        main = ui.vbox(spacing=8)
        if wins:
            main.append(ui.button("Switch to it", lambda: self.focus(wins[0]), "primary", "\uf061", "Enter"))
            main.append(ui.button("New window", lambda: self.launch(app), icon="\U000f0415", key="Ctrl+Enter"))
        else:
            main.append(ui.button("Open", lambda: self.launch(app), "primary", "\U000f040a", "Enter"))
        parts.append(main)
        if wins:
            box = ui.vbox(ui.section("Windows", len(wins), "click to switch"), spacing=6)
            for w in wins[:8]:
                b = Gtk.Button()
                b.add_css_class("btn")
                b.add_css_class("win")
                inner = ui.hbox(ui.label("\uf2d0", "glyph", "t-green"),
                                ui.vbox(ui.label(w["title"], "win-title", xalign=0, ellipsize=Pango.EllipsizeMode.END),
                                        ui.label(f"workspace {w['workspace']}" + (" · focused" if w["focused"] else ""),
                                                 "p-meta", xalign=0), spacing=1), spacing=10)
                b.set_child(inner)
                b.connect("clicked", lambda _b, w=w: self.focus(w))
                box.append(b)
            parts.append(box)
        if app.actions:
            acts = ui.vbox(ui.section("Actions", len(app.actions)), spacing=6)
            for i, (aid, aname) in enumerate(app.actions[:9], 1):
                acts.append(ui.button(aname, lambda a=aid: self.launch(app, a), icon="\U000f040a", key=f"Alt+{i}"))
            parts.append(acts)
        parts.append(ui.kv([("Command", os.path.basename(app.exe) or "-")]))
        return ui.vbox(*parts, spacing=12)

    # ------------------------------------------------------------ actions
    def count(self, app):
        usage = util.load_state(STATE, {})
        u = usage.setdefault(app.id, {"count": 0, "last": 0})
        u["count"] += 1
        u["last"] = time.time()
        util.save_state(STATE, usage)

    def open_app(self, app):
        """Switch to it when it's running (sway / i3), else open it."""
        wins = self.windows_of(app)
        if wins:
            self.count(app)
            self.focus(wins[0])
        else:
            self.launch(app)

    def focus(self, w):
        code, _ = util.run(["swaymsg", f"[con_id={int(w['id'])}]", "focus"], timeout=2)
        if code:
            self.set_status("couldn't switch to it")
            return
        self.close()

    def launch(self, app, action=None):
        self.count(app)
        ctx = Gdk.Display.get_default().get_app_launch_context()
        try:
            if action:
                app.info.launch_action(action, ctx)
            else:
                app.info.launch([], ctx)
        except Exception as e:
            log.exception("couldn't launch %s (action %r)", app.name, action)
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
            if "ctrl" in mods:
                self.launch(row.data)
            else:
                self.open_app(row.data)
            return False
        what, cmd = row.data
        self.run_command(cmd, terminal=(what == "term"))
        return False

    def key(self, name, row, mods):
        # Alt: Ctrl+1..9 switch a tool's tabs in every Vyom tool
        if mods == {"alt"} and name.isdigit() and name != "0" and row is not None and isinstance(row.data, App):
            i = int(name) - 1
            if i < len(row.data.actions):
                self.launch(row.data, row.data.actions[i][0])
            return True
        # 1..8 with an empty search box: the dock (unless an app's name starts with it)
        if not mods and len(name) == 1 and name in "12345678" and self.panel and not self.panel.query() and self.dock:
            i = int(name) - 1
            if i < len(self.dock) and not any(a.name.startswith(name) for a in self.apps):
                self.open_app(self.dock[i])
                return True
        return False
