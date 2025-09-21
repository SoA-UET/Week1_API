from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
from lxml import etree


class MyService(ServiceBase):

    @rpc(Unicode, _returns=Unicode)
    def GetWeather(ctx, city):
        # Lấy raw SOAP request
        soap_request = ctx.in_document

        # Nếu là ElementTree thì lấy root
        if isinstance(soap_request, etree._ElementTree):
            root = soap_request.getroot()
        else:
            root = soap_request

        ns = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "wsse": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
        }

        username = root.findtext(".//wsse:Username", namespaces=ns)
        password = root.findtext(".//wsse:Password", namespaces=ns)

        print(f"🛡️ WS-Security header nhận được: {username}/{password}")

        # Validate username & password
        if username != "dat" or password != "123456":
            raise Exception("❌ Authentication failed!")

        # Trả kết quả nếu pass auth
        return f"Nhiệt độ tại {city} là 32°C"


application = Application([MyService], "my.namespace",
                          in_protocol=Soap11(validator="lxml"),
                          out_protocol=Soap11())

wsgi_app = WsgiApplication(application)

if __name__ == "__main__":
    server = make_server("127.0.0.1", 8084, wsgi_app)
    print("✅ SOAP server chạy ở http://127.0.0.1:8084")
    server.serve_forever()
