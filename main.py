def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")


def load(url):
    try:
        body = url.request()
        show(body)
    except Exception as e:
        print(e)
        print("Failed to load", url)
        return False


if __name__ == "__main__":
    import sys
    from url import URL

    load(URL(sys.argv[1]))
