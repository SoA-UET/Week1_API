from http.server import BaseHTTPRequestHandler, HTTPServer
import xml.etree.ElementTree as ET

received_messages = set()
expected_id = 1  # MessageID ban đầu

class SOAPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        global expected_id

        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode("utf-8")

        # Parse SOAP XML
        root = ET.fromstring(body)
        ns = {"soap": "http://schemas.xmlsoap.org/soap/envelope/"}
        message_id = int(root.find(".//MessageID").text)
        payload = root.find(".//Payload").text

        print(f"📩 Nhận MessageID={message_id}, Payload={payload}")

        response_status = "Accepted"

        # Kiểm tra duplicate
        if message_id in received_messages:
            print("⚠️ Duplicate message, bỏ qua.")
            response_status = "Duplicate"
        # Kiểm tra thứ tự
        elif message_id != expected_id:
            print(f"⚠️ MessageID={message_id} không đúng thứ tự, mong đợi {expected_id}")
            response_status = "OutOfOrder"
        else:
            received_messages.add(message_id)
            expected_id += 1
            print("✅ Message xử lý thành công.")

        # SOAP Response
        response_xml = f"""<?xml version="1.0"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <Response>
                    <Status>{response_status}</Status>
                </Response>
            </soap:Body>
        </soap:Envelope>
        """

        self.send_response(200)
        self.send_header("Content-Type", "text/xml")
        self.end_headers()
        self.wfile.write(response_xml.encode("utf-8"))


def run():
    server = HTTPServer(("localhost", 8086), SOAPHandler)
    print("🚀 SOAP Server chạy ở http://localhost:8086")
    server.serve_forever()


if __name__ == "__main__":
    run()
