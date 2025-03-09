import requests

url = 'http://localhost:5000/webhook'

for i in range(25):
    data = {
        "name": f"Lead TESTE {i+1}",
        "email": f"lead{i+1}abcd0@example.com",
        "phone": [f"+551198{i+1}9399{i+1}"],
        "horario_contato": "Tarde",
        "valor_investimento": "5000",
        "preferencia_contato": "Telefone"
    }
    response = requests.post(url, json=data)
    print(f"Enviando lead {i+1}: Status {response.status_code}")

# response = requests.post(url, json={})