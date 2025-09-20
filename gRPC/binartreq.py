import os, sys
sys.path.append(os.path.join(os.getcwd(), 'server-py'))
import orders_pb2 as pb

m = pb.CreateOrderReq(customer_id="C001", item_ids=["A","B"])
with open(os.path.join('example','req.bin'), 'wb') as f:
    f.write(m.SerializeToString())
print("Wrote example/req.bin")