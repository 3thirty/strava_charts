import base64
import io
from urllib.parse import urlencode


class Lambda:
    request = {}

    response = {
        "statusCode": 500,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": ""
    }

    def __init__(self, event: dict):
        self.request = self.getRequest(event)

    def getRequest(self, event: dict) -> dict:
        """
        Convert a lambda event (in API Gateway format) to the WSGI format for
        bottle
        """
        headers = event.get("headers", {})

        event_body = event.get("body", "")
        if event.get("isBase64Encoded", False):
            body = base64.b64decode(event_body)
        elif event_body:
            body = event_body.encode("utf-8")
        else:
            body = b""

        cookies = {}
        if "version" in event and event["version"] == "2.0":
            method = event["requestContext"]["http"].get("method", "GET")
            path = event.get("rawPath", "/")
            query_string = event.get("rawQueryString", "")

            for cookie_header in event.get("cookies", {}):
                (cookie_name, cookie_value) = cookie_header.split('=', 1)
                cookies[cookie_name] = cookie_value.replace('\\', '')
        else:
            method = event.get("httpMethod", "GET")
            cookies = event["headers"].get("cookie", "")
            path = event.get("path", "/")
            query_params = event.get("queryStringParameters", {}) or {}
            query_string = urlencode(query_params)

        # Build request for WSGI
        request = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "SERVER_NAME": headers.get("host", "lambda"),
            "SERVER_PORT": "80",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": headers.get("x-forwarded-proto", "http"),
            "wsgi.input": io.BytesIO(body),
            "wsgi.errors": io.StringIO(),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": True,
        }

        for key, value in headers.items():
            header_key = "HTTP_" + key.upper().replace("-", "_")
            request[header_key] = value

        request['HTTP_COOKIE'] = cookies

        return request

    def handleRequest(self, application) -> bool:
        body = application(self.request, self._buildResponse)
        self.response["body"] = bytes.join(b'', body).decode("utf-8")

        return True

    def getResponse(self) -> dict:
        return self.response

    def _buildResponse(self, status_line, headers, exc_info=None):
        self.response["statusCode"] = int(status_line.split()[0])
        self.response["headers"].update(headers)
