from textual.widgets import Static, Tree
from textual.containers import Vertical

from notebook.clusters import Cluster


class ClusterView(Vertical):
    def update_clusters(self, clusters: list[Cluster]) -> None:
        self.remove_children()
        if not clusters:
            self.mount(Static("No clusters yet. Index some notes first."))
            return
        tree = Tree("Topics")
        tree.root.expand()
        for cluster in clusters:
            branch = tree.root.add(f"[bold]{cluster.label}[/bold] ({len(cluster.note_ids)})")
            for title in cluster.note_titles:
                branch.add_leaf(title)
        self.mount(tree)
