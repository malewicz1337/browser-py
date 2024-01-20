if __name__ == "__main__":
    import sys
    import tkinter
    from network.url import URL
    from browser import Browser

    if len(sys.argv) > 1:
        Browser().load(URL(sys.argv[1]))
    else:
        Browser().load(URL())

    tkinter.mainloop()
