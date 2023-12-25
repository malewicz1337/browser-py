import threading
import time
import socket
import ssl


class Sockets:
    sockets = {}

    @classmethod
    def get_socket(cls, scheme, host, port):
        key = (scheme, host, port)
        if key not in cls.sockets or cls.sockets[key] is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))

            if scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=host)

            cls.sockets[key] = (s, time.time())
        return cls.sockets[key][0]

    @staticmethod
    def close_idle_sockets(idle_time=300):  # idle time in seconds
        current_time = time.time()
        for key, (socket, last_used) in list(Sockets.sockets.items()):
            if current_time - last_used > idle_time:
                socket.close()
                del Sockets.sockets[key]

    @staticmethod
    def start_socket_cleaner(interval=300):  # interval in seconds
        def cleaner():
            while True:
                Sockets.close_idle_sockets(interval)
                time.sleep(interval)

        thread = threading.Thread(target=cleaner, daemon=True)
        thread.start()

    @classmethod
    def close_socket(cls, scheme, host, port):
        key = (scheme, host, port)
        if key in cls.sockets:
            socket, last_used = cls.sockets[key]
            socket.close()
            del cls.sockets[key]

    @classmethod
    def close_all(cls):
        for key, (socket, last_used) in list(cls.sockets.items()):
            socket.close()
            del cls.sockets[key]
        cls.sockets = {}
