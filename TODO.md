# TODO List

### dom

- Add support for tags: pre, abbr, sup
- Position content in the center

## Tasks

- **Bullets:** Add bullets to list items, which in HTML are <li> tags. You can make them little squares, located to the left of the list item itself. Also indent <li> elements so the text inside the element is to the right of the bullet point.

- **Anonymous block boxes:** Sometimes, an element has a mix of text-like and container-like children. For example, in this HTML,

<div><i>Hello, </i><b>world!</b><p>So it began...</p></div>

the <div> element has three children: the <i>, <b>, and <p> elements. The first two are text-like; the last is container-like. This is supposed to look like two paragraphs, one for the <i> and <b> and the second for the <p>. Make your browser do that. Specifically, modify BlockLayout so it can be passed a sequence of sibling nodes, instead of a single node. Then, modify the algorithm that constructs the layout tree so that any sequence of text-like elements gets made into a single BlockLayout.

[Test Implementation](./todos/anonymous-block-boxes.md)
