from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from cors_middleware import CORSMiddleware

class MyService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def sayHello(ctx, first_name):
        return f"Hello, {first_name}"

application = Application([MyService], 'my.namespace',
    in_protocol=Soap11(), out_protocol=Soap11())
wsgi_app = WsgiApplication(application)

wsgi_app = CORSMiddleware(wsgi_app)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('0.0.0.0', 8080, wsgi_app)
    print("SOAP server running on http://localhost:8080")
    server.serve_forever()
