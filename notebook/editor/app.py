"""A vim-inspired text editor with an always-visible help bar."""

from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Static

from notebook.editor.buffer import Buffer


HELP_NORMAL = (
    "[b]i[/] insert  [b]a[/] append  [b]A[/] end  "
    "[b]o[/]/[b]O[/] open line  [b]x[/] del  [b]dd[/] del line  "
    "[b]:[/] command  [b]h j k l[/] move  "
    "[b]w[/]/[b]b[/] word  [b]0[/]/[b]$[/] line  [b]gg[/]/[b]G[/] file"
)
HELP_INSERT = (
    "[b]Esc[/] → normal    "
    "Type to insert  │  "
    "[b]Backspace[/] [b]Delete[/] [b]Enter[/] [b]Tab[/] [b]Arrow keys[/]"
)
HELP_COMMAND = (
    "[b]Enter[/] execute  [b]Esc[/] cancel  │  "
    "[b]:w[/] save  [b]:q[/] quit  [b]:wq[/] save+quit  [b]:q![/] force quit"
)
HELP = {"NORMAL": HELP_NORMAL, "INSERT": HELP_INSERT, "COMMAND": HELP_COMMAND}

MODE_STYLE = {
    "NORMAL": "bold white on dark_blue",
    "INSERT": "bold white on dark_green",
    "COMMAND": "bold white on dark_magenta",
}


class EditorCanvas(Widget):
    """Renders the text buffer with line numbers and cursor."""

    can_focus = True

    def __init__(self, buf: Buffer, **kwargs):
        super().__init__(**kwargs)
        self.buf = buf
        self.scroll_top = 0

    def render(self) -> Text:
        height = self.size.height
        lines = self.buf.lines
        cur_row = self.buf.row
        cur_col = self.buf.col

        if cur_row < self.scroll_top:
            self.scroll_top = cur_row
        if cur_row >= self.scroll_top + height:
            self.scroll_top = cur_row - height + 1

        gutter = max(3, len(str(len(lines)))) + 1
        result = Text()

        for screen_row in range(height):
            if screen_row > 0:
                result.append("\n")

            file_row = self.scroll_top + screen_row

            if file_row < len(lines):
                result.append(f" {file_row + 1:>{gutter}} ", style="dim")
                result.append("\u2502 ", style="dim")

                line = lines[file_row]
                if file_row == cur_row:
                    if cur_col < len(line):
                        result.append(line[:cur_col])
                        result.append(line[cur_col], style="reverse bold")
                        result.append(line[cur_col + 1:])
                    else:
                        result.append(line)
                        result.append(" ", style="reverse bold")
                else:
                    result.append(line)
            else:
                result.append(f" {'~':>{gutter}} ", style="dim blue")

        return result


