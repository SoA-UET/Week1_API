import smtpd
import asyncore
import email

class CustomSMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        print("📩 Nhận email từ:", mailfrom)
        print("📨 Gửi tới:", rcpttos)
        print("🌐 Peer:", peer)

        # Parse nội dung email
        msg = email.message_from_bytes(data)

        print("\n===== Headers =====")
        for k, v in msg.items():
            print(f"{k}: {v}")

        print("\n===== Body =====")
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/xml":
                    print(part.get_payload(decode=True).decode("utf-8"))
        else:
            print(msg.get_payload(decode=True).decode("utf-8"))

        print("====================\n")

        return

if __name__ == "__main__":
    server = CustomSMTPServer(("localhost", 1025), None)
    print("📡 SMTP server đang chạy tại smtp://localhost:1025 ...")
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        print("\n🛑 Server đã dừng.")
