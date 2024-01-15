import tkinter


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


def layout(text, width):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    lines = text.split("\n")

    for line in lines:
        words = line.split()
        for word in words:
            word_width = len(word) * HSTEP

            # Check if the word fits in the remaining line, wrap otherwise
            if cursor_x + word_width >= width:
                cursor_y += VSTEP
                cursor_x = HSTEP

            # Add each character of the word to the display list
            for char in word:
                display_list.append((cursor_x, cursor_y, char))
                cursor_x += HSTEP

            # Space after the word
            if cursor_x + HSTEP < width:
                cursor_x += HSTEP

        # New line and potential paragraph break
        cursor_y += VSTEP * 1.2  # Paragraph breaks
        cursor_x = HSTEP

    return display_list


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        # self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack(fill="both", expand=True)
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.wheelscroll)
        self.window.bind("<Configure>", self.on_resize)
        self.current_text = ""

    def load(self, url):
        """Send the request, recieve and show body."""

        try:
            body = url.request()
            text = lex(body)
            self.current_text = text
            self.display_list = layout(text, WIDTH)
            self.draw()

            return True
        except Exception as e:
            print("Error at load method on Browser: ", e)
            print("Failed to load", url)
            return False

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, (y - self.scroll), text=c)

    def on_resize(self, event):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = event.width, event.height
        if self.current_text:
            self.display_list = layout(self.current_text, WIDTH)
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
