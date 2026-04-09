"""Text buffer backed by the rope from notebook.utils.balanced."""

from __future__ import annotations

from notebook.utils.balanced import blank


class Buffer:
    def __init__(self, text: str = ""):
        self.rope = blank
        if text:
            self.rope = blank.insert(0, text)
        self.cursor = 0
        self._target_col = 0

    @property
    def length(self) -> int:
        return self.rope.length

    @property
    def text(self) -> str:
        if self.rope.length == 0:
            return ""
        return "".join(self.rope.segments(0, self.rope.length))

    @property
    def lines(self) -> list[str]:
        t = self.text
        if not t:
            return [""]
        return t.split("\n")

    @property
    def line_count(self) -> int:
        if self.rope.length == 0:
            return 1
        return self.rope.newlines + 1

    @property
    def row(self) -> int:
        if self.rope.length == 0:
            return 0
        return self.rope.row(min(self.cursor, self.rope.length))

    @property
    def col(self) -> int:
        if self.rope.length == 0:
            return 0
        r = self.row
        start = self.rope.rowpos(r)
        return self.cursor - start

    def line_text(self, row: int) -> str:
        ls = self.lines
        if 0 <= row < len(ls):
            return ls[row]
        return ""

    def _row_start(self, row: int) -> int:
        if self.rope.length == 0:
            return 0
        return self.rope.rowpos(row)

    # --- Movement ---

    def move_left(self):
        if self.cursor > 0:
            self.cursor -= 1
        self._target_col = self.col

    def move_right(self):
        if self.cursor < self.rope.length:
            self.cursor += 1
        self._target_col = self.col

    def move_up(self):
        r = self.row
        if r > 0:
            start = self._row_start(r - 1)
            line_len = len(self.line_text(r - 1))
            self.cursor = start + min(self._target_col, line_len)

    def move_down(self):
        r = self.row
        if r < self.line_count - 1:
            start = self._row_start(r + 1)
            line_len = len(self.line_text(r + 1))
            self.cursor = start + min(self._target_col, line_len)

    def move_to_line_start(self):
        self.cursor = self._row_start(self.row)
        self._target_col = 0

    def move_to_line_end(self):
        r = self.row
        self.cursor = self._row_start(r) + len(self.line_text(r))
        self._target_col = self.col

    def move_to_start(self):
        self.cursor = 0
        self._target_col = 0

    def move_to_end(self):
        last = self.line_count - 1
        self.cursor = self._row_start(last) + len(self.line_text(last))
        self._target_col = self.col

    def move_word_forward(self):
        t = self.text
        pos = self.cursor
        while pos < len(t) and (t[pos].isalnum() or t[pos] == "_"):
            pos += 1
        while pos < len(t) and not (t[pos].isalnum() or t[pos] == "_"):
            pos += 1
        self.cursor = pos
        self._target_col = self.col

    def move_word_backward(self):
        t = self.text
        pos = self.cursor
        while pos > 0 and not (t[pos - 1].isalnum() or t[pos - 1] == "_"):
            pos -= 1
        while pos > 0 and (t[pos - 1].isalnum() or t[pos - 1] == "_"):
            pos -= 1
        self.cursor = pos
        self._target_col = self.col

    # --- Editing ---

    def insert_text(self, text: str):
        self.rope = self.rope.insert(self.cursor, text)
        self.cursor += len(text)
        self._target_col = self.col

    def delete_char_forward(self):
        if self.cursor < self.rope.length:
            self.rope = self.rope.erase(self.cursor, self.cursor + 1)

    def backspace(self):
        if self.cursor > 0:
            self.cursor -= 1
            self.rope = self.rope.erase(self.cursor, self.cursor + 1)
            self._target_col = self.col

    def delete_line(self):
        r = self.row
        start = self._row_start(r)
        end = start + len(self.line_text(r))
        if end < self.rope.length:
            end += 1  # eat the \n after
        elif start > 0:
            start -= 1  # eat the \n before (last line)
        if start < end:
            self.rope = self.rope.erase(start, end)
        self.cursor = min(start, max(0, self.rope.length))
        self._target_col = self.col

    def open_line_below(self):
        r = self.row
        end = self._row_start(r) + len(self.line_text(r))
        self.cursor = end
        self.insert_text("\n")

    def open_line_above(self):
        start = self._row_start(self.row)
        self.cursor = start
        self.insert_text("\n")
        self.cursor = start
        self._target_col = 0
