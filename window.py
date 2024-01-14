import tkinter

from url import URL

WIDTH, HEIGHT = 800, 600


class Window:
    """Some docstring"""

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()

    def load(self, url):
        """Loads some shapes"""
        self.canvas.create_rectangle(10, 20, 400, 300)
        self.canvas.create_oval(100, 100, 150, 150)
        self.canvas.create_text(200, 150, text="Hello")


if __name__ == "__main__":
    import sys

    Window().load(URL())
    tkinter.mainloop()
