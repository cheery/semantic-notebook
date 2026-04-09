from textual.widgets import Input
from textual.message import Message


class SearchSubmitted(Message):
    def __init__(self, query: str):
        super().__init__()
        self.query = query


class SearchBar(Input):
    def __init__(self, **kwargs):
        super().__init__(placeholder="Search notes...", **kwargs)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self.post_message(SearchSubmitted(event.value.strip()))
