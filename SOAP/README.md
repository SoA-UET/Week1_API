# Demo SOAP API

- [Demo SOAP API](#demo-soap-api)
  - [Lý thuyết](#lý-thuyết)
    - [Giới thiệu về SOAP](#giới-thiệu-về-soap)
    - [Giới thiệu về WSDL](#giới-thiệu-về-wsdl)
  - [Demo](#demo)
    - [Giới thiệu demo](#giới-thiệu-demo)
    - [Các công cụ cần cài đặt](#các-công-cụ-cần-cài-đặt)
    - [Setup môi trường](#setup-môi-trường)
    - [Chạy demo](#chạy-demo)

## Lý thuyết

### Giới thiệu về SOAP

SOAP (Simple Object Access Protocol) là một giao thức dựa trên XML để trao đổi thông điệp giữa các ứng dụng qua mạng.

Nó thường chạy trên HTTP hoặc SMTP, được thiết kế để **định dạng dữ liệu theo chuẩn XML**, giúp các hệ thống khác nhau (viết bằng nhiều ngôn ngữ lập trình hoặc chạy trên nhiều nền tảng) có thể giao tiếp với nhau một cách thống nhất.

Đặc điểm chính của SOAP:

- Sử dụng **XML** làm định dạng thông điệp.
- Hỗ trợ nhiều giao thức truyền tải (HTTP, SMTP...).
- Thường đi kèm với **WSDL** (Web Services Description Language) để mô tả chi tiết API (các phương thức, kiểu dữ liệu, endpoint...).
  - SOAP không bắt buộc phải có WSDL.
  - WSDL chỉ là một "hợp đồng" (contract) có nhiệm vụ:
    - Mô tả API (endpoint, phương thức, tham số, kiểu dữ liệu).
    - Giúp tự động sinh code client/server trong nhiều ngôn ngữ.
  - Chức năng tương tự OpenAPI/Swagger.
  - Nếu không có WSDL:
    - Client và server vẫn có thể trao đổi thông điệp SOAP bằng XML theo chuẩn, miễn là hai bên thống nhất format.
    - Tuy nhiên, việc tích hợp sẽ khó hơn, vì lập trình viên phải tự viết request/response XML, thay vì để công cụ sinh ra từ WSDL.
- Đi kèm hệ sinh thái `WS-* standards` (WS-Security, WS-Transaction, WS-ReliableMessaging...) cho các yêu cầu nâng cao. Một số ví dụ:
  - `WS-Security`: Bảo mật ở mức thông điệp, end-to-end, không phụ thuộc vào kênh (khác với SSL/TLS bảo mật ở mức kênh truyền). `WS-Security` cho phép ký số (digital signature), mã hóa (encryption), chèn thông tin xác thực (username/password, token, certificate) ngay trong thông điệp SOAP XML.
  - `WS-ReliableMessaging` đảm bảo thông điệp SOAP được gửi đúng, đủ, và theo thứ tự. Trong môi trường mạng không ổn định, thông điệp có thể bị mất hoặc gửi trùng. (Với các loại API khác như REST và gRPC, cần viết custom logic như tự động retry... để đảm bảo tính ổn định này.)
  - `WS-AtomicTransaction` và `WS-Coordination` cho phép nhiều dịch vụ SOAP tham gia một giao dịch phân tán (distributed transaction).
    - Trong ngân hàng hay thương mại điện tử, cần đảm bảo tính atomic trên toàn hệ thống.
    - Tức là, giao dịch thành công trên tất cả các dịch vụ liên quan, hoặc tất cả các dịch vụ đó phải rollback.
    - Nhiều dịch vụ cùng tham gia và đảm bảo atomic cho giao dịch đó, chứ không phải chỉ atomic trong phạm vi một database.
    - Với các loại API khác như REST... cần dùng Saga, Two-phase Commit... để giải quyết vấn đề giao dịch phân tán atomic.

### Giới thiệu về WSDL

**WSDL** (viết tắt của Web Services Description Language) là một tệp tin dựa trên định dạng XML, đóng vai trò là "hợp đồng" mô tả chi tiết cách thức hoạt động và truy cập một dịch vụ web (web service). Tệp tin này cung cấp cho ứng dụng client những thông tin cần thiết về các chức năng của dịch vụ, bao gồm các phương thức có sẵn, các tham số đầu vào/ra và cách thức kết nối để sử dụng dịch vụ đó.

**TODO: Viết thêm chi tiết**

## Demo

### Giới thiệu demo

Demo minh họa cách xây dựng và gọi một dịch vụ SOAP:

- **SOAP Server**: Cung cấp một số hàm/dịch vụ cơ bản.
- **SOAP Client**: Gửi request và nhận response từ server.

### Các công cụ cần cài đặt

- Python 3.10

### Setup môi trường

```sh
cd <project_root>/SOAP
cd backend_python
python3.10 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

### Chạy demo

Backend:

```sh
cd <project_root>/SOAP
cd backend_python
source ./venv/bin/activate

python main.py
```
