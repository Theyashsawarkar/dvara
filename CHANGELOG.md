# Changelog

Newest first. Releases are tags (`vX.Y.Z`).

## v0.3.0 -- 2026-11-09

- **Vim keys** (Vyom 0.7, ADR 0008): NORMAL and INSERT modes, `Space` as the leader with a which-key strip, `?` and `Space ?` list every key, `Space Space` is a palette, counts (`5j`), `gg` / `G`, `H` / `L` for tabs. It opens in INSERT (search-first): type, then `Esc` for NORMAL. Needs Vyom 0.7.0.
- Its keys are data (`dvara/vim.py`); `scripts/keybinds.py` writes the `# keybind:` lines and the README's key tables from them, and `--check` (CI) fails when they drift.
- `O` opens a new window, `Space b 1..8` opens a dock app, `Space x 1..9` runs an app's own action, `Space o t` runs what you typed in a terminal, `Space o e` opens its .desktop file, `Space y n` / `Space y c` copy its name / command, `Space d d` forgets its usage (asks first), `Space r` rescans.
- `1..8` open the dock only while typing in an empty search box (in NORMAL, digits are counts).
- `1`..`8` in INSERT only open a dock app the dock has: past its end the digit is typed, as before.
- `Enter` / `o` / `O` in NORMAL typed before the results arrive wait for them, so they open the app you searched for.

## v0.2.1 -- 2026-11-08

- The dock shows icons and names only, no number keys under them (`1..8` still opens one,
  left to right; the tooltip says which); a running app keeps its green dot.

## v0.2.0 -- 2026-11-07

- **A dock of your 8 most-used apps** as big icons above the list when the search box is empty; `1..8`
  opens one (unless an app's name starts with that digit, so you can still search for it). Running
  apps come next, then everything A–Z.
- **The letters that matched are highlighted** (peach and underlined), so you can see why a search
  found an app.
- **Running apps say so** in green ("Running · 2 windows"), and **Enter switches to them** instead of
  opening another (sway / i3). `Ctrl+Enter` now opens a new window (it used to run the first action:
  that's `Alt+1`).
- The preview shows the app's **open windows with their workspace** (click one to switch to it), how
  often and when you last opened it, and its actions as buttons with their keys (`Alt+1..9`).
- "Run as a command" (`Shift+Enter`) and "without a terminal" rows under the results, with a preview.
- Blue, like the redesign's Apps panel. Needs Vyom 0.6.0.

## v0.1.7 -- 2026-11-06

- **Alt+1..9 runs an app's numbered action** (New window, Private window…): Ctrl+1..9 now switches a tool's tabs in every Vyom tool.
- Every corner is rounded: the website's callouts.
- A logo and a shloka at the top of the README and the website: every Vayu tool has them now.

## v0.1.6 -- 2026-10-24

- An app that fails to launch is logged with its traceback, as well as the notification. Unused imports removed.
- Logs are in the journal (Vyom 0.3.2): the README, CONTRIBUTING and the bug
  report form say `journalctl --user -u vyom -u vyom-daemon -b`.

## v0.1.5 -- 2026-10-21

- A website (GitHub Pages, https://theyashsawarkar.github.io/dvara/): the README as a home page, the
  changelog, and architecture decision records (`docs/adr/`), built from these files by
  `scripts/build-site.py`; CI checks the site is up to date.

## v0.1.4 -- 2026-10-21

- Documentation for open source: a logo and banner, a full README (features,
  install, usage, configuration, troubleshooting, the whole Vyom family),
  CONTRIBUTING, SECURITY and CODE_OF_CONDUCT, issue and pull request
  templates, and CI (compiles, checks plugin.toml and that every key is
  documented).

## v0.1.3 -- 2026-10-19

- Opens at Vyom's shared panel size (Vyom 0.2.5) like every other tool:
  its own width/height are gone.

## v0.1.2 -- 2026-10-19

- Keys are spelled out (Ctrl+Enter, Shift+Enter, Backspace) instead of symbols
  (⌃↵, ⇧↵, ⌫) in the footer and on rows and buttons.

## v0.1.1 -- 2026-10-19

- Wider: 900 x 520 (before Vyom's scale), with a 340 px preview, so long app
  names and descriptions fit.

## v0.1.0 -- 2026-10-19

- First release, as its own repository: the app launcher. Replaces wofi's app launcher (`wofi --show drun`) in Vayu.
- Every installed app (.desktop files), with its real icon.
- Ranked by **how often and how recently you open each app**; with an empty search, your frequent apps come first, then everything A–Z.
- Matches the name, the generic name ("Web browser"), keywords and the command, typos and all.
- The preview shows what the app is, **how many of its windows are already open**, and its own actions (New window, Private window…), each on `Ctrl+1..9`.
- `Shift+Enter` runs whatever you typed as a command in a terminal; a row below the results runs it without one.
