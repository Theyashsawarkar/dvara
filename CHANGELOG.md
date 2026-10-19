# Changelog

Newest first. Releases are tags (`vX.Y.Z`).

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
