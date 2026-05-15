"""
Basic example showing how to create objects from data using a dynamic factory with
register/unregister methods.
"""

import json

from protocol import factory, loader


def main() -> None:
    """Create devices from a file containg an experiment definition."""

    # read data from a JSON file
    with open("./level.json") as file:
        data = json.load(file)

        # load the plugins
        loader.load_plugins(data["plugins"])

        # create the characters
        characters = [factory.create(item) for item in data["characters"]]

        # do something with the characters
        for character in characters:
            character.make_a_noise()


if __name__ == "__main__":
    main()