class EditorApp(App):
    CSS = """
    #canvas {
        height: 1fr;
    }
    #status-bar {
        height: 1;
        background: $surface;
        padding: 0 1;
    }
    #help-bar {
        height: 1;
        background: $panel;
        padding: 0 1;
    }
    """

    def __init__(self, filepath: str, **kwargs):
        super().__init__(**kwargs)
        self.filepath = Path(filepath)
        text = self.filepath.read_text(encoding="utf-8") if self.filepath.exists() else ""
        self.buf = Buffer(text)
        self.mode = "NORMAL"
        self.command_text = ""
        self.message = ""
        self.modified = False
        self.pending = ""

    def compose(self) -> ComposeResult:
        yield EditorCanvas(self.buf, id="canvas")
        yield Static("", id="status-bar")
        yield Static("", id="help-bar")

    def on_mount(self):
        self._refresh_ui()
        self.query_one("#canvas").focus()

    def _refresh_ui(self):
        self.query_one("#canvas").refresh()

        # Status bar
        mode_style = MODE_STYLE.get(self.mode, "")
        status = Text()
        if self.mode == "COMMAND":
            status.append(f" :{self.command_text}\u2588 ", style=mode_style)
        else:
            status.append(f"  {self.mode}  ", style=mode_style)
        status.append(f"  {self.filepath.name}")
        if self.modified:
            status.append(" [+]", style="bold red")
        status.append(f"  \u2502  Ln {self.buf.row + 1}, Col {self.buf.col + 1}")
        status.append(f"  \u2502  {self.buf.line_count} lines")
        if self.message:
            status.append(f"  \u2502  {self.message}")
        self.query_one("#status-bar").update(status)

        # Help bar
        self.query_one("#help-bar").update(HELP.get(self.mode, ""))

    # --- Key handling ---

    def on_key(self, event):
        event.prevent_default()
        event.stop()
        self.message = ""

        if self.mode == "NORMAL":
            self._handle_normal(event)
        elif self.mode == "INSERT":
            self._handle_insert(event)
        elif self.mode == "COMMAND":
            self._handle_command(event)

        self._refresh_ui()

    def _handle_normal(self, event):
        key = event.key
        char = event.character or ""

        # Multi-key sequences
        if self.pending == "d":
            self.pending = ""
            if key == "d":
                self.buf.delete_line()
                self.modified = True
            return
        if self.pending == "g":
            self.pending = ""
            if key == "g":
                self.buf.move_to_start()
            return

        # Navigation
        if key in ("h", "left"):
            self.buf.move_left()
        elif key in ("l", "right"):
            self.buf.move_right()
        elif key in ("j", "down"):
            self.buf.move_down()
        elif key in ("k", "up"):
            self.buf.move_up()
        elif key == "w":
            self.buf.move_word_forward()
        elif key == "b" and not self.pending:
            self.buf.move_word_backward()
        elif key == "0" or key == "home":
            self.buf.move_to_line_start()
        elif char == "$" or key == "end":
            self.buf.move_to_line_end()

        # Mode switches
        elif key == "i":
            self.mode = "INSERT"
        elif key == "a":
            self.buf.move_right()
            self.mode = "INSERT"
        elif char == "A":
            self.buf.move_to_line_end()
            self.mode = "INSERT"
        elif char == "I":
            self.buf.move_to_line_start()
            self.mode = "INSERT"
        elif key == "o":
            self.buf.open_line_below()
            self.mode = "INSERT"
            self.modified = True
        elif char == "O":
            self.buf.open_line_above()
            self.mode = "INSERT"
            self.modified = True

        # Editing
        elif key == "x":
            self.buf.delete_char_forward()
            self.modified = True
        elif key == "d":
            self.pending = "d"
        elif key == "g":
            self.pending = "g"
        elif char == "G":
            self.buf.move_to_end()

        # Command mode
        elif char == ":":
            self.mode = "COMMAND"
            self.command_text = ""

    def _handle_insert(self, event):
        key = event.key

        if key == "escape":
            self.mode = "NORMAL"
            if self.buf.col > 0 and self.buf.col >= len(self.buf.line_text(self.buf.row)):
                self.buf.move_left()
        elif key == "backspace":
            self.buf.backspace()
            self.modified = True
        elif key == "delete":
            self.buf.delete_char_forward()
            self.modified = True
        elif key == "enter":
            self.buf.insert_text("\n")
            self.modified = True
        elif key == "tab":
            self.buf.insert_text("    ")
            self.modified = True
        elif key in ("left", ):
            self.buf.move_left()
        elif key in ("right", ):
            self.buf.move_right()
        elif key in ("up", ):
            self.buf.move_up()
        elif key in ("down", ):
            self.buf.move_down()
        elif key == "home":
            self.buf.move_to_line_start()
        elif key == "end":
            self.buf.move_to_line_end()
        elif event.character and len(event.character) == 1 and event.character.isprintable():
            self.buf.insert_text(event.character)
            self.modified = True

    def _handle_command(self, event):
        key = event.key

        if key == "escape":
            self.mode = "NORMAL"
            self.command_text = ""
        elif key == "backspace":
            if self.command_text:
                self.command_text = self.command_text[:-1]
            else:
                self.mode = "NORMAL"
        elif key == "enter":
            self._run_command(self.command_text.strip())
            self.command_text = ""
        elif event.character and event.character.isprintable():
            self.command_text += event.character

    def _run_command(self, cmd: str):
        if cmd == "w":
            self._save()
        elif cmd == "q":
            if self.modified:
                self.message = "Unsaved changes! :q! to force, :wq to save+quit"
                self.mode = "NORMAL"
                return
            self.exit()
        elif cmd == "q!":
            self.exit()
        elif cmd == "wq" or cmd == "x":
            self._save()
            self.exit()
        else:
            self.message = f"Unknown: {cmd}"
        self.mode = "NORMAL"

    def _save(self):
        self.filepath.write_text(self.buf.text, encoding="utf-8")
        self.modified = False
        self.message = f"Saved {self.filepath.name}"
