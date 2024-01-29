import tkinter.font
from dom.text import Text
from dom.element import Element
from cssom.cssparser import CSSParser

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
cursor_x, cursor_y = HSTEP, VSTEP
FONTS = {}

BLOCK_ELEMENTS = [
    "html",
    "body",
    "article",
    "section",
    "nav",
    "aside",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hgroup",
    "header",
    "footer",
    "address",
    "p",
    "hr",
    "pre",
    "blockquote",
    "ol",
    "ul",
    "menu",
    "li",
    "dl",
    "dt",
    "dd",
    "figure",
    "figcaption",
    "main",
    "div",
    "table",
    "form",
    "fieldset",
    "legend",
    "details",
    "summary",
]


def get_font(size, weight, slant, family="Times"):
    key = (size, weight, slant, family)
    if key not in FONTS:
        font = tkinter.font.Font(family=family, size=size, weight=weight, slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class DrawText:
    def __init__(self, x1, y1, text, font):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll, text=self.text, font=self.font, anchor="nw"
        )


class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            width=0,
            fill=self.color,
        )


class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.previous = None
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)

        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height

        self.display_list = child.display_list

    def paint(self):
        return []


class BlockLayout:
    def __init__(self, node, parent, previous):
        self.x = None
        self.y = None
        self.width = None
        self.height = None

        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.display_list = []

    def layout(self):
        if isinstance(self.node, Element) and self.node.tag == "head":
            return

        self.x = self.parent.x
        self.width = self.parent.width

        if self.previous:
            if self.previous.y is not None and self.previous.height is not None:
                self.y = self.previous.y + self.previous.height
            else:
                self.y = self.parent.y
        else:
            self.y = self.parent.y

        mode = self.layout_mode()
        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else:
            self.cursor_x = 0
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 16
            self.centering = False
            self.in_pre = False

            self.line = []
            self.recurse(self.node)
            self.flush()

        for child in self.children:
            child.layout()

        if mode == "block":
            self.height = sum(
                child.height for child in self.children if child.height is not None
            )
        else:
            self.height = self.cursor_y

    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        elif any(
            [
                isinstance(child, Element) and child.tag in BLOCK_ELEMENTS
                for child in self.node.children
            ]
        ):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"

    def layout_intermediate(self):
        previous = None
        for child in self.node.children:
            next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next

    def recurse(self, tree):
        if isinstance(tree, Text):
            # if self.in_pre:
            #     for char in tree.text:
            #         if char == "\n":
            #             self.flush()
            #             self.cursor_y += VSTEP
            #             self.cursor_x = 0
            #         elif char.isspace():
            #             self.word(" ")
            #         else:
            #             self.word(char)

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

        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])

        baseline = self.cursor_y + 1.25 * max_ascent

        if self.centering:
            line_width = sum(font.measure(word) for _x, word, font in self.line)
            line_width += (len(self.line) - 1) * font.measure(" ")

            centered_x = (WIDTH - line_width) // 2
            temp_cursor_x = max(HSTEP, centered_x)

            for x, word, font in self.line:
                y = self.y + baseline - font.metrics("ascent")
                self.display_list.append((temp_cursor_x, y, word, font))
                temp_cursor_x += font.measure(word) + font.measure(" ")

        else:
            for rel_x, word, font in self.line:
                x = self.x + rel_x
                y = self.y + baseline - font.metrics("ascent")
                self.display_list.append((x, y, word, font))

        self.cursor_x = 0
        self.line = []

        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

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
        elif tag == "pre":
            self.flush()
            self.in_pre = True
            self.font_family = "Courier"
        elif tag == "code":
            self.font_family = "Courier"

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
        elif tag == "pre":
            self.flush()
            self.in_pre = False
            self.font_family = "Times"
        elif tag == "code":
            self.font_family = "Times"

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

            centered_x = (self.width - line_width) // 2
            self.cursor_x = max(HSTEP, centered_x)

        # if self.in_pre:
        #     if self.cursor_x + word_width > self.width:
        #         self.flush()
        #         self.cursor_y += VSTEP
        #         self.cursor_x = 0

        #     self.line.append((self.cursor_x, word, font))
        #     self.cursor_x += word_width

        if self.cursor_x + word_width > self.width:
            self.flush()

        self.line.append((self.cursor_x, word, font))
        self.cursor_x += word_width + space_width

    def paint(self):
        cmds = []

        if isinstance(self.node, Element) and self.node.tag == "pre":
            x2, y2 = self.x + self.width, self.y + self.height  # type: ignore
            rect = DrawRect(self.x, self.y, x2, y2, "gray")
            print("pre")
            cmds.append(rect)

        if self.layout_mode() == "inline":
            for x, y, word, font in self.display_list:
                text_cmd = DrawText(x, y, word, font)
                cmds.append(text_cmd)

        bgcolor = self.node.style.get("background-color", "transparent")

        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height  # type: ignore
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            print(rect)
            cmds.append(rect)

        return cmds
