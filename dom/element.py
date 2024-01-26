class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.children = []
        self.parent = parent
        self.attributes = attributes
        self.style = {}

    def __repr__(self):
        return "<" + self.tag + ">"
