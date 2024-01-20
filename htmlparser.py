from text import Text
from element import Element


class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []

    HEAD_TAGS = [
        "base",
        "basefont",
        "bgsound",
        "noscript",
        "link",
        "meta",
        "title",
        "style",
        "script",
    ]

    SELF_CLOSING_TAGS = [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]

    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c

        if not in_tag and text:
            self.add_text(text)

        return self.finish()

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}

        try:
            for attrpair in parts[1:]:
                if "=" in attrpair:
                    key, value = attrpair.split("=", 1)
                    attributes[key.casefold()] = value

                    if len(value) > 2 and value[0] in ["'", '"']:
                        value = value[1:-1]

                else:
                    attributes[attrpair.casefold()] = ""

            return tag, attributes
        except Exception as e:
            print("Error at HTMLParser get attributes method ", e)
            return tag, attributes

    def add_text(self, text):
        if text.isspace():
            return

        try:
            self.implicit_tags(None)
            if self.unfinished:
                parent = self.unfinished[-1]
                node = Text(text, parent)
                parent.children.append(node)
            else:
                print("No unfinished in add text")
                pass
        except Exception as e:
            print("Error at HTMLParser get text method ", e)

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return

        self.implicit_tags(tag)

        try:
            if tag.startswith("/"):
                if len(self.unfinished) == 1:
                    return
                node = self.unfinished.pop()
                parent = self.unfinished[-1]
                parent.children.append(node)

            elif tag in self.SELF_CLOSING_TAGS:
                if self.unfinished:
                    parent = self.unfinished[-1]
                    node = Element(tag, attributes, parent)
                    parent.children.append(node)
                else:
                    print("No unfinished in add tag 2")
                    pass

            else:
                parent = self.unfinished[-1] if self.unfinished else None
                node = Element(tag, attributes, parent)
                self.unfinished.append(node)

        except Exception as e:
            print("Error at HTMLParser add tag method ", e)

    def implicit_tags(self, tag):
        try:
            while True:
                open_tags = [node.tag for node in self.unfinished]
                if open_tags == [] and tag != "html":
                    self.add_tag("html")
                elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                    if tag in self.HEAD_TAGS:
                        self.add_tag("head")
                    else:
                        self.add_tag("body")
                elif (
                    open_tags == ["html", "head"]
                    and tag not in ["/head"] + self.HEAD_TAGS
                ):
                    self.add_tag("/head")
                else:
                    break
        except Exception as e:
            print("Error at HTMLParser implicit tags method ", e)

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)

        try:
            while len(self.unfinished) > 1:
                node = self.unfinished.pop()
                parent = self.unfinished[-1]
                parent.children.append(node)
            return self.unfinished.pop()

        except Exception as e:
            print("Error at HTMLParser finish method ", e)
