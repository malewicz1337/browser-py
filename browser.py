import tkinter
from dom.element import Element

from dom.layout import DocumentLayout
from dom.htmlparser import HTMLParser
from cssom.cssparser import style
from dom.text import Text

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
cursor_x, cursor_y = HSTEP, VSTEP
SCROLL_STEP = 10


def paint_tree(layout_object, display_list):
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)


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
            self.save_html()
            style(self.nodes)
            self.document = DocumentLayout(self.nodes)
            self.document.layout()
            self.display_list = []
            paint_tree(self.document, self.display_list)
            self.draw()
            return True

        except Exception as e:
            print("Error at load method on Browser: ", e)
            self.load("about:blank")
            return False

    def serialize_node(self, node):
        if isinstance(node, Text):
            return node.text
        elif isinstance(node, Element):
            html = f"<{node.tag}"

            if node.attributes:
                for attr, value in node.attributes.items():
                    html += f' {attr}="{value}"'

            html += ">"

            for child in node.children:
                html += self.serialize_node(child)  # type: ignore

            html += f"</{node.tag}>"

            return html

    def save_html(self):
        if not self.nodes:
            return False

        html_content = self.serialize_node(self.nodes)

        with open("./output.html", "w", encoding="utf-8") as file:
            file.write(html_content)  # type: ignore

        return True

    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)

    def on_resize(self, event):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = event.width, event.height
        if self.nodes:
            self.document = DocumentLayout(self.nodes)
            self.document.layout()
            self.display_list = []
            paint_tree(self.document, self.display_list)
            self.draw()

    def scrolldown(self, e):
        max_y = max(self.document.height or 0 + 2 * VSTEP - HEIGHT, 0)
        print("Scrolling down, current scroll:", self.scroll, "max_y:", max_y)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
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

        scroll_speed = SCROLL_STEP
        max_y = max(self.document.height or 0 + 2 * VSTEP - HEIGHT, 0)

        self.scroll -= delta * scroll_speed
        self.scroll = max(0, min(self.scroll, max_y))

        self.draw()
