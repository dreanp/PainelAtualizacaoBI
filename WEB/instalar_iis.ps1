# ============================================================================
# Script de Instalação Automática - Painel Power BI no IIS
# ============================================================================
# Este script automatiza toda a configuração do IIS para hospedar o painel
# Execute como Administrador!
# ============================================================================

param(
    [string]$SiteName = "PowerBI_Panel",
    [string]$PhysicalPath = "C:\PowerBI_Web",
    [string]$Port = 80,
    [string]$HostName = ""
)

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          Configurador - Painel Power BI no IIS                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar se é administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "❌ ERRO: Este script precisa ser executado como Administrador!" -ForegroundColor Red
    Write-Host "Clique direito em PowerShell → Executar como Administrador" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Executando como Administrador" -ForegroundColor Green
Write-Host ""

# ============================================================================
# PASSO 1: Verificar IIS
# ============================================================================
Write-Host "📋 PASSO 1: Verificando IIS..." -ForegroundColor Yellow

$iisFeature = Get-WindowsFeature -Name Web-Server
if ($iisFeature.Installed) {
    Write-Host "✅ IIS já está instalado" -ForegroundColor Green
} else {
    Write-Host "⚙️  Instalando IIS (isso pode levar alguns minutos)..." -ForegroundColor Cyan
    Install-WindowsFeature -Name Web-Server -IncludeManagementTools
    Write-Host "✅ IIS instalado com sucesso" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# PASSO 2: Criar pasta
# ============================================================================
Write-Host "📂 PASSO 2: Criando/Verificando pasta..." -ForegroundColor Yellow

if (Test-Path $PhysicalPath) {
    Write-Host "✅ Pasta já existe: $PhysicalPath" -ForegroundColor Green
} else {
    Write-Host "➕ Criando pasta: $PhysicalPath" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $PhysicalPath -Force | Out-Null
    Write-Host "✅ Pasta criada" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# PASSO 3: Copiar arquivo HTML
# ============================================================================
Write-Host "📄 PASSO 3: Copiando arquivo HTML..." -ForegroundColor Yellow

$sourceFile = Read-Host "📍 Caminho do arquivo painel_bi_v2.html"

if (Test-Path $sourceFile) {
    Copy-Item -Path $sourceFile -Destination "$PhysicalPath\index.html" -Force
    Write-Host "✅ Arquivo copiado para $PhysicalPath\index.html" -ForegroundColor Green
} else {
    Write-Host "❌ Arquivo não encontrado: $sourceFile" -ForegroundColor Red
    Write-Host "Coloque o arquivo e tente novamente" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# ============================================================================
# PASSO 4: Configurar Permissões
# ============================================================================
Write-Host "🔐 PASSO 4: Configurando permissões de pasta..." -ForegroundColor Yellow

$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "IIS_IUSRS",
    "FullControl",
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl = Get-Acl $PhysicalPath
$acl.AddAccessRule($rule)
Set-Acl -Path $PhysicalPath -AclObject $acl

Write-Host "✅ Permissões configuradas para IIS_IUSRS" -ForegroundColor Green
Write-Host ""

# ============================================================================
# PASSO 5: Configurar IIS
# ============================================================================
Write-Host "⚙️  PASSO 5: Configurando IIS..." -ForegroundColor Yellow

Import-Module WebAdministration

$siteName = $SiteName
$existingSite = Get-IISSite -Name $siteName -ErrorAction SilentlyContinue

if ($existingSite) {
    Write-Host "⚠️  Site '$siteName' já existe" -ForegroundColor Yellow
    $removeOld = Read-Host "Deseja remover e recriar? (S/N)"
    
    if ($removeOld -eq "S" -or $removeOld -eq "s") {
        Write-Host "🗑️  Removendo site anterior..." -ForegroundColor Cyan
        Remove-IISSite -Name $siteName -Confirm:$false
        Start-Sleep -Seconds 2
    } else {
        Write-Host "⏭️  Mantendo configuração anterior" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "✅ Configuração concluída!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Acesse o site em:" -ForegroundColor Cyan
        Write-Host "  http://localhost:$Port" -ForegroundColor White
        exit 0
    }
}

# Criar binding
$binding = "*:$($Port):"
if ($HostName) {
    $binding = "*:$($Port):$HostName"
}

Write-Host "➕ Criando site '$siteName'..." -ForegroundColor Cyan
New-IISSite -Name $siteName `
            -BindingInformation $binding `
            -PhysicalPath $PhysicalPath `
            -Force | Out-Null

Write-Host "✅ Site criado: $siteName" -ForegroundColor Green

# Iniciar site
Write-Host "▶️  Iniciando site..." -ForegroundColor Cyan
Start-IISSite -Name $siteName

Start-Sleep -Seconds 2

$siteStatus = (Get-IISSite -Name $siteName).State
if ($siteStatus -eq "Started") {
    Write-Host "✅ Site iniciado com sucesso" -ForegroundColor Green
} else {
    Write-Host "⚠️  Site status: $siteStatus" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# PASSO 6: Configurar DNS Local (Opcional)
# ============================================================================
Write-Host "🌐 PASSO 6: Configurar DNS (Opcional)..." -ForegroundColor Yellow

$configurarDNS = Read-Host "Deseja adicionar entrada no arquivo HOSTS? (S/N)"

if ($configurarDNS -eq "S" -or $configurarDNS -eq "s") {
    $dnsName = Read-Host "Nome DNS desejado (ex: powerbi.local)"
    $hostFile = "C:\Windows\System32\drivers\etc\hosts"
    
    # Ler arquivo hosts
    $hostsContent = Get-Content $hostFile
    
    # Verificar se entrada já existe
    if ($hostsContent -like "*$dnsName*") {
        Write-Host "⚠️  Entrada já existe no HOSTS" -ForegroundColor Yellow
    } else {
        # Adicionar nova entrada
        Add-Content -Path $hostFile -Value "192.168.0.210  $dnsName" -Encoding ASCII
        Write-Host "✅ Entrada adicionada ao HOSTS: 192.168.0.210  $dnsName" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================================
# RESUMO FINAL
# ============================================================================
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                   ✅ CONFIGURAÇÃO CONCLUÍDA!                   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📊 Informações do Site:" -ForegroundColor Cyan
Write-Host "  Nome: $siteName" -ForegroundColor White
Write-Host "  Caminho: $PhysicalPath" -ForegroundColor White
Write-Host "  Porta: $Port" -ForegroundColor White

if ($HostName) {
    Write-Host "  Host: $HostName" -ForegroundColor White
    Write-Host "  Acesso: http://$HostName" -ForegroundColor White
} else {
    Write-Host "  Acesso: http://localhost:$Port" -ForegroundColor White
    Write-Host "  Acesso: http://192.168.0.210:$Port" -ForegroundColor White
}

Write-Host ""
Write-Host "🔍 Próximos passos:" -ForegroundColor Cyan
Write-Host "  1. Abra seu navegador e acesse a URL acima" -ForegroundColor White
Write-Host "  2. Verifique se a página carrega corretamente" -ForegroundColor White
Write-Host "  3. Clique em 'Testar Conexão' para validar a API" -ForegroundColor White
Write-Host "  4. Execute uma tarefa para confirmar tudo funciona" -ForegroundColor White
Write-Host ""

Write-Host "📝 Notas:" -ForegroundColor Yellow
Write-Host "  • Se a porta 80 está em uso, tente especificar outra porta" -ForegroundColor White
Write-Host "  • Use 'Get-IISSite' para listar todos os sites" -ForegroundColor White
Write-Host "  • Logs estão em: C:\inetpub\logs\LogFiles\" -ForegroundColor White
Write-Host ""

Write-Host "Press Enter para finalizar..."
Read-Host
