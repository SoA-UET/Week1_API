import * as soap from "soap";

async function main() {
  const wsdlUrl = "http://localhost:8082/myservice?wsdl";

  const client = await soap.createClientAsync(wsdlUrl);
  const [result] = await client.sayHelloAsync({ first_name: "Alice" });

  console.log(result); // { greeting: 'Hello, Alice' }
}

main();
