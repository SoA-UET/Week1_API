import { Button, Input } from "antd";
import { useState } from "react";
import { XMLParser } from "fast-xml-parser";

export default function HomePage() {
    const [endpoint, setEndpoint] = useState("http://localhost:8082/myservice");
    const [namespace, setNamespace] = useState("my.namespace");
    const [name, setName] = useState("");

    const callSoapApi = async () => {
        const action = "sayHello";
        const payload = createPayload(namespace, name, action);

        const res = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "text/xml;charset=UTF-8",
                "SOAPAction": action,
            },
            body: payload,
        });

        const text = await res.text();
        alert(parseResponse(text));
    };

    return <div>
        <h2>SOAP API Try-out</h2>

        <div>
            <label>Service Endpoint: </label>
            <Input value={endpoint} onChange={(e) => setEndpoint(e.target.value)} style={{ width: 400 }} />
        </div>

        <div>
            <label>Service Namespace: </label>
            <Input value={namespace} onChange={(e) => setNamespace(e.target.value)} style={{ width: 400 }} />
        </div>

        <div>
            <label>Enter Name: </label>
            <Input value={name} onChange={(e) => setName(e.target.value)} style={{ width: 400 }} />
        </div>

        <div style={{ marginTop: 20 }}>
            <Button onClick={callSoapApi} type="primary">Call SOAP API</Button>
        </div>

        <div style={{ marginTop: 20 }}>
            <i>Note: Make sure the SOAP API server is running and accessible.</i>
        </div>
    </div>;
}

const createPayload = (serviceNamespace: string, name: string, action: string) => {
    return `
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                        xmlns:my="${serviceNamespace}">
        <soapenv:Header/>
        <soapenv:Body>
            <my:${action}>
                <first_name>${name}</first_name>
            </my:${action}>
        </soapenv:Body>
        </soapenv:Envelope>
    `;
};

const parseResponse = (responseBodyText: string) => {
    const parser = new XMLParser({
        ignoreAttributes: false,
        removeNSPrefix: true, // important: removes "soap11env:" and "tns:"
    });

    const obj = parser.parse(responseBodyText);
    const result = obj.Envelope.Body.sayHelloResponse.sayHelloResult;
    
    return `Parsed result:\n${result}\n\nRaw response:\n${responseBodyText}`;
};
