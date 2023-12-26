import base64
from curses import raw
import html
import gzip
from cache import Cache
from sockets import Sockets
import urllib.parse


class URL:
    def __init__(
        self, url="file:///path/to/default/testfile.html"
    ):  # default file path
        self.url = url

        self.view_source = False
        if url.startswith("view-source:"):
            self.view_source = True
            url = url[len("view-source:") :]

        if "://" in url:
            self.scheme, url = url.split("://", 1)
        else:
            self.scheme, url = url.split(":", 1)

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
            # self.data = url  # Data embedded in URL
            self.data = urllib.parse.unquote(url)

    # Decode HTML entities in the text.
    def decode_html_entities(self, text):
        return html.unescape(text)

    # Additional method to read chunked binary data
    def read_chunked(self, response):
        chunks = []
        while True:
            # Read and decode the size line
            size_str = response.readline().decode("iso-8859-1").strip()
            if not size_str:
                break  # Exit if the size line is empty (should not happen, but just in case)

            # Convert size from hex to int
            chunk_size = int(size_str, 16)

            # If chunk size is 0, this is the last chunk
            if chunk_size == 0:
                break

            # Read the chunk data
            chunk = response.read(chunk_size)
            chunks.append(chunk)

            # Read and discard the trailing "\r\n" after the chunk
            response.read(2)  # Read 2 bytes for "\r\n"

        # Combine all chunks into a single byte sequence
        return b"".join(chunks)

    def request(self, redirect_limit=10):
        if self.scheme in ["http", "https"]:
            cached_response = Cache.get_cached_response(self.url)
            if cached_response:
                return self.process_cached_response(cached_response)

            s = Sockets.get_socket(self.scheme, self.host, self.port)

            request_headers = (
                f"GET {self.path} HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                "Connection: keep-alive\r\n"
                "Accept-Encoding: gzip\r\n"
                "Accept: */*\r\n"
                "User-Agent: mlwcz\r\n\r\n"
            )

            s.send(request_headers.encode("utf8"))

            response = s.makefile("rb")  # Open in binary mode
            raw_statusline = response.readline()
            statusline = raw_statusline.decode(
                "iso-8859-1"
            )  # ISO-8859-1 is a safe bet for headers
            version, status, explanation = statusline.split(" ", 2)
            status_code = int(status)

            response_headers = {}
            content_length = None

            while True:
                line = response.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
                line = line.decode("iso-8859-1")
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

            # Determine correct encoding
            gzip_compressed = response_headers.get("content-encoding") == "gzip"
            content_type = response_headers.get("content-type", "")
            encoding = "utf8"  # Default encoding
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].split(";")[0]
            elif "text" in content_type or "json" in content_type:
                encoding = "utf8"

            # Read the response body
            raw_body = b""
            if (
                "transfer-encoding" in response_headers
                and response_headers["transfer-encoding"] == "chunked"
            ):
                raw_body = self.read_chunked(response)
            elif content_length is not None:
                raw_body = response.read(content_length)
            else:
                raw_body = response.read()

            if gzip_compressed:
                # Decompress gzip data
                try:
                    raw_body = gzip.decompress(raw_body)
                except Exception as e:
                    print(f"Error decompressing gzip data: {e}")
                    return None

            # Decode or process the response body
            try:
                # Decode the body if it's text
                if "text" in content_type or "json" in content_type:
                    body = raw_body.decode(encoding)
                else:
                    body = raw_body  # Handle as binary data
            except UnicodeDecodeError:
                print(f"Failed to decode response with encoding: {encoding}")
                return None

            # Check for cache
            cache_control = response_headers.get("cache-control", "")
            # Process the response for caching
            if "no-store" not in cache_control:
                max_age = Cache.get_max_age(cache_control)
                cache_entry = {
                    "body": raw_body,
                    "headers": response_headers,
                    "url": self.url,
                    "encoding": encoding,
                }
                Cache.store_in_cache(cache_entry, max_age, self.url)

            if (
                "connection" in response_headers
                and response_headers["connection"] == "close"
            ) or status_code == 304:
                Sockets.close_socket(self.scheme, self.host, self.port)

            if self.view_source:
                # Return raw HTML for view-source
                return body
            else:
                # Decode HTML entities for normal viewing
                return self.decode_html_entities(body)

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

    def process_cached_response(self, cached_response):
        raw_body = cached_response["body"]
        response_headers = cached_response["headers"]
        content_type = response_headers.get("content-type", "")
        encoding = cached_response["encoding"]

        # Decode or process the response body
        try:
            # Decode the body if it's text
            if "text" in content_type or "json" in content_type:
                body = raw_body.decode(encoding)
            else:
                body = raw_body  # Handle as binary data
        except UnicodeDecodeError:
            print(f"Failed to decode response with encoding: {encoding}")
            return None

        if self.view_source:
            # Return raw HTML for view-source
            return body
        else:
            # Decode HTML entities for normal viewing
            return self.decode_html_entities(body)
