import tkinter
import tkinter.font

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
cursor_x, cursor_y = HSTEP, VSTEP
SCROLL_STEP = 100
FONTS = {}


def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class Text:
    def __init__(self, text):
        self.text = text


class Tag:
    def __init__(self, tag):
        self.tag = tag


def lex(body):
    """Remove html tags from body and return text only."""

    out = []
    buffer = ""
    in_tag = False

    for c in body:
        if c == "<":
            in_tag = True
            if buffer:
                out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c

    if not in_tag and buffer:
        out.append(Text(buffer))

    return out


class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.line = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.flush()

        for tok in tokens:
            self.token(tok)

    def flush(self):
        if not self.line:
            return

        max_ascent = max([font.metrics("ascent") for x, word, font in self.line])
        max_descent = max([font.metrics("descent") for x, word, font in self.line])

        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []

    def token(self, tok):
        if isinstance(tok, Text):
            # font = tkinter.font.Font(size=self.size, weight=self.weight, slant=self.style)  # type: ignore

            for word in tok.text.split():
                self.word(word)

            # self.cursor_y += (
            #     font.metrics("linespace") * 1.25
            # )  # Add space after each line
            # self.cursor_x = HSTEP

        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        word_width = font.measure(word)
        space_width = font.measure(" ")

        if self.cursor_x + word_width > WIDTH - HSTEP:
            self.flush()

        if self.cursor_x + word_width + space_width > WIDTH - HSTEP:
            self.cursor_y += font.metrics("linespace") * 1.25  # Move to next line
            self.cursor_x = HSTEP

        self.display_list.append((self.cursor_x, self.cursor_y, word, font))
        self.cursor_x += word_width + space_width  # Add space after each word
        self.line.append((self.cursor_x, word, font))


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack(fill="both", expand=True)
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.wheelscroll)
        self.window.bind("<Configure>", self.on_resize)
        self.current_tokens = ""

    def load(self, url):
        """Send the request, recieve and show body."""

        if url == "about:blank":
            self.display_list = []
            self.draw()
            return True

        try:
            body = url.request()
            tokens = lex(body)
            self.current_tokens = tokens
            self.display_list = Layout(tokens).display_list
            self.draw()

            return True

        except Exception as e:
            print("Error at load method on Browser: ", e)
            print("Failed to load", url)
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
        self.display_list = Layout(self.current_tokens).display_list
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

        scroll_speed = 50
        self.scroll -= delta * scroll_speed

        # Boundary check
        self.scroll = max(0, min(self.scroll, len(self.display_list) * VSTEP - HEIGHT))

        self.draw()


if __name__ == "__main__":
    import sys
    from url import URL

    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
