from dom.element import Element


def style(node):

    if isinstance(node, Element) and "style" in node.attributes:
        try:
            pairs = CSSParser(node.attributes["style"]).body()
            for property, value in pairs.items():
                node.style[property] = value

        except Exception as e:
            print(f"Error parsing CSS for node: {e}")

    for child in node.children:
        style(child)


class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        if not (self.i > start):
            raise Exception(
                f"Parsing error: Expected a word at position {self.i} in '{self.s}'"
            )
        return self.s[start : self.i]

    def literal(self, literal):
        if not (self.i < len(self.s) and self.s[self.i] == literal):
            raise Exception(
                f"Parsing error: Expected '{literal}' at position {self.i} in '{self.s}'"
            )
        self.i += 1

    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.casefold(), val

    def body(self):
        pairs = {}
        while self.i < len(self.s):
            try:
                prop, val = self.pair()
                pairs[prop.casefold()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()

            # todo: handle errors more gracefully)
            except Exception as e:
                # print(f"Error at CSSParser body method: {e}")
                why = self.ignore_until([";"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break

        return pairs

    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
        return None
