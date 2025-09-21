# 📖 gRPC Demo: Unary, Server Streaming, Client Streaming, Bidirectional Streaming

## 🚀 Giới thiệu
Dự án này minh họa cách dùng **gRPC** với **Protocol Buffers** trong giao tiếp giữa microservices.  
Ta triển khai **Server bằng Python** và **Client bằng Node.js**, để thử các kiểu RPC:

- **Unary**: 1 request → 1 response  
- **Server streaming**: 1 request → nhiều response  
- **Client streaming**: nhiều request → 1 response  
- **Bidirectional streaming**: nhiều request ↔ nhiều response đồng thời

---

## 📂 Cấu trúc dự án
```
demo-grpc/
 ├─ proto/           # file .proto định nghĩa service & messages
 ├─ server-py/       # Python gRPC server (orders service)
 ├─ client-node/     # Node.js gRPC client (index.mjs)
 └─ evidence/        # Evidence: JSON vs Protobuf binary
```

---

## 🔧 Chạy thử

### 1. Cài dependencies
# Python server
pip install grpcio grpcio-tools

# Node client
npm install @grpc/grpc-js @grpc/proto-loader
```

### 2. Sinh code từ .proto
# Python
python -m grpc_tools.protoc -I=proto proto/orders.proto   --python_out=server-py --grpc_python_out=server-py


### 3. Chạy server
cd server-py
python server.py


### 4. Chạy client
cd client-node
node index.mjs



## 📌 Ứng dụng thực tế
- **Unary**: CRUD cơ bản (tạo đơn hàng, lấy thông tin user)  
- **Server streaming**: stream log, tiến độ xử lý đơn hàng  
- **Client streaming**: upload nhiều chunk file/log rồi tổng hợp  
- **Bidirectional streaming**: chat app, game real-time, IoT sensors  
