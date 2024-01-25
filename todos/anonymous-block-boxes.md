```bash
class DocumentLayout:
    def layout(self):
        # ......
        self.layout_children(self.node, self)

    def layout_children(self, node, parent_layout):
        children = node.children
        inline_buffer = []

        for child in children:
            if isinstance(child, Element) and child.tag in BLOCK_ELEMENTS:
                if inline_buffer:
                    inline_layout = BlockLayout(inline_buffer, parent_layout, None)
                    parent_layout.children.append(inline_layout)
                    inline_layout.layout()
                    inline_buffer = []

                block_layout = BlockLayout(child, parent_layout, None)
                parent_layout.children.append(block_layout)
                block_layout.layout()
            else:
                # Buffer inline elements
                inline_buffer.append(child)

        if inline_buffer:
            inline_layout = BlockLayout(inline_buffer, parent_layout, None)
            parent_layout.children.append(inline_layout)
            inline_layout.layout()

class BlockLayout:
    def __init__(self, nodes, parent, previous):
        # ......
        if not isinstance(nodes, list):
            nodes = [nodes]
        self.nodes = nodes
        # ......

    def layout(self):
        # ......
        mode = self.layout_mode()
        if mode == "block":
        # ......
        else:
            # Handle inline nodes in the sequence
            for node in self.nodes:
                self.recurse(node)
            self.flush()
        # ......

    def layout_mode(self):
        # Modify to check all nodes in the sequence
        if any(isinstance(node, Text) for node in self.nodes):
            return "inline"
        elif any(node.tag in BLOCK_ELEMENTS for node in self.nodes if isinstance(node, Element)):
            return "block"
        else:
            return "block"
```
