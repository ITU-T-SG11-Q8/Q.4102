import threading


def hello(text, cc):
    print(text)
    print(cc)


if __name__ == '__main__':
    t = threading.Timer(2, hello, ["bb", "cc"])
    t.start()
