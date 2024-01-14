import tkinter


def lex(body):
    """Remove html tags from body and print text only."""

    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            # print(c, end="")
            text += c

    return text


WIDTH, HEIGHT = 800, 600


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

    def load(self, url):
        """Send the request, recieve and show body."""

        try:
            body = url.request()
            text = lex(body)

            HSTEP, VSTEP = 13, 18
            cursor_x, cursor_y = HSTEP, VSTEP
            for c in text:
                self.canvas.create_text(cursor_x, cursor_y, text=c)
                cursor_x += HSTEP

                if cursor_x >= WIDTH - HSTEP:
                    cursor_y += VSTEP
                    cursor_x = HSTEP

            return True
        except Exception as e:
            print(e)
            print("Failed to load", url)
            return False


if __name__ == "__main__":
    import sys
    from url import URL

    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()
