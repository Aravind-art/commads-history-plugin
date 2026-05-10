import os
import re
from gi.repository import Gtk, GLib, Pango, Gdk
import terminatorlib.plugin as plugin

AVAILABLE = ['HistorySidebar']


class HistorySidebar(plugin.MenuItem):
    capabilities = ['terminal_menu']

    _sidebar_injected = False
    _sidebar_widget   = None
    _list_box         = None   # Gtk.ListBox — replaces TreeView
    _commands         = []     # Plain Python list — replaces ListStore
    _search_entry     = None
    _active_terminal  = None

    def __init__(self):
        plugin.MenuItem.__init__(self)

        shell = os.environ.get('SHELL', '/bin/bash')
        home  = os.path.expanduser('~')

        if 'zsh' in shell:
            self.history_file = os.path.join(home, '.zsh_history')
        elif 'fish' in shell:
            self.history_file = os.path.join(home, '.local', 'share', 'fish', 'fish_history')
        else:
            self.history_file = os.path.join(home, '.bash_history')

        self._last_modified = 0

    def callback(self, menuitems, menu, terminal):
        HistorySidebar._active_terminal = terminal

        if not HistorySidebar._sidebar_injected:
            HistorySidebar._sidebar_injected = True
            GLib.idle_add(self._inject_sidebar, terminal)

        menuitems.append(Gtk.SeparatorMenuItem())

        is_visible = (
            HistorySidebar._sidebar_widget is not None and
            HistorySidebar._sidebar_widget.is_visible()
        )
        label = 'Hide History Sidebar' if is_visible else 'Show History Sidebar'
        toggle_item = Gtk.MenuItem(label=label)
        toggle_item.connect('activate', self._toggle_sidebar)
        menuitems.append(toggle_item)

    def _inject_sidebar(self, terminal):
        main_window = terminal.get_toplevel()
        if not isinstance(main_window, Gtk.Window):
            return False

        win = Gtk.Window()
        win.set_title('Command History')
        win.set_default_size(280, 600)
        win.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        win.set_transient_for(main_window)
        win.set_destroy_with_parent(True)

        mx, my = main_window.get_position()
        mw, _  = main_window.get_size()
        win.move(mx + mw + 4, my)

        win.connect('delete-event', lambda w, e: w.hide() or True)

        sidebar = self._build_sidebar()
        win.add(sidebar)
        win.realize()

        HistorySidebar._sidebar_widget = win

        GLib.timeout_add(2000, self._refresh_history)
        self._refresh_history()

        return False

    def _build_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_size_request(260, -1)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(8)
        box.set_margin_bottom(8)

        heading = Gtk.Label()
        heading.set_markup('<b>📋 Command History</b>')
        heading.set_halign(Gtk.Align.START)
        box.pack_start(heading, False, False, 0)

        search = Gtk.Entry()
        search.set_placeholder_text('Search commands...')
        search.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, 'system-search-symbolic')
        search.connect('changed', self._on_search_changed)
        HistorySidebar._search_entry = search
        box.pack_start(search, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        box.pack_start(scroll, True, True, 0)

        # Gtk.ListBox — each row is a full widget, so Gtk.Label handles
        # unicode and emoji rendering natively via Pango's font fallback.
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.set_filter_func(self._filter_row)
        list_box.connect('row-activated', self._on_row_activated)
        HistorySidebar._list_box = list_box


        scroll.add(list_box)
        return box

    def _to_pango_markup(self, text):
        # Only escape XML special characters — no font spans, no overrides.
        # GTK handles emoji fallback naturally when we don't interfere,
        # exactly the same way the heading label renders 📋 without any hints.
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))

    def _make_row(self, cmd):
        row = Gtk.ListBoxRow()

        # Store the raw command directly on the row object so we can
        # retrieve it on click without any index matching gymnastics.
        row.command = cmd

        label = Gtk.Label()
        label.set_markup(self._to_pango_markup(cmd))
        label.set_halign(Gtk.Align.START)   # left-align text
        label.set_xalign(0)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_tooltip_text(cmd)         # full command on hover

        # Wrap in a box for padding
        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        inner.set_margin_start(4)
        inner.set_margin_end(4)
        inner.set_margin_top(3)
        inner.set_margin_bottom(3)
        inner.pack_start(label, True, True, 0)

        row.add(inner)
        return row

    def _read_history(self):
        commands = []

        if not os.path.exists(self.history_file):
            return commands

        try:
            with open(self.history_file, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if re.match(r'^:\s*\d+:\d+;', line):
                        parts = line.split(';', 1)
                        if len(parts) > 1:
                            line = parts[1]
                    if line.startswith('- cmd:'):
                        line = line[6:].strip()
                    if line:
                        commands.append(line)
        except Exception as e:
            print(f'HistorySidebar: Could not read history file: {e}')

        seen   = set()
        unique = []
        for cmd in reversed(commands):
            if cmd not in seen:
                seen.add(cmd)
                unique.append(cmd)

        return unique

    def _refresh_history(self):
        if HistorySidebar._list_box is None:
            return True

        try:
            current_mtime = os.path.getmtime(self.history_file)
        except:
            return True

        if current_mtime == self._last_modified:
            return True

        self._last_modified = current_mtime

        # Remove all existing rows
        for child in HistorySidebar._list_box.get_children():
            HistorySidebar._list_box.remove(child)

        HistorySidebar._commands = self._read_history()

        for cmd in HistorySidebar._commands:
            row = self._make_row(cmd)
            HistorySidebar._list_box.add(row)

        HistorySidebar._list_box.show_all()
        HistorySidebar._list_box.invalidate_filter()

        return True

    def _filter_row(self, row, data=None):
        if HistorySidebar._search_entry is None:
            return True

        search_text = HistorySidebar._search_entry.get_text().lower()
        if not search_text:
            return True

        # command is stored directly on the row object in _make_row
        return search_text in getattr(row, 'command', '').lower()

    def _on_search_changed(self, entry):
        if HistorySidebar._list_box:
            HistorySidebar._list_box.invalidate_filter()

    def _on_row_activated(self, list_box, row):
        if HistorySidebar._active_terminal is None:
            return

        command = getattr(row, 'command', None)
        if not command:
            return

        try:
            vte = HistorySidebar._active_terminal.vte
        except AttributeError:
            return

        if vte is None:
            return

        try:
            vte.feed_child(command.encode('utf-8'))
        except TypeError:
            encoded = command.encode('utf-8')
            vte.feed_child(encoded, len(encoded))

    def _toggle_sidebar(self, menuitem):
        if HistorySidebar._sidebar_widget is None:
            return

        if HistorySidebar._sidebar_widget.is_visible():
            HistorySidebar._sidebar_widget.hide()
        else:
            HistorySidebar._sidebar_widget.show_all()