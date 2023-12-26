def show(body):
    """Remove html tags from body and print text only."""

    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")


def load(url):
    """Send the request, recieve and show body."""

    try:
        body = url.request()
        show(body)
        return True
    except Exception as e:
        print(e)
        print("Failed to load", url)
        return False


if __name__ == "__main__":
    import sys
    from url import URL

    load(URL(sys.argv[1]))
