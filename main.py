from ast import Try
import tkinter
import tkinter.font

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
cursor_x, cursor_y = HSTEP, VSTEP
SCROLL_STEP = 100
FONTS = {}


def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.children = []
        self.parent = parent
        self.attributes = attributes

    def __repr__(self):
        return "<" + self.tag + ">"


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
            parent = self.unfinished[-1]
            node = Text(text, parent)
            parent.children.append(node)
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
                parent = self.unfinished[-1]
                node = Element(tag, attributes, parent)
                parent.children.append(node)

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


class Layout:
    def __init__(self, nodes):
        self.display_list = []
        self.line = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.centering = False
        self.superscript = False
        self.pre = False
        self.abbr = False

        self.flush()

        self.recurse(nodes)

    def recurse(self, tree):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

    def flush(self):
        if not self.line:
            return

        font = get_font(self.size, self.weight, self.style)

        max_ascent = max([font.metrics("ascent") for _x, _word, font in self.line])
        baseline = self.cursor_y + 1.25 * max_ascent

        if self.centering:
            line_width = sum(font.measure(word) for _x, word, font in self.line)
            line_width += (len(self.line) - 1) * font.measure(" ")

            centered_x = (WIDTH - line_width) // 2
            temp_cursor_x = max(HSTEP, centered_x)

            for x, word, font in self.line:
                y = baseline - font.metrics("ascent")
                self.display_list.append((temp_cursor_x, y, word, font))
                temp_cursor_x += font.measure(word) + font.measure(" ")

        else:
            for x, word, font in self.line:
                y = baseline - font.metrics("ascent")
                self.display_list.append((x, y, word, font))

        max_descent = max([font.metrics("descent") for _x, _word, font in self.line])

        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()
        elif tag == "h1":
            self.flush()
            self.centering = True
            self.size += 10
        # elif tag == "sup":
        #     self.flush()
        #     self.superscript = True
        #     self.size = self.size // 2
        elif tag == "pre":
            self.flush()
            self.pre = True
            self.weight = "bold"
            self.style = "roman"
            self.size = 16

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP
        elif tag == "h1":
            self.flush()
            self.centering = False
            self.size -= 10
        # elif tag == "sup":
        #     self.flush()
        #     self.superscript = False
        #     self.size = self.size * 2
        elif tag == "pre":
            self.flush()
            self.pre = False
            self.weight = "bold"
            self.style = "roman"
            self.size = 16

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        word_width = font.measure(word)
        space_width = font.measure(" ")

        if self.pre:
            font = tkinter.font.Font(size=self.size, weight=self.weight, slant=self.style, family="Courier New")  # type: ignore

            for char in word:
                char_width = font.measure(char)
                if char == "\n":
                    self.flush()
                    self.cursor_y += font.metrics("linespace") * 1.25
                    self.cursor_x = HSTEP
                    continue

                if self.cursor_x + char_width > WIDTH - HSTEP:
                    self.flush()
                    self.cursor_y += font.metrics("linespace") * 1.25
                    self.cursor_x = HSTEP

                self.line.append((self.cursor_x, char, font))
                self.cursor_x += char_width

        elif self.abbr:
            for char in word:
                if char.islower():
                    small_cap_font = get_font(self.size, "bold", "roman")
                    self.line.append((self.cursor_x, char.upper(), small_cap_font))
                else:
                    font = get_font(self.size, self.weight, self.style)
                    self.line.append((self.cursor_x, char, font))

                char_width = font.measure(char)
                self.cursor_x += char_width

        else:
            if self.centering:
                line_width = (
                    sum(font.measure(w) for _, w, _ in self.line)
                    + len(self.line) * space_width
                )
                if self.line:
                    line_width += space_width
                line_width += word_width

                centered_x = (WIDTH - line_width) // 2
                self.cursor_x = max(HSTEP, centered_x)

            if self.cursor_x + word_width > WIDTH - HSTEP:
                self.flush()

            # *: Do I even need this ?
            if self.line and self.cursor_x + word_width + space_width > WIDTH - HSTEP:
                self.flush()

            if self.cursor_x + word_width + space_width > WIDTH - HSTEP:
                self.cursor_y += font.metrics("linespace") * 1.25
                self.cursor_x = HSTEP

            # if self.superscript:
            #     ascent = font.metrics("ascent")
            #     normal_font = get_font(self.size * 2, self.weight, self.style)
            #     normal_ascent = normal_font.metrics("ascent")
            #     y_offset = normal_ascent - ascent
            # else:
            #     y_offset = 0

            self.line.append((self.cursor_x, word, font))

            self.cursor_x += word_width + space_width


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack(fill="both", expand=True)
        self.scroll = 0
        self.nodes = None
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.wheelscroll)
        self.window.bind("<Configure>", self.on_resize)

    def load(self, url):
        if url == "about:blank":
            self.display_list = []
            self.draw()
            return True

        try:
            body = url.request()
            self.nodes = HTMLParser(body).parse()
            self.display_list = Layout(self.nodes).display_list
            self.draw()
            return True

        except Exception as e:
            print("Error at load method on Browser: ", e)
            self.load("about:blank")
            return False

    def draw(self):
        self.canvas.delete("all")
        for x, y, text, font in self.display_list:
            if y > self.scroll + HEIGHT or y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(
                x, (y - self.scroll), text=text, font=font, anchor="nw"
            )

    def on_resize(self, event):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = event.width, event.height
        if self.nodes:
            self.display_list = Layout(self.nodes).display_list
            self.draw()

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.scroll = min(self.scroll, len(self.display_list) * VSTEP - HEIGHT)
        self.draw()

    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        self.scroll = max(0, self.scroll)
        self.draw()

    def wheelscroll(self, e):
        delta = e.delta
        if self.window.tk.call("tk", "windowingsystem") == "win32":
            delta //= 120
        elif self.window.tk.call("tk", "windowingsystem") == "aqua":
            delta //= 3

        scroll_speed = 100
        self.scroll -= delta * scroll_speed

        # Boundary check
        self.scroll = max(0, min(self.scroll, len(self.display_list) * VSTEP - HEIGHT))

        self.draw()


if __name__ == "__main__":
    import sys
    from url import URL

    if len(sys.argv) > 1:
        Browser().load(URL(sys.argv[1]))
    else:
        Browser().load(URL())

    tkinter.mainloop()
