# Guia: Hospedar Painel Power BI no IIS

## Pré-requisitos

- Windows Server 2019 (você já tem)
- IIS instalado
- Permissões de administrador

## Passo 1: Verificar se IIS está instalado

Abra PowerShell como Administrador e rode:

```powershell
Get-WindowsFeature -Name Web-*
```

Se não estiver instalado, rode:

```powershell
Install-WindowsFeature -Name Web-Server -IncludeManagementTools
```

## Passo 2: Criar uma pasta para o site

Crie uma pasta para hospedar a página web:

```powershell
mkdir "C:\PowerBI_Web"
```

Coloque o arquivo **`painel_bi_v2.html`** nessa pasta com o nome `index.html`:

```powershell
Copy-Item "C:\PowerBI_API\painel_bi_v2.html" "C:\PowerBI_Web\index.html"
```

## Passo 3: Configurar o IIS

### Opção A: Usando o Gerenciador do IIS (Graphical)

1. Abra **Gerenciador do IIS** (busque por "IIS" no iniciar)
2. No painel esquerdo, expanda seu servidor
3. Clique com botão direito em **"Sites"** → **"Adicionar site"**

Configure assim:
- **Nome do Site**: PowerBI_Panel
- **Pool de Aplicativos**: DefaultAppPool
- **Binding (tipo)**: http
- **Binding (IP)**: All Unassigned
- **Binding (Porta)**: 80 (ou 8080 se 80 estiver em uso)
- **Binding (Nome do host)**: deixe em branco por enquanto
- **Caminho físico**: C:\PowerBI_Web

4. Clique em **OK**

### Opção B: Usando PowerShell (Mais Rápido)

```powershell
# Criar pool de aplicativos
New-IISAppPool -Name "PowerBIAppPool"

# Criar site
New-IISSite -Name "PowerBI_Panel" -BindingInformation "*:80:" -PhysicalPath "C:\PowerBI_Web" -ApplicationPool "PowerBIAppPool"

# Iniciar o site
Start-IISSite -Name "PowerBI_Panel"
```

## Passo 4: Configurar Permissões de Pasta

O IIS precisa de permissão para acessar a pasta:

1. Clique direito em **C:\PowerBI_Web** → **Propriedades**
2. Vá para aba **Segurança**
3. Clique em **Editar**
4. Selecione **IIS_IUSRS** (ou **IUSR**)
5. Marque **Controle Total** → **OK**

Ou via PowerShell:

```powershell
$folderPath = "C:\PowerBI_Web"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "IIS_IUSRS",
    "FullControl",
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl = Get-Acl $folderPath
$acl.AddAccessRule($rule)
Set-Acl -Path $folderPath -AclObject $acl
```

## Passo 5: Testar o Acesso

Abra seu navegador e acesse:

```
http://localhost/
```

ou

```
http://192.168.0.210/
```

Se ver a página carregada, sucesso! 🎉

## Passo 6: Configurar DNS (Opcional mas Recomendado)

### Opção A: DNS Interno (Rede Local)

Se você tem um servidor DNS interno (como Active Directory):

1. Acesse o gerenciador DNS
2. Crie um novo registro A
3. **Nome**: powerbi (ou powerbi-panel)
4. **IP**: 192.168.0.210
5. **Salvar**

Depois acesse: `http://powerbi` ou `http://powerbi-panel`

### Opção B: Arquivo HOSTS (Teste Local)

Para testar localmente sem DNS:

1. Abra `C:\Windows\System32\drivers\etc\hosts` (como Administrador)
2. Adicione a linha:

```
192.168.0.210  powerbi.local
```

3. Salve o arquivo
4. Acesse: `http://powerbi.local`

### Opção C: DNS Externo (Com Domínio Real)

Se você tem um domínio (ex: empresa.com):

1. Acesse o painel do seu registrador de domínio (GoDaddy, Namecheap, etc)
2. Crie um registro A:
   - **Host**: powerbi
   - **IP**: seu IP público (não local!)
3. Salve

Depois acesse: `http://powerbi.empresa.com`

**⚠️ Nota**: Isso requer configurar seu roteador para encaminhar porta 80 para seu servidor interno.

## Passo 7: Configurar HTTPS (SSL/TLS)

### Criar Certificado Auto-Assinado (para teste)

```powershell
$cert = New-SelfSignedCertificate -DnsName "powerbi.local" -CertStoreLocation "cert:\LocalMachine\My"
```

### Vincular ao IIS

1. No Gerenciador IIS, selecione seu site
2. Clique em **Bindings** (painel direito)
3. Clique em **Add**
4. Tipo: **https**
5. Porta: **443**
6. Certificado SSL: selecione o certificado criado
7. **OK**

## Passo 8: Configurar a Página para Usar HTTPS

Se você ativou HTTPS, atualize a URL na página web:

Abra `index.html` e mude:

```javascript
value="http://192.168.0.210:5000"
```

Para:

```javascript
value="https://192.168.0.210:5000"
```

(Se a API também tiver SSL)

## Troubleshooting

### Porta 80 já em uso

Se a porta 80 está ocupada, use outra:

```powershell
netstat -ano | findstr :80
```

Se retornar algo, mude para porta 8080:

```powershell
New-IISSite -Name "PowerBI_Panel" -BindingInformation "*:8080:" -PhysicalPath "C:\PowerBI_Web"
```

Acesse: `http://192.168.0.210:8080/`

### Erro de acesso negado

Verifique as permissões:

```powershell
icacls "C:\PowerBI_Web"
```

Deve mostrar IIS_IUSRS com (F) ou (M) (Full ou Modify).

### Site não inicia

Verifique o log do IIS:

```powershell
Get-Content "C:\inetpub\logs\LogFiles\W3SVC1\*.log" -Tail 20
```

## Conclusão

Você terá:
- ✅ Página web hospedada no IIS
- ✅ Acessível via HTTP/HTTPS
- ✅ Com DNS local ou externo
- ✅ Conectando com a API Python sem problemas CORS

Próximos passos:
1. Testar acesso via navegador
2. Configurar agendamento das tarefas (opcional)
3. Monitorar logs da API
