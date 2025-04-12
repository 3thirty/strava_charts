import base64
import io


class Lambda:
    request = {}

    response = {
        "status": 500,
        "headers": {},
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
        else:
            body = event_body.encode("utf-8")

        # Build request for WSGI
        request = {
            "REQUEST_METHOD": event["requestContext"]["http"]["method"],
            "PATH_INFO": event.get("rawPath", "/"),
            "QUERY_STRING": event.get("rawQueryString", ""),
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

        return request

    def handleRequest(self, application) -> bool:
        self.response["body"] = application(self.request, self._buildResponse)

        return True

    def getResponse(self) -> dict:
        return self.response

    def _buildResponse(self, status_line, headers, exc_info=None):
        self.response["status"] = int(status_line.split()[0])
        self.response["headers"] = dict(headers)
