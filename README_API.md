# API de Atualização do Power BI

API Flask para disparar atualizações do Power BI de forma segura através de uma interface web.

## Instalação

### 1. Instalar dependências

```bash
pip install flask --break-system-packages
pip install requests --break-system-packages
pip install python-dotenv --break-system-packages
```

Para ambiente de produção (com Gunicorn):
```bash
pip install gunicorn --break-system-packages
```

### 2. Configurar variáveis de ambiente

Edite o arquivo `.env`:

```
API_TOKEN=seu-token-muito-secreto-aqui
SERVIDOR_BI=192.168.0.210
TASK_NAME=AtualizaBI_TI
```

**IMPORTANTE:** Mude o `API_TOKEN` para algo seguro! Você pode gerar um token forte assim em Python:

```python
import secrets
print(secrets.token_urlsafe(32))
```

### 3. Executar a API

#### Modo desenvolvimento (teste):
```bash
python api_bi.py
```

A API estará disponível em: `http://localhost:5000`

#### Modo produção (recomendado com Gunicorn):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 api_bi:app
```

## Endpoints

### 1. Health Check (sem autenticação)
```
GET /health
```

**Resposta:**
```json
{
  "status": "ok",
  "timestamp": "2024-02-17T10:30:00.123456",
  "mensagem": "API de atualização do BI está funcionando"
}
```

### 2. Informações da API (sem autenticação)
```
GET /info
```

**Resposta:**
```json
{
  "nome": "API de Atualização do Power BI",
  "versao": "1.0.0",
  "endpoints": {...},
  "autenticacao": "Bearer Token no header Authorization"
}
```

### 3. Status da Configuração (sem autenticação)
```
GET /status
```

**Resposta:**
```json
{
  "servidor": "192.168.0.210",
  "tarefa": "AtualizaBI_TI",
  "timestamp": "2024-02-17T10:30:00.123456"
}
```

### 4. Disparar Atualização (COM autenticação)
```
POST /atualizar-bi
Header: Authorization: Bearer seu-token-aqui
```

**Resposta de sucesso (202):**
```json
{
  "timestamp": "2024-02-17T10:30:00.123456",
  "status": "sucesso",
  "mensagem": "Atualização iniciada com sucesso",
  "ip_cliente": "192.168.1.100"
}
```

**Resposta de erro (401 - sem token):**
```json
{
  "erro": "Token não fornecido"
}
```

**Resposta de erro (401 - token inválido):**
```json
{
  "erro": "Token inválido"
}
```

## Testando a API

### Usando o script de teste Python:

```bash
python teste_api.py
```

### Usando cURL:

#### Testar health check:
```bash
curl http://localhost:5000/health
```

#### Testar info:
```bash
curl http://localhost:5000/info
```

#### Disparar atualização:
```bash
curl -X POST http://localhost:5000/atualizar-bi \
  -H "Authorization: Bearer seu-token-aqui"
```

#### Com token inválido (teste de segurança):
```bash
curl -X POST http://localhost:5000/atualizar-bi
```

### Usando Postman ou Insomnia:

1. Método: `POST`
2. URL: `http://localhost:5000/atualizar-bi`
3. Headers: 
   - `Authorization`: `Bearer seu-token-aqui`
4. Body: vazio

## Logging

A API registra todas as atividades no arquivo `api_bi.log` e também no console.

Exemplo de log:
```
2024-02-17 10:30:00,123 - __main__ - INFO - Requisição de atualização recebida de 192.168.1.100
2024-02-17 10:30:00,124 - __main__ - INFO - Executando comando: schtasks /run /s 192.168.0.210 /tn "AtualizaBI_TI"
2024-02-17 10:30:01,456 - __main__ - INFO - Atualização do BI iniciada com sucesso
```

## Instalando como Serviço Windows

### Usando NSSM (Non-Sucking Service Manager)

1. Baixe o NSSM: https://nssm.cc/download
2. Extraia em uma pasta, ex: `C:\nssm`
3. Abra PowerShell como Administrador e execute:

```powershell
cd C:\nssm\win64
.\nssm.exe install BiApiService "C:\Python\python.exe" "C:\caminho\para\api_bi.py"
.\nssm.exe start BiApiService
```

### Usando um script batch:

Crie um arquivo `instalar_servico.bat`:

```batch
@echo off
cd /d %~dp0
python -m pip install pywin32
python Scripts/pyinstall_win.py --install pywin32

REM Instalar como serviço usando NSSM ou similar
echo Serviço instalado!
pause
```

## Segurança

- **Token**: Mude o token padrão! Use um token seguro (mínimo 32 caracteres)
- **HTTPS**: Em produção, use HTTPS/SSL
- **Firewall**: Restrinja acesso à API apenas de IPs autorizados
- **Logs**: Monitore os logs regularmente para tentativas suspeitas
- **Credenciais**: Armazene o token em variáveis de ambiente, não no código

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'flask'"
**Solução:** Instale Flask: `pip install flask --break-system-packages`

### Erro: "Porta 5000 já em uso"
**Solução:** Mude a porta no código ou termine o processo usando a porta

### Erro: "Acesso negado ao conectar ao servidor BI"
**Solução:** Verifique:
- O IP do servidor está correto
- Há firewall bloqueando a comunicação
- A tarefa agendada existe no servidor
- O usuário que executa a API tem permissões

## Próximos Passos

1. Teste a API neste servidor
2. Crie uma página web para disparar a atualização
3. Configure autenticação mais robusta se necessário
4. Implante como serviço Windows em produção

## Suporte

Para dúvidas ou problemas, verifique:
- Logs em `api_bi.log`
- Resposta HTTP (verifique o status code)
- Configuração do `.env`
- Permissões de rede e firewall
