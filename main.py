import tkinter


WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
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


def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    words = text.split()

    for word in words:
        word_width = len(word) * HSTEP

        # Check if the word fits in the remaining line, wrap otherwise
        if cursor_x + word_width >= WIDTH:
            cursor_y += VSTEP
            cursor_x = HSTEP

        # Add each character of the word to the display list
        for char in word:
            display_list.append((cursor_x, cursor_y, char))
            cursor_x += HSTEP

        # Add space after the word
        if cursor_x + HSTEP < WIDTH:
            cursor_x += HSTEP

    return display_list


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)

    def load(self, url):
        """Send the request, recieve and show body."""

        try:
            body = url.request()
            text = lex(body)
            self.display_list = layout(text)
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
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()


if __name__ == "__main__":
    import sys
    from url import URL

    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
