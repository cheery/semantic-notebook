from textual.binding import Binding
from textual.widgets import Markdown


class NoteViewer(Markdown):
    can_focus = True

    def show_note(self, title: str, content: str) -> None:
        self.update(content)

    def show_empty(self) -> None:
        self.update("*Select a note to view*")
