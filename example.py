"""
Basic example showing how to create objects from data using a dynamic factory with
register/unregister methods.
"""

import json

from protocol import factory, loader
from gui import gui

def main() -> None:
    """Create devices from a file containg an experiment definition."""

    g = gui.GUI(title="Hyperion", geometry="1400x900")

    # read data from a JSON file
    with open("./config.json") as file:
        data = json.load(file)

        # load the plugins
        loader.load_plugins(data["plugins"])

        for item in data["devices"]:
            item_copy = item.copy()
            query_file = item_copy.pop("queryfile")
            queries = item_copy.pop("queries")
            g.add_device(queryfile=query_file, queries=queries)
            factory.create(item_copy)


if __name__ == "__main__":
    main()
