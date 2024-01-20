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
        # self.superscript = False
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
            font = tkinter.font.Font(
                size=self.size, weight="normal", slant="roman", family="Courier New"
            )

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
