import tkinter
import tkinter.font

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 8, 14
cursor_x, cursor_y = HSTEP, VSTEP
SCROLL_STEP = 100


def lex(body):
    """Remove html tags from body and return text only."""

    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c

    return text


def layout(text, font):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP

    lines = text.split("\n")

    for line in lines:
        words = line.split()
        for word in words:
            w = font.measure(word)

            # Check if the word will exceed the line width
            if cursor_x + w >= WIDTH - HSTEP:
                cursor_y += font.metrics("linespace") * 1.25
                cursor_x = HSTEP

            # Add the word to the display list
            display_list.append((cursor_x, cursor_y, word))
            cursor_x += w + font.measure(" ")

        # Move to the next line after each line of text
        # cursor_y += font.metrics("linespace") * 1.25
        # cursor_x = HSTEP

    return display_list


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
        self.current_text = ""

        self.bi_times = tkinter.font.Font(
            family="Times",
            size=16,
            weight="normal",
            slant="roman",
        )

    def load(self, url):
        """Send the request, recieve and show body."""

        if url == "about:blank":
            self.current_text = ""
            self.display_list = []
            self.draw()
            return True

        try:
            body = url.request()
            text = lex(body)
            self.current_text = text
            self.display_list = layout(text, self.bi_times)
            self.draw()

            return True

        except Exception as e:
            print("Error at load method on Browser: ", e)
            print("Failed to load", url)
            self.load("about:blank")
            return False

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, (y - self.scroll), text=c, font=self.bi_times)

    def on_resize(self, event):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = event.width, event.height
        if self.current_text:
            self.display_list = layout(self.current_text, self.bi_times)
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
