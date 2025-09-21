import smtplib
from email.mime.text import MIMEText

soap_request = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
   <soap:Body>
      <GetWeather xmlns="http://example.com/weather">
         <City>Hanoi</City>
      </GetWeather>
   </soap:Body>
</soap:Envelope>"""

msg = MIMEText(soap_request, "xml")
msg["Subject"] = "SOAP Request"
msg["From"] = "client@example.com"
msg["To"] = "service@example.com"

with smtplib.SMTP("localhost", 1025) as server:
    server.send_message(msg)

print("✅ Đã gửi SOAP Request qua SMTP")
