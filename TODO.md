# TODO List

### dom

- Add support for tags: pre, abbr, sup
- Position content in the center

## Tasks

- **Bullets:** Add bullets to list items, which in HTML are <li> tags. Make them little squares, located to the left of the list item itself. Also indent <li> elements so the text inside the element is to the right of the bullet point.

- **Anonymous block boxes:** Sometimes, an element has a mix of text-like and container-like children. For example, in this HTML,

<div><i>Hello, </i><b>world!</b><p>So it began...</p></div>

the <div> element has three children: the <i>, <b>, and <p> elements. The first two are text-like; the last is container-like. This is supposed to look like two paragraphs, one for the <i> and <b> and the second for the <p>. Modify BlockLayout so it can be passed a sequence of sibling nodes, instead of a single node. Then, modify the algorithm that constructs the layout tree so that any sequence of text-like elements gets made into a single BlockLayout.

[Test Implementation](./todos/anonymous-block-boxes.md)

- **Run-ins:** A “run-in heading” is a heading that is drawn as part of the next paragraph’s text. Modify browser to render <h6> elements as run-in headings.

- **Special tags:** Add proper handling for <pre> and <code> tags.
