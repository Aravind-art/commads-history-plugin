# History Commands Plugin

A Terminator plugin that displays a searchable command history sidebar, making it easy to browse and re-execute previous commands.

## Features

- **Command History Sidebar**: View shell command history in a dedicated window
- **Search Functionality**: Filter commands with a real-time search bar
- **Multi-Shell Support**: Works with Bash, Zsh, and Fish shells
- **One-Click Execution**: Click any command to execute it in the active terminal
- **Tooltip Preview**: Hover over commands to see full command text
- **Auto-Refresh**: Automatically updates when shell history changes
- **Unique Commands**: Displays only unique commands (duplicates removed)

## Requirements

- **Terminator** terminal emulator
- **Python 3** with PyGObject (GObject Introspection bindings)
- **GTK3** libraries
- One of the supported shells:
  - Bash (`.bash_history`)
  - Zsh (`.zsh_history`)
  - Fish (`.local/share/fish/fish_history`)

## Installation

1. **Locate Terminator plugins directory**:
   ```bash
   mkdir -p ~/.config/terminator/plugins
   ```

2. **Copy the plugin file**:
   ```bash
   cp history_sidebar.py ~/.config/terminator/plugins/
   ```

3. **Enable the plugin** in Terminator:
   - Open Terminator
   - Right-click → Preferences
   - Go to Plugins tab
   - Check **HistorySidebar** to enable it
   - Close preferences

4. **Restart Terminator** for changes to take effect

## Usage

### Opening the History Sidebar

1. Right-click in any Terminator terminal window
2. Look for the option **Show History Sidebar** in the context menu
3. A new window titled "Command History" will appear

### Searching Commands

1. In the history sidebar, type in the search box to filter commands
2. Search is case-insensitive and matches anywhere in the command
3. Results update in real-time as you type
4. Clear the search box to view all commands again

### Executing Commands

- **Click on any command** in the list to execute it in the active terminal
- The command is sent to the terminal without auto-execution (use Enter to run)
- Full command text is shown in a tooltip when hovering

### Hiding the Sidebar

- Right-click in the terminal and select **Hide History Sidebar**
- Or close the Command History window directly

## Configuration

Currently, the plugin automatically detects your shell:

- **Zsh users**: Reads from `~/.zsh_history`
- **Fish users**: Reads from `~/.local/share/fish/fish_history`
- **Bash users**: Reads from `~/.bash_history`

No manual configuration is required.

## Troubleshooting

### Sidebar doesn't appear
- Ensure Terminator is restarted after installing the plugin
- Check that Python GTK3 bindings are installed:
  ```bash
  python3 -c "from gi.repository import Gtk; print('GTK working')"
  ```

### Commands not appearing
- Verify the shell history file exists in the expected location
- Check file permissions (should be readable by your user)
- Ensure you've executed commands in the current shell session

### Plugin not showing in preferences
- Clear Terminator cache:
  ```bash
  rm -rf ~/.config/terminator/plugins/__pycache__
  ```
- Restart Terminator

## Development

To debug or modify the plugin:

1. Edit `history_sidebar.py` in `~/.config/terminator/plugins/`
2. Restart Terminator to apply changes
3. Check for errors in the terminal output

## License

This plugin is provided as-is for use with Terminator.

## Notes

- History is read in reverse chronological order (newest first)
- Only unique commands are displayed (duplicates are automatically filtered)
- The sidebar updates automatically every 2 seconds for new history
- Very long commands are truncated with an ellipsis and shown in full on hover
