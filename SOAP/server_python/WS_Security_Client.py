from zeep import Client
from zeep.wsse.username import UsernameToken

# Client với UsernameToken
client = Client("http://127.0.0.1:8084/?wsdl",
                wsse=UsernameToken("dat", "123456"))

result = client.service.GetWeather("Hanoi")
print("🌤️ Server trả về:", result)
