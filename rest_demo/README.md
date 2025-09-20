# REST Demo - Django REST API

## Hướng dẫn cài đặt và chạy dự án

### 1. Clone dự án từ GitHub

```bash
git clone <repository-url>
cd Week1_API/rest_demo
```

### 2. Cài đặt môi trường Python

Đảm bảo bạn đã cài đặt Python 3.8+ trên máy tính.

### 3. Tạo môi trường ảo (Virtual Environment)

```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
# Trên Windows:
venv\Scripts\activate

# Trên macOS/Linux:
source venv/bin/activate
```

### 4. Cài đặt các thư viện cần thiết

```bash
pip install django
pip install djangorestframework
pip install drf-yasg
```

### 5. Thiết lập cơ sở dữ liệu

```bash
# Tạo các migration
python manage.py makemigrations

# Áp dụng migration
python manage.py migrate
```

### 6. Chạy server

```bash
python manage.py runserver
```

Server sẽ chạy tại: http://127.0.0.1:8000/

### 7. Truy cập Swagger UI

- Swagger UI: http://127.0.0.1:8000/swagger/