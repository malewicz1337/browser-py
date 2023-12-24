import socket
import ssl
import base64
import mimetypes
import os


class URL:
    def __init__(
        self, url="file:///path/to/default/testfile.html"
    ):  # default file path
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file", "data"]

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

    def request(self):
        if self.scheme in ["http", "https"]:
            s = socket.socket(
                family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
            )
            s.connect((self.host, self.port))

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)

            request_headers = (
                f"GET {self.path} HTTP/1.0\r\n"
                f"Host: {self.host}\r\n"
                "Connection: close\r\n"
                "Accept: */*\r\n"
                "User-Agent: mlwcz\r\n"
            )
            s.send(request_headers.encode("utf8"))

            response = s.makefile("r", encoding="utf8", newline="\r\n")
            statusline = response.readline()
            version, status, explanation = statusline.split(" ", 2)

            response_headers = {}
            while True:
                line = response.readline()
                if line == "\r\n":
                    break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers

            content_type = response_headers.get("content-type", "")
            encoding = "utf8"
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].split(";")[0]

            body = response.read().decode(encoding)
            s.close()
            return body

        elif self.scheme == "file":
            with open(self.path, "r") as file:
                return file.read()

        elif self.scheme == "data":
            mime_type, data_string = self.data.split(",", 1)
            if ";base64" in mime_type:
                return base64.b64decode(data_string).decode("utf8")
            else:
                return data_string
