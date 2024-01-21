import tkinter.font
from dom.text import Text

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
cursor_x, cursor_y = HSTEP, VSTEP
FONTS = {}


def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)
        child.layout()
        self.display_list = child.display_list


class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        self.display_list = []
        self.line = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.centering = False

        self.flush()
        self.recurse(self.node)

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
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP
        elif tag == "br":
            self.flush()
        elif tag == "h1":
            self.flush()
            self.centering = True
            self.size += 10

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

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        word_width = font.measure(word)
        space_width = font.measure(" ")

        if self.centering:
            line_width = (
                sum(font.measure(word) for _x, word, font in self.line)
                + len(self.line) * space_width
            )
            if self.line:
                line_width += space_width
            line_width += word_width

            centered_x = (WIDTH - line_width) // 2
            self.cursor_x = max(HSTEP, centered_x)

        if self.cursor_x + word_width > WIDTH - HSTEP:
            self.flush()

        # *: Yes, I actually need this)))
        if self.line and self.cursor_x + word_width + space_width > WIDTH - HSTEP:
            self.flush()

        if self.cursor_x + word_width + space_width > WIDTH - HSTEP:
            self.cursor_y += font.metrics("linespace") * 1.25
            self.cursor_x = HSTEP

        self.line.append((self.cursor_x, word, font))

        self.cursor_x += word_width + space_width
