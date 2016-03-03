class TocNode:
    def __init__(self, name, link=None):
        self.name = name
        self.link = link
        self.entries = []

    def add_entry(self, tocnode):
        self.entries.append(tocnode)

