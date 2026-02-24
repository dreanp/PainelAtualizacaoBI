import requests
import json

# Configuração
API_URL = 'http://192.168.0.210:5000'  # Altere para o IP do seu servidor se for diferente
TOKEN = 'seu-token-aqui'  # Deve ser igual ao do .env

def testar_health():
    """Testa o endpoint de health check"""
    print("\n=== Testando Health Check ===")
    try:
        response = requests.get(f'{API_URL}/health')
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {e}")

def testar_info():
    """Testa o endpoint de informações"""
    print("\n=== Testando Info ===")
    try:
        response = requests.get(f'{API_URL}/info')
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {e}")

def testar_status():
    """Testa o endpoint de status"""
    print("\n=== Testando Status ===")
    try:
        response = requests.get(f'{API_URL}/status')
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {e}")

def testar_atualizacao_sem_token():
    """Testa a atualização SEM token (deve falhar)"""
    print("\n=== Testando Atualização SEM Token (deve falhar) ===")
    try:
        response = requests.post(f'{API_URL}/atualizar-bi')
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {e}")

def testar_atualizacao_com_token_invalido():
    """Testa a atualização com token INVÁLIDO (deve falhar)"""
    print("\n=== Testando Atualização com Token Inválido (deve falhar) ===")
    try:
        headers = {'Authorization': f'Bearer token-invalido'}
        response = requests.post(f'{API_URL}/atualizar-bi', headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {e}")

def testar_atualizacao_com_token_valido():
    """Testa a atualização com token VÁLIDO"""
    print("\n=== Testando Atualização com Token Válido ===")
    try:
        headers = {'Authorization': f'Bearer {TOKEN}'}
        response = requests.post(f'{API_URL}/atualizar-bi', headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("TESTANDO API DE ATUALIZAÇÃO DO POWER BI")
    print("=" * 50)
    
    testar_health()
    testar_info()
    testar_status()
    testar_atualizacao_sem_token()
    testar_atualizacao_com_token_invalido()
    testar_atualizacao_com_token_valido()
    
    print("\n" + "=" * 50)
    print("TESTES CONCLUÍDOS")
    print("=" * 50)
