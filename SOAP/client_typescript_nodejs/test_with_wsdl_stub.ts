import { createClientAsync } from "./generated/myservice";

async function main() {
    const client = await createClientAsync("http://localhost:8082/myservice?wsdl");
    const [result] = await client.sayHelloAsync({ first_name: "Alice, with WSDL stub" });

    console.log(result); // { greeting: 'Hello, Alice' }
}

main();
