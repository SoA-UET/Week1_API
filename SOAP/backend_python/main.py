from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

class MyService(ServiceBase):
    @rpc(Unicode, _returns=Unicode)
    def sayHello(ctx, first_name):
        return f"Hello, {first_name}"

application = Application([MyService], 'my.namespace',
    in_protocol=Soap11(), out_protocol=Soap11())
wsgi_app = WsgiApplication(application)

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    server = make_server('127.0.0.1', 8082, wsgi_app)
    print("SOAP server running on http://127.0.0.1:8082")
    server.serve_forever()
