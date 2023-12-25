import base64
import html
from sockets import Sockets


class URL:
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
        chunked_body = b""
        while True:
            line = response.readline()
            if line == b"\r\n":
                break
            chunk_size = int(line, 16)
            if chunk_size == 0:
                break
            chunked_body += response.read(chunk_size)
            response.read(2)  # discard CRLF at the end of the chunk
        return chunked_body

    def request(self, redirect_limit=10):
        if self.scheme in ["http", "https"]:
            s = Sockets.get_socket(self.scheme, self.host, self.port)

            request_headers = (
                f"GET {self.path} HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                "Connection: keep-alive\r\n"
                "Accept: */*\r\n"
                "User-Agent: mlwcz\r\n\r\n"
            )

            print("Sending request headers...")
            s.send(request_headers.encode("utf8"))

            response = s.makefile("r", encoding="utf8", newline="\r\n")
            statusline = response.readline()
            version, status, explanation = statusline.split(" ", 2)
            status_code = int(status)

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

            # Check if it's a redirect
            if 300 <= status_code < 400:
                location = response_headers.get("location")
                if not location:
                    raise Exception("Redirect location not provided")

                # Handle relative redirect
                if location.startswith("/"):
                    location = f"{self.scheme}://{self.host}:{self.port}{location}"

                # Follow the redirect
                return URL(location).request(redirect_limit - 1)

            # assert (
            #     "transfer-encoding" not in response_headers
            # ), "Transfer-Encoding is not supported"
            # assert (
            #     "content-encoding" not in response_headers
            # ), "Content-Encoding is not supported"

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

            # Check the type of raw_body and decode if necessary
            if isinstance(raw_body, bytes):
                decoded_body = raw_body.decode(encoding)
            else:
                decoded_body = raw_body

            if response_headers.get("connection") == "close":
                Sockets.close_socket(self.scheme, self.host, self.port)

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
