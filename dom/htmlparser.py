from dom.text import Text
from dom.element import Element

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

FORMATTING_TAGS = ["b", "i", "em", "strong", "u"]


class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def parse(self):
        text = ""
        in_tag = False
        in_comment = False
        in_script = False
        in_quote = False
        quote_char = None

        for i in range(len(self.body)):
            c = self.body[i]

            if in_quote:
                if c == quote_char:
                    in_quote = False
                text += c
                continue

            if c == "<" and not in_script and not in_tag:
                if self.body[i : i + 7].lower() == "<script":
                    in_script = True
                    self.add_tag("script")
                    continue

            if in_script:
                if c == "<" and self.body[i : i + 9].lower() == "</script>":
                    in_script = False
                    self.add_tag("/script")
                    i += 8
                    continue
                else:
                    text += c
                    continue

            if c == "<" and not in_comment:
                next_chars = self.body[i : i + 4]
                if next_chars == "<!--":
                    in_comment = True
                    i += 3
                    continue

            if in_comment:
                next_chars = self.body[i : i + 3]
                if next_chars == "-->":
                    in_comment = False
                    i += 2
                    continue

            if in_comment:
                continue

            if in_tag:
                if c == ">" and not in_quote:
                    in_tag = False
                    self.add_tag(text)
                    text = ""
                elif c in ['"', "'"]:
                    in_quote = True
                    quote_char = c
                    text += c
                else:
                    text += c
                continue

            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            else:
                text += c

        if not in_tag and text:
            self.add_text(text)

        return self.finish()

    def get_attributes(self, text):
        parts = text.split()

        if not parts:
            return "", {}

        tag = parts[0].casefold()
        attributes = {}

        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)

                if len(value) > 2 and value[0] in ["'", '"']:
                    value = value[1:-1]

                attributes[key.casefold()] = value

            else:
                attributes[attrpair.casefold()] = ""

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

        if tag in ["p", "li"]:
            self.close_open_tags(tag)

        if tag.startswith("/"):
            self.close_tag(tag)

        elif tag in SELF_CLOSING_TAGS:
            if self.unfinished:
                parent = self.unfinished[-1]
                node = Element(tag, attributes, parent)
                parent.children.append(node)
            else:
                print("No unfinished in add tag 2")
                pass

        else:
            if self.unfinished:
                parent = self.unfinished[-1]
            else:
                parent = None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def close_open_tags(self, new_tag):
        while self.unfinished and self.unfinished[-1].tag in ["p", "li"]:
            if self.unfinished[-1].tag != new_tag or new_tag == "li":
                break
            self.close_tag(self.unfinished[-1].tag)

    def close_tag(self, tag):
        if len(self.unfinished) == 1:
            return
        if self.unfinished:
            expected_tag = tag[1:]
            if expected_tag in FORMATTING_TAGS:
                self.handle_misnested_tags(expected_tag)
            else:
                node = self.unfinished.pop()
                if self.unfinished:
                    parent = self.unfinished[-1]
                    parent.children.append(node)

    def handle_misnested_tags(self, expected_tag):
        if self.unfinished:
            index = None
            for i in range(len(self.unfinished) - 1, -1, -1):
                if self.unfinished[i].tag == expected_tag:
                    index = i
                    break

            if index is not None:
                misnested_tags = []
                while len(self.unfinished) > index:
                    node = self.unfinished.pop()
                    if node.tag in FORMATTING_TAGS:
                        misnested_tags.append(node.tag)
                    if self.unfinished:
                        parent = self.unfinished[-1]
                        parent.children.append(node)

                for tag in reversed(misnested_tags):
                    self.add_tag(tag)

    def implicit_tags(self, tag):
        try:
            while True:
                open_tags = [node.tag for node in self.unfinished]
                if open_tags == [] and tag != "html":
                    self.add_tag("html")
                elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                    if tag in HEAD_TAGS:
                        self.add_tag("head")
                    else:
                        self.add_tag("body")
                elif open_tags == ["html", "head"] and tag not in ["/head"] + HEAD_TAGS:
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
                if self.unfinished:
                    parent = self.unfinished[-1]
                    parent.children.append(node)

            if self.unfinished:
                return self.unfinished.pop()
            else:
                return None

        except Exception as e:
            print("Error at HTMLParser finish method ", e)
