import time, random, sys
from concurrent import futures
import grpc

import orders_pb2 as pb
import orders_pb2_grpc as rpc

RESET = "\x1b[0m"
BOLD  = "\x1b[1m"
CYAN  = "\x1b[36m"
GREEN = "\x1b[32m"
YELL  = "\x1b[33m"
RED   = "\x1b[31m"
GRAY  = "\x1b[90m"

def ts():
    return time.strftime("%H:%M:%S", time.localtime())

def head(s): return f"{BOLD}{CYAN}{s}{RESET}"
def ok(s):   return f"{GREEN}{s}{RESET}"
def warn(s): return f"{YELL}{s}{RESET}"
def err(s):  return f"{RED}{s}{RESET}"
def info(s): return f"{GRAY}{s}{RESET}"

class OrderService(rpc.OrderServiceServicer):

    # Unary
    def Create(self, request, context):
        print(head("\n========== UNARY RPC - Create =========="))
        print(f"[{ts()}] server ← Create  payload={{customer_id:{request.customer_id}, item_ids:{list(request.item_ids)}}}")
        oid = f"ord_{int(time.time()*1e6)}"
        print(ok(f"[{ts()}] server → Create  response={{order_id:{oid}}}"))
        return pb.CreateOrderRes(order_id=oid)

    # Server-streaming
    def StreamStatus(self, request, context):
        print(head("\n========== SERVER STREAMING - StreamStatus =========="))
        print(f"[{ts()}] server ← StreamStatus  orderId={request.order_id}")
        statuses = ["PENDING", "PAID", "PACKING", "SHIPPING", "DONE"]
        for i, st in enumerate(statuses):
            ev = pb.StatusEvent(status=st, ts=int(time.time()))
            print(ok(f"[{ts()}] server → status[{i}]"), f"{ev.status} ts={ev.ts}")
            time.sleep(0.25)
            yield ev
        print(info(f"[{ts()}] server → StreamStatus END"))

    # Client-streaming
    def UploadNotes(self, request_iterator, context):
        print(head("\n========== CLIENT STREAMING - UploadNotes =========="))
        cnt = 0
        for note in request_iterator:
            cnt += 1
            print(f"[{ts()}] server ← note[{cnt}]  text={note.text} ts={note.ts}")
        print(ok(f"[{ts()}] server → summary  count={cnt}"))
        return pb.UploadSummary(count=cnt)

    # Bidirectional-streaming
    def Chat(self, request_iterator, context):
        print(head("\n========== BIDIRECTIONAL STREAMING - Chat =========="))
        idx = 0
        for msg in request_iterator:
            sender = getattr(msg, "from", "")
            print(f"[{ts()}] server ← chat[{idx}]  from={sender} text={msg.text} ts={msg.ts}")
            reply = pb.ChatMsg()
            setattr(reply, "from", "server")
            reply.text = f"ack:{sender}|{msg.text}|{random.randint(0,99)}"
            reply.ts   = int(time.time())
            print(ok(f"[{ts()}] server → chat[{idx}]  from=server text={reply.text} ts={reply.ts}"))
            idx += 1
            yield reply
        print(info(f"[{ts()}] server → Chat END"))

def serve():
    print(head("🚀 gRPC Python server starting on :50051"))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rpc.add_OrderServiceServicer_to_server(OrderService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print(ok(f"[{ts()}] READY  listen=:50051"))
    server.wait_for_termination()

if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        print(warn("\nServer interrupted"))
        sys.exit(0)
