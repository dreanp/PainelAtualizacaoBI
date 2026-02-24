# ⚡ Painel de Atualização Power BI

Sistema web completo para disparar atualizações de relatórios Power BI via tarefas agendadas do Windows, com autenticação por usuário, controle de permissões por aplicação e painel administrativo.

---

## 📋 Sumário

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
- [Banco de Dados](#banco-de-dados)
- [Referência da API](#referência-da-api)
- [Frontend](#frontend)
- [Hospedagem no IIS](#hospedagem-no-iis)
- [Segurança](#segurança)
- [Troubleshooting](#troubleshooting)

---

## Visão Geral

O sistema é composto por uma **API Flask** (backend) e páginas HTML estáticas (frontend). Usuários fazem login, visualizam apenas as aplicações às quais têm acesso e disparam atualizações de relatórios Power BI com um clique. Administradores têm acesso a um painel para gerenciar usuários e permissões.

**Fluxo resumido:**

```
Usuário → login.html → dashboard.html → API Flask → schtasks (Windows) → Power BI Gateway
```

---

## Arquitetura

```
┌─────────────────────────────────┐
│         Frontend (IIS)          │
│  login.html / dashboard.html    │
│       admin.html                │
└────────────┬────────────────────┘
             │ HTTP (fetch API)
             ▼
┌─────────────────────────────────┐
│      Backend: api_bi.py         │
│      Flask · Python 3.x         │
│      Porta 5000                 │
└──────┬──────────────┬───────────┘
       │              │
       ▼              ▼
┌────────────┐  ┌─────────────────┐
│ SQL Server │  │ schtasks /run   │
│ (usuários) │  │ (Windows Task   │
│            │  │  Scheduler)     │
└────────────┘  └─────────────────┘
```

### Componentes

| Componente | Tecnologia | Função |
|---|---|---|
| API | Python / Flask | Autenticação, autorização e disparo de tarefas |
| Frontend | HTML + CSS (vanilla) | Interface do usuário |
| Banco de dados | SQL Server (pyodbc) | Gerenciamento de usuários e permissões |
| Agendador | Windows Task Scheduler | Execução das atualizações Power BI |
| Servidor Web | IIS (Windows Server) | Hospedagem das páginas estáticas |

---

## Estrutura de Arquivos

```
├── api_bi.py              # API principal (Flask)
├── gerar_hashes.py        # Utilitário para gerar hashes bcrypt
├── teste_api.py           # Script de testes dos endpoints
├── .env                   # Variáveis de ambiente (não versionar!)
├── api_bi.log             # Log gerado em runtime (não versionar)
│
├── login.html             # Página de login
├── login.css
│
├── dashboard.html         # Painel do usuário (disparo de tarefas)
├── dashboard.css
│
├── admin.html             # Painel de gerenciamento de usuários (admin)
├── admin.css
│
├── index.html             # Redirecionamento / página inicial
├── web.config             # Configuração do IIS (documento padrão)
│
├── instalar_iis.ps1       # Script PowerShell para instalação do IIS
├── GUIA_IIS.md            # Guia detalhado de configuração do IIS
└── README.md              # Este arquivo
```

> **Não versionar:** `.env`, `api_bi.log`, e qualquer arquivo contendo senhas ou tokens.

---

## Pré-requisitos

### Backend

- Python 3.8+
- Windows Server (para execução do `schtasks`)
- SQL Server com ODBC Driver 17
- Tarefas agendadas configuradas no Windows Task Scheduler

### Frontend

- IIS instalado no Windows Server

---

## Instalação e Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 2. Instalar dependências Python

```bash
pip install flask flask-cors requests python-dotenv pyodbc bcrypt --break-system-packages
```

Para produção com Gunicorn:

```bash
pip install gunicorn --break-system-packages
```

### 3. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto (use `.env.example` como base):

```env
# Token de autenticação Bearer (gere um token seguro!)
API_TOKEN=seu-token-muito-secreto-aqui

# Servidor onde as tarefas agendadas estão configuradas
SERVIDOR_BI=192.168.0.210

# Nome da tarefa padrão (usado pelo endpoint /atualizar-bi)
TASK_NAME=AtualizaBI_TI

# Banco de dados SQL Server
DB_SERVER=192.168.0.210
DB_NAME=powerbi_usuarios
DB_USER=usuario_sql
DB_PASSWORD=senha_sql
```

Para gerar um token seguro:

```python
import secrets
print(secrets.token_urlsafe(32))
```

### 4. Criar o banco de dados

Execute o script SQL abaixo no SQL Server (veja a seção [Banco de Dados](#banco-de-dados)).

### 5. Gerar hashes de senha

Edite e execute `gerar_hashes.py` para gerar os hashes bcrypt dos usuários iniciais:

```bash
pip install bcrypt --break-system-packages
python gerar_hashes.py
```

Cole os hashes gerados nos `INSERT`s do banco de dados.

### 6. Executar a API

**Modo desenvolvimento:**

```bash
python api_bi.py
```

**Modo produção (recomendado):**

```bash
gunicorn -w 4 -b 0.0.0.0:5000 api_bi:app
```

A API estará disponível em `http://localhost:5000`.

---

## Banco de Dados

### Schema da tabela `usuarios`

```sql
CREATE TABLE usuarios (
    username      VARCHAR(50)   PRIMARY KEY,
    senha_hash    VARCHAR(255)  NOT NULL,
    display_name  VARCHAR(100)  NOT NULL,
    aplicacoes    VARCHAR(MAX)  NOT NULL DEFAULT '[]', -- JSON array de task IDs
    ativo         BIT           NOT NULL DEFAULT 1,
    criado_em     DATETIME      DEFAULT GETDATE(),
    atualizado_em DATETIME      DEFAULT GETDATE()
);
```

### Exemplo de INSERT

```sql
-- Substitua o hash pelo valor gerado pelo gerar_hashes.py
INSERT INTO usuarios (username, senha_hash, display_name, aplicacoes, ativo)
VALUES (
    'admin',
    '$2b$12$HASH_GERADO_AQUI',
    'Administrador',
    '["AtualizaBI_TI","AtualizaBI_Financeiro"]',
    1
);
```

### Campo `aplicacoes`

Armazena um array JSON com os IDs das tarefas agendadas que o usuário tem permissão de executar:

```json
["AtualizaBI_TI", "AtualizaBI_Financeiro", "AtualizaBI_Margens"]
```

### Tarefas disponíveis

| ID da Tarefa | Nome de Exibição |
|---|---|
| `AtualizaBI_AcomSemanalDesp` | Acomp. Semanal |
| `AtualizaBI_Despesas` | Despesas |
| `AtualizaBI_FCST` | Forecast |
| `AtualizaBI_Financeiro` | Financeiro |
| `AtualizaBI_Manutencao` | Manutenção |
| `AtualizaBI_Margens` | Margens |
| `AtualizaBI_Orcamento` | Orçamento |
| `AtualizaBI_QL_RH` | RH / QL |
| `AtualizaBI_Suprimentos` | Suprimentos |
| `AtualizaBI_TI` | TI |

---

## Referência da API

Base URL: `http://<SERVIDOR>:5000`

### Endpoints públicos (sem autenticação)

#### `GET /health`
Verifica se a API está no ar.

```json
// 200 OK
{
  "status": "ok",
  "timestamp": "2024-02-17T10:30:00.123456",
  "mensagem": "API de atualização do BI está funcionando"
}
```

#### `GET /status`
Retorna a configuração ativa (servidor e tarefa padrão).

#### `GET /info`
Lista todos os endpoints disponíveis e instrução de autenticação.

#### `POST /login`
Autentica o usuário e retorna seus dados e permissões.

**Request body:**
```json
{
  "username": "financeiro",
  "password": "sua-senha"
}
```

**Response 200:**
```json
{
  "username": "financeiro",
  "displayName": "Financeiro",
  "applications": ["AtualizaBI_Financeiro", "AtualizaBI_Margens"]
}
```

**Response 401:**
```json
{ "mensagem": "Usuário ou senha incorretos" }
```

---

### Endpoints protegidos

Todos requerem o header:
```
Authorization: Bearer <API_TOKEN>
```

#### `POST /atualizar-bi`
Dispara a tarefa agendada padrão (definida em `TASK_NAME` no `.env`).

**Response 202:**
```json
{
  "timestamp": "2024-02-17T10:30:00.123456",
  "status": "sucesso",
  "mensagem": "Atualização iniciada com sucesso",
  "ip_cliente": "192.168.1.100"
}
```

#### `POST /executar-tarefa/<nome_da_tarefa>`
Dispara uma tarefa específica pelo ID.

```bash
POST /executar-tarefa/AtualizaBI_Financeiro
```

#### `GET /tarefas`
Lista todas as tarefas disponíveis no sistema.

#### `GET /usuarios`
Lista todos os usuários cadastrados.

#### `GET /usuarios/<username>`
Retorna os dados de um usuário específico.

#### `POST /usuarios`
Cria um novo usuário.

**Request body:**
```json
{
  "username": "novo_usuario",
  "password": "senha-segura",
  "display_name": "Nome de Exibição",
  "aplicacoes": ["AtualizaBI_TI"],
  "ativo": 1
}
```

#### `PUT /usuarios/<username>`
Atualiza dados do usuário (envie apenas os campos a alterar). Para alterar a senha, inclua `"password"` no body.

#### `PUT /usuarios/<username>/toggle`
Alterna o status ativo/inativo do usuário.

---

### Testando a API

```bash
# Health check
curl http://localhost:5000/health

# Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua-senha"}'

# Disparar tarefa
curl -X POST http://localhost:5000/atualizar-bi \
  -H "Authorization: Bearer seu-token-aqui"

# Ou use o script de testes incluso:
python teste_api.py
```

---

## Frontend

### Páginas

| Arquivo | Descrição |
|---|---|
| `login.html` | Tela de autenticação. Chama `POST /login` e salva o retorno em `sessionStorage`. |
| `dashboard.html` | Painel principal. Exibe apenas as aplicações do usuário logado. Permite selecionar múltiplas tarefas e executá-las. Admins veem configurações extras. |
| `admin.html` | Painel de gerenciamento de usuários. Acessível apenas para o usuário `admin`. |

### Autenticação no frontend

O login retorna um objeto JSON que é salvo em `sessionStorage` com a chave `userData`:

```json
{
  "username": "financeiro",
  "displayName": "Financeiro",
  "applications": ["AtualizaBI_Financeiro"]
}
```

Todas as páginas verificam `sessionStorage` ao carregar e redirecionam para `login.html` se não houver sessão ativa.

### Configuração da URL da API

A URL da API está definida diretamente nas páginas HTML na variável `API_URL`. Atualize-a se o servidor mudar:

```javascript
// Em login.html, dashboard.html e admin.html
const API_URL = 'http://192.168.0.210:5000';
```

---

## Hospedagem no IIS

### Instalação rápida via PowerShell

```powershell
# Executar como Administrador
Install-WindowsFeature -Name Web-Server -IncludeManagementTools
```

Ou use o script incluso:

```powershell
.\instalar_iis.ps1
```

### Configurar o site

```powershell
# Criar pasta e copiar arquivos
mkdir "C:\PowerBI_Web"
Copy-Item ".\*.html",".\*.css" "C:\PowerBI_Web\"
Copy-Item ".\web.config" "C:\PowerBI_Web\"

# Criar site no IIS
New-IISSite -Name "PowerBI_Panel" `
            -BindingInformation "*:80:" `
            -PhysicalPath "C:\PowerBI_Web"

# Permissões
icacls "C:\PowerBI_Web" /grant "IIS_IUSRS:(OI)(CI)F"
```

O arquivo `web.config` já está configurado para servir `login.html` como documento padrão.

Para um guia completo com configurações de DNS e HTTPS, veja [GUIA_IIS.md](./GUIA_IIS.md).

---

## Segurança

### Boas práticas implementadas

- Senhas armazenadas com hash **bcrypt**
- Autenticação via **Bearer Token** no header HTTP
- Tentativas de acesso inválidas registradas em log com IP do cliente
- Usuários inativos não conseguem autenticar
- Controle de acesso por aplicação no nível do banco de dados

### Recomendações para produção

- **Troque o `API_TOKEN`** para um valor seguro gerado com `secrets.token_urlsafe(32)`
- **Não versione o `.env`** — adicione-o ao `.gitignore`
- Configure **HTTPS/TLS** no IIS e rode a API atrás de um proxy reverso (nginx, IIS ARR)
- Restrinja o acesso à porta `5000` no firewall, liberando apenas IPs autorizados
- Monitore o arquivo `api_bi.log` regularmente

### .gitignore recomendado

```
.env
api_bi.log
__pycache__/
*.pyc
*.pyo
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'flask'`**
```bash
pip install flask --break-system-packages
```

**Porta 5000 já em uso**
```bash
# Verificar o processo na porta
netstat -ano | findstr :5000
# Matar o processo pelo PID
taskkill /PID <PID> /F
```

**Erro de conexão com SQL Server**
- Confirme que o ODBC Driver 17 está instalado
- Verifique as credenciais no `.env`
- Certifique-se que a porta 1433 está acessível no firewall

**`Acesso negado` ao executar `schtasks`**
- O usuário que executa a API precisa de permissão para acionar tarefas remotas no servidor BI
- Verifique se o servidor BI está acessível na rede

**Erros de CORS no browser**
- A API usa `flask-cors` e está configurada para aceitar qualquer origem
- Em produção, restrinja as origens permitidas no `CORS(app, origins=[...])`

---

## Licença

Uso interno. Consulte o responsável pelo projeto para redistribuição.
