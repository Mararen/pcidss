from rich.tree import Tree
from rich.console import Console
from pathlib import Path

def build_tree(directory, tree, max_depth, current_depth=0):
    if current_depth >= max_depth:
        return
    for path in sorted(Path(directory).iterdir()):
        branch = tree.add(path.name)
        if path.is_dir():
            build_tree(path, branch, max_depth, current_depth + 1)

console = Console()
root = Tree("pcidss")
build_tree(".", root, max_depth=3)
console.print(root)