import requests
import random
import time

def send_message(message_id, payload):
    soap_request = f"""<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <Message>
                <MessageID>{message_id}</MessageID>
                <Payload>{payload}</Payload>
            </Message>
        </soap:Body>
    </soap:Envelope>
    """

    headers = {"Content-Type": "text/xml"}
    response = requests.post("http://localhost:8086", data=soap_request, headers=headers)
    print(f"📤 Sent MessageID={message_id}, Server trả về: {response.text}\n")


# Gửi 5 message, cố tình gửi trùng và sai thứ tự
messages = [
    (1, "Hello"),
    (2, "How"),
    (2, "How AGAIN"),  # Duplicate
    (4, "Out of order"),  # Sai thứ tự
    (3, "Are you?"),
    (5, "Bye")
]

for mid, payload in messages:
    send_message(mid, payload)
    time.sleep(1)
