import grpc from '@grpc/grpc-js';
import protoLoader from '@grpc/proto-loader';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const protoPath = path.resolve(__dirname, '../proto/orders.proto');

const pkgDef = await protoLoader.load(protoPath, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});
const root = grpc.loadPackageDefinition(pkgDef);
const OrderService = root.orders.v1.OrderService;

const client = new OrderService('localhost:50051', grpc.credentials.createInsecure());

const ts = () => new Date().toISOString().split('T')[1].replace('Z','');
const c = {
  head: (s) => `\x1b[1m\x1b[36m${s}\x1b[0m`,    // cyan bold
  ok:   (s) => `\x1b[32m${s}\x1b[0m`,           // green
  warn: (s) => `\x1b[33m${s}\x1b[0m`,           // yellow
  err:  (s) => `\x1b[31m${s}\x1b[0m`,           // red
  info: (s) => `\x1b[90m${s}\x1b[0m`,           // gray
};

function logBlock(title) {
  console.log('\n' + c.head(`========== ${title} ==========`));
}

/** Unary */
function demoUnary() {
  logBlock('UNARY RPC - Create');
  console.log(`[${ts()}] client → Create  payload=`, {customer_id:'C001', item_ids:['A','B']});
  return new Promise((resolve, reject) => {
    client.Create({ customer_id: 'C001', item_ids: ['A', 'B'] }, (err, res) => {
      if (err) {
        console.error(c.err(`[${ts()}] client ← Create ERROR`), err);
        return reject(err);
      }
      console.log(c.ok(`[${ts()}] client ← Create OK`), res);
      resolve(res.order_id);
    });
  });
}

/** Server streaming */
function demoServerStream(orderId) {
  logBlock('SERVER STREAMING - StreamStatus');
  console.log(`[${ts()}] client → StreamStatus  orderId=${orderId}`);
  return new Promise((resolve, reject) => {
    const call = client.StreamStatus({ order_id: orderId });
    call.on('data', ev => console.log(c.ok(`[${ts()}] client ← status event`), ev));
    call.on('end',  () => { console.log(c.info(`[${ts()}] client ← StreamStatus END`)); resolve(); });
    call.on('error', err => { console.error(c.err(`[${ts()}] client ← StreamStatus ERROR`), err); reject(err); });
  });
}

/** Client streaming */
function demoClientStream() {
  logBlock('CLIENT STREAMING - UploadNotes');
  return new Promise((resolve, reject) => {
    const call = client.UploadNotes((err, summary) => {
      if (err) {
        console.error(c.err(`[${ts()}] client ← UploadNotes ERROR`), err);
        return reject(err);
      }
      console.log(c.ok(`[${ts()}] client ← UploadNotes SUMMARY`), summary);
      resolve();
    });

    const notes = [
      { text: 'note 1', ts: Math.floor(Date.now()/1000) },
      { text: 'note 2', ts: Math.floor(Date.now()/1000) },
      { text: 'note 3', ts: Math.floor(Date.now()/1000) },
    ];

    notes.forEach((n, i) => {
      console.log(`[${ts()}] client → UploadNotes  send[${i}]`, n);
      call.write(n);
    });
    console.log(c.info(`[${ts()}] client → UploadNotes END-OF-STREAM`));
    call.end();
  });
}

/** Bidirectional streaming */
function demoBidi() {
  logBlock('BIDIRECTIONAL STREAMING - Chat');
  return new Promise((resolve, reject) => {
    const call = client.Chat();

    call.on('data', msg => {
      console.log(c.ok(`[${ts()}] client ← Chat  recv`), msg);
    });
    call.on('end', () => {
      console.log(c.info(`[${ts()}] client ← Chat END`));
      resolve();
    });
    call.on('error', err => {
      console.error(c.err(`[${ts()}] client ← Chat ERROR`), err);
      reject(err);
    });

    const sends = [
      { from: 'cli', text: 'hello 1', ts: Math.floor(Date.now()/1000) },
      { from: 'cli', text: 'hello 2', ts: Math.floor(Date.now()/1000) },
      { from: 'cli', text: 'hello 3', ts: Math.floor(Date.now()/1000) },
    ];

    let i = 0;
    const tick = setInterval(() => {
      if (i >= sends.length) {
        clearInterval(tick);
        console.log(c.info(`[${ts()}] client → Chat END-OF-STREAM`));
        call.end();
        return;
      }
      const m = sends[i++];
      console.log(`[${ts()}] client → Chat  send`, m);
      call.write(m);
    }, 250);
  });
}

(async () => {
  try {
    const orderId = await demoUnary();
    await demoServerStream(orderId);
    await demoClientStream();
    await demoBidi();
    console.log('\n' + c.head('✅ ALL DONE'));
  } catch (e) {
    console.error(c.err('✗ FAILED'), e);
    process.exit(1);
  }
})();
