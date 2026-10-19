# dvara

**dvara** (द्वार, "gateway") — The app launcher. A tool for [Vyom](https://github.com/Theyashsawarkar/vyom), the keyboard-driven panels of [Vayu](https://github.com/Theyashsawarkar/vayu); in Vayu it replaces wofi's app launcher (`wofi --show drun`).

> App launcher: your most-used apps first, app actions, running windows, run a command.

## Features

- Every installed app (.desktop files), with its real icon.
- Ranked by **how often and how recently you open each app**; with an empty search, your frequent apps come first, then everything A–Z.
- Matches the name, the generic name ("Web browser"), keywords and the command, typos and all.
- The preview shows what the app is, **how many of its windows are already open**, and its own actions (New window, Private window…), each on `Ctrl+1..9`.
- `Shift+Enter` runs whatever you typed as a command in a terminal; a row below the results runs it without one.

## Keys

| Key | Action |
|---|---|
| `Enter` | Open the selected app |
| `Ctrl+Enter` | Run the selected app's first action (e.g. a new window) |
| `Shift+Enter` | Run what you typed as a command (in a terminal) |
| `Ctrl+1..9` | Run that numbered action of the selected app |
| `Esc` | close |

Every Vyom panel also has: `Up`/`Down` (or `Ctrl+K`/`Ctrl+J`) to move, `Page Up`/`Page Down`, `Tab` to switch to the next tool.

## Requirements

- [Vyom](https://github.com/Theyashsawarkar/vyom) 0.2 or newer (Python 3.11+, GTK 4, gtk4-layer-shell, a layer-shell compositor)
- optional: swaymsg (open-window counts)

## Install

```sh
git clone https://github.com/Theyashsawarkar/dvara ~/.local/share/vyom/plugins/dvara
vyom reload        # or log out and in
vyom dvara         # open it (again: close it)
```

Bind it to a key, e.g. in sway:

```
bindsym $mod+<key> exec vyom dvara
```

Update: `git -C ~/.local/share/vyom/plugins/dvara pull && vyom reload`. `vyom list` shows every installed tool and why one would be skipped.

## Configuration

In `~/.config/vyom/config.toml` (all optional):

```toml
[plugin.dvara]
# terminal: terminal for Shift+Enter (default: $TERMINAL, else kitty/foot/alacritty/wezterm)
```

## License

MIT.
