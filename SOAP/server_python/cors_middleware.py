class CORSMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def cors_start_response(status, headers, exc_info=None):
            headers.append(("Access-Control-Allow-Origin", "*"))
            headers.append(("Access-Control-Allow-Methods", "POST, OPTIONS"))
            headers.append(("Access-Control-Allow-Headers", "Content-Type, SOAPAction"))
            return start_response(status, headers, exc_info)

        # Handle preflight OPTIONS request
        if environ["REQUEST_METHOD"] == "OPTIONS":
            start_response("200 OK", [
                ("Access-Control-Allow-Origin", "*"),
                ("Access-Control-Allow-Methods", "POST, OPTIONS"),
                ("Access-Control-Allow-Headers", "Content-Type, SOAPAction"),
                ("Content-Length", "0"),
            ])
            return [b""]

        return self.app(environ, cors_start_response)
