import socket
import ssl
import base64
import html
import time
import threading


class URL:
    sockets = {}

    def __init__(
        self, url="file:///path/to/default/testfile.html"
    ):  # default file path
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file", "data"]

        self.view_source = False
        if url.startswith("view-source:"):
            self.view_source = True
            url = url[len("view-source:") :]

        if self.scheme in ["http", "https"]:
            self.port = 80 if self.scheme == "http" else 443

            if "/" not in url:
                url = url + "/"

            self.host, url = url.split("/", 1)
            self.path = "/" + url

            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)

        elif self.scheme == "file":
            self.path = url  # Local file path

        elif self.scheme == "data":
            self.data = url  # Data embedded in URL

    def decode_html_entities(self, text):
        """
        Decode HTML entities in the text.
        """
        return html.unescape(text)

    def read_chunked(self, response):
        body_chunks = []
        while True:
            chunk_size_str = response.readline().strip()
            chunk_size = int(chunk_size_str, 16) if chunk_size_str else 0
            if chunk_size == 0:
                break  # End of chunks
            chunk = response.read(chunk_size)
            response.readline()  # Consume trailing newline
            body_chunks.append(chunk)
        return b"".join(body_chunks)

    def get_socket(self):
        key = (self.scheme, self.host, self.port)
        if key not in self.sockets or self.sockets[key] is None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)

            self.sockets[key] = (s, time.time())
        return self.sockets[key][0]

    def request(self):
        if self.scheme in ["http", "https"]:
            s = self.get_socket()

            request_headers = (
                f"GET {self.path} HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                # "Connection: close\r\n"
                "Accept: */*\r\n"
                "User-Agent: mlwcz\r\n"
            )
            s.send(request_headers.encode("utf8"))

            response = s.makefile("r", encoding="utf8", newline="\r\n")
            statusline = response.readline()
            version, status, explanation = statusline.split(" ", 2)

            response_headers = {}
            content_length = None

            while True:
                line = response.readline()
                if line == "\r\n":
                    break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()
                if header.casefold() == "content-length":
                    content_length = int(value.strip())

            assert (
                "transfer-encoding" not in response_headers
            ), "Transfer-Encoding is not supported"
            assert (
                "content-encoding" not in response_headers
            ), "Content-Encoding is not supported"

            content_type = response_headers.get("content-type", "")
            encoding = "utf8"
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].split(";")[0]

            if (
                "transfer-encoding" in response_headers
                and response_headers["transfer-encoding"] == "chunked"
            ):
                raw_body = self.read_chunked(response)
            else:
                assert content_length is not None, "Content-Length header is missing"
                raw_body = response.read(content_length)

            decoded_body = raw_body.decode(encoding)

            key = (self.scheme, self.host, self.port)
            if response_headers.get("connection") == "close":
                s.close()
                self.sockets[key] = None

            if self.view_source:
                # Return raw HTML for view-source
                return decoded_body
            else:
                # Decode HTML entities for normal viewing
                return self.decode_html_entities(decoded_body)

        elif self.scheme == "file":
            with open(self.path, "r") as file:
                content = file.read()

            if self.view_source:
                return content
            else:
                return self.decode_html_entities(content)

        elif self.scheme == "data":
            mime_type, data_string = self.data.split(",", 1)

            if self.view_source:
                if ";base64" in mime_type:
                    return base64.b64decode(data_string).decode("utf8")
                else:
                    return data_string
            else:
                if ";base64" in mime_type:
                    return base64.b64decode(data_string).decode("utf8")
                else:
                    return self.decode_html_entities(data_string)

    @staticmethod
    def close_idle_sockets(idle_time=300):  # idle time in seconds
        current_time = time.time()
        for key, (socket, last_used) in list(URL.sockets.items()):
            if current_time - last_used > idle_time:
                socket.close()
                del URL.sockets[key]

    @staticmethod
    def start_socket_cleaner(interval=300):  # interval in seconds
        def cleaner():
            while True:
                URL.close_idle_sockets(interval)
                time.sleep(interval)

        thread = threading.Thread(target=cleaner, daemon=True)
        thread.start()
