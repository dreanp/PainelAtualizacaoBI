from flask import Flask, request, jsonify
from functools import wraps
import subprocess
from flask_cors import CORS
import logging
from datetime import datetime
import os
import json
import pyodbc
import bcrypt
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da aplicação
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_bi.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variáveis de ambiente
BEARER_TOKEN = os.getenv('API_TOKEN', 'seu-token-super-secreto-aqui')
SERVIDOR_BI  = os.getenv('SERVIDOR_BI', '192.168.0.210')
TASK_NAME    = os.getenv('TASK_NAME', 'AtualizaBI_TI')

DB_SERVER   = os.getenv('DB_SERVER')
DB_NAME     = os.getenv('DB_NAME')
DB_USER     = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')


# ============================================
# Conexão com SQL Server
# ============================================

def get_db_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


# ============================================
# Decorator para autenticação com Bearer Token
# ============================================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'erro': 'Formato de Authorization inválido'}), 401

        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401

        if token != BEARER_TOKEN:
            logger.warning(f'Tentativa de acesso com token inválido de {request.remote_addr}')
            return jsonify({'erro': 'Token inválido'}), 401

        return f(*args, **kwargs)

    return decorated


# ============================================
# Função para executar o schtasks
# ============================================

def executar_atualizacao():
    try:
        comando = f'schtasks /run /s {SERVIDOR_BI} /tn "{TASK_NAME}"'
        logger.info(f'Executando comando: {comando}')

        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        if resultado.returncode == 0:
            logger.info('Atualização do BI iniciada com sucesso')
            return True, 'Atualização iniciada com sucesso'
        else:
            logger.error(f'Erro ao executar schtasks: {resultado.stderr}')
            return False, f'Erro ao executar: {resultado.stderr}'

    except subprocess.TimeoutExpired:
        logger.error('Timeout ao executar o comando')
        return False, 'Timeout ao executar o comando'
    except Exception as e:
        logger.error(f'Exceção ao executar comando: {str(e)}')
        return False, f'Erro: {str(e)}'


# ============================================
# Rotas públicas (sem autenticação)
# ============================================

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'nome': 'API de Atualização do Power BI',
        'versao': '1.1.0',
        'status': 'ativo',
        'mensagem': 'Bem-vindo! Use os endpoints abaixo:',
        'endpoints': {
            'POST /login': 'Autenticação de usuário',
            'GET /health': 'Verificação de saúde da API',
            'GET /info': 'Informações detalhadas da API',
            'GET /status': 'Status da configuração',
            'POST /atualizar-bi': 'Dispara a atualização do BI (requer token Bearer)',
        },
        'documentacao': 'Veja o README.md para mais detalhes'
    }), 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'mensagem': 'API de atualização do BI está funcionando'
    }), 200


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'servidor': SERVIDOR_BI,
        'tarefa': TASK_NAME,
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/info', methods=['GET'])
def info():
    return jsonify({
        'nome': 'API de Atualização do Power BI',
        'versao': '1.1.0',
        'endpoints': {
            'POST /login': 'Autenticação de usuário',
            'POST /atualizar-bi': 'Dispara a atualização do BI (requer token)',
            'GET /health': 'Verificação de saúde da API',
            'GET /status': 'Status da configuração',
            'GET /info': 'Informações da API'
        },
        'autenticacao': 'Bearer Token no header Authorization'
    }), 200


# ============================================
# Login
# ============================================

@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()

    if not dados or 'username' not in dados or 'password' not in dados:
        return jsonify({'mensagem': 'Dados inválidos'}), 400

    username = dados['username'].strip().lower()
    password = dados['password']

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT username, senha_hash, display_name, aplicacoes
            FROM usuarios
            WHERE username = ? AND ativo = 1
        """, username)

        usuario = cursor.fetchone()
        conn.close()

        if not usuario:
            logger.warning(f'Tentativa de login com usuário inexistente: {username} | IP: {request.remote_addr}')
            return jsonify({'mensagem': 'Usuário ou senha incorretos'}), 401

        senha_correta = bcrypt.checkpw(
            password.encode('utf-8'),
            usuario.senha_hash.encode('utf-8')
        )

        if not senha_correta:
            logger.warning(f'Senha incorreta para o usuário: {username} | IP: {request.remote_addr}')
            return jsonify({'mensagem': 'Usuário ou senha incorretos'}), 401

        logger.info(f'Login bem-sucedido: {username} | IP: {request.remote_addr}')

        return jsonify({
            'username':     usuario.username,
            'displayName':  usuario.display_name,
            'applications': json.loads(usuario.aplicacoes)
        }), 200

    except Exception as e:
        logger.error(f'Erro no endpoint /login: {str(e)}')
        return jsonify({'mensagem': f'Erro interno: {str(e)}'}), 500


# ============================================
# Rotas protegidas (requerem Bearer Token)
# ============================================

@app.route('/atualizar-bi', methods=['POST'])
@token_required
def atualizar_bi():
    try:
        ip_cliente = request.remote_addr
        logger.info(f'Requisição de atualização recebida de {ip_cliente}')

        sucesso, mensagem = executar_atualizacao()

        resposta = {
            'timestamp': datetime.now().isoformat(),
            'status': 'sucesso' if sucesso else 'erro',
            'mensagem': mensagem,
            'ip_cliente': ip_cliente
        }

        return jsonify(resposta), 202 if sucesso else 500

    except Exception as e:
        logger.error(f'Erro na rota /atualizar-bi: {str(e)}')
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'status': 'erro',
            'mensagem': f'Erro interno do servidor: {str(e)}'
        }), 500


@app.route('/executar-tarefa/<task_name>', methods=['POST'])
@token_required
def executar_tarefa(task_name):
    try:
        if not all(c.isalnum() or c in '_- ' for c in task_name):
            logger.warning(f'Tentativa de executar tarefa com nome inválido: {task_name}')
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'status': 'erro',
                'mensagem': 'Nome de tarefa inválido'
            }), 400

        ip_cliente = request.remote_addr
        logger.info(f'Requisição para executar tarefa "{task_name}" recebida de {ip_cliente}')

        comando   = f'schtasks /run /s {SERVIDOR_BI} /tn "{task_name}"'
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        if resultado.returncode == 0:
            logger.info(f'Tarefa "{task_name}" iniciada com sucesso')
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'status': 'sucesso',
                'mensagem': f'Tarefa "{task_name}" iniciada com sucesso',
                'ip_cliente': ip_cliente,
                'tarefa': task_name
            }), 202
        else:
            logger.error(f'Erro ao executar tarefa "{task_name}": {resultado.stderr}')
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'status': 'erro',
                'mensagem': f'Erro ao executar tarefa: {resultado.stderr}',
                'tarefa': task_name
            }), 500

    except subprocess.TimeoutExpired:
        logger.error(f'Timeout ao executar tarefa "{task_name}"')
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'status': 'erro',
            'mensagem': 'Timeout ao executar o comando',
            'tarefa': task_name
        }), 500
    except Exception as e:
        logger.error(f'Erro na rota /executar-tarefa: {str(e)}')
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'status': 'erro',
            'mensagem': f'Erro interno do servidor: {str(e)}'
        }), 500


@app.route('/tarefas', methods=['GET'])
@token_required
def listar_tarefas():
    tarefas = [
        'AtualizaBI_AcomSemanal',
        'AtualizaBI_Despesas',
        'AtualizaBI_FCST',
        'AtualizaBI_Financeiro',
        'AtualizaBI_Manutencao',
        'AtualizaBI_Margens',
        'AtualizaBI_Orcamento',
        'AtualizaBI_QL_RH',
        'AtualizaBI_Suprimentos',
        'AtualizaBI_TI'
    ]

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'total': len(tarefas),
        'tarefas': tarefas,
        'instrucoes': 'Use POST /executar-tarefa/<nome_da_tarefa> para disparar uma tarefa'
    }), 200

# ============================================================
# Endpoints de Gerenciamento de Usuários
# Adicione este bloco ao seu app.py existente
# ============================================================

# GET /usuarios — listar todos
@app.route('/usuarios', methods=['GET'])
@token_required
def listar_usuarios():
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, display_name, aplicacoes, ativo, criado_em, atualizado_em
            FROM usuarios
            ORDER BY username
        """)
        rows = cursor.fetchall()
        conn.close()

        usuarios = [
            {
                'username':     row.username,
                'display_name': row.display_name,
                'aplicacoes':   row.aplicacoes,
                'ativo':        row.ativo,
                'criado_em':    row.criado_em.isoformat() if row.criado_em else None,
                'atualizado_em': row.atualizado_em.isoformat() if row.atualizado_em else None,
            }
            for row in rows
        ]

        return jsonify({'usuarios': usuarios}), 200

    except Exception as e:
        logger.error(f'Erro em GET /usuarios: {str(e)}')
        return jsonify({'mensagem': f'Erro interno: {str(e)}'}), 500


# GET /usuarios/<username> — buscar um usuário
@app.route('/usuarios/<username>', methods=['GET'])
@token_required
def buscar_usuario(username):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, display_name, aplicacoes, ativo
            FROM usuarios
            WHERE username = ?
        """, username)
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'mensagem': 'Usuário não encontrado'}), 404

        return jsonify({
            'usuario': {
                'username':     row.username,
                'display_name': row.display_name,
                'aplicacoes':   row.aplicacoes,
                'ativo':        row.ativo,
            }
        }), 200

    except Exception as e:
        logger.error(f'Erro em GET /usuarios/{username}: {str(e)}')
        return jsonify({'mensagem': f'Erro interno: {str(e)}'}), 500


# POST /usuarios — criar novo usuário
@app.route('/usuarios', methods=['POST'])
@token_required
def criar_usuario():
    dados = request.get_json()

    campos = ['username', 'password', 'display_name', 'aplicacoes']
    if not dados or not all(c in dados for c in campos):
        return jsonify({'mensagem': 'Campos obrigatórios: username, password, display_name, aplicacoes'}), 400

    username     = dados['username'].strip().lower()
    password     = dados['password']
    display_name = dados['display_name'].strip()
    aplicacoes   = json.dumps(dados['aplicacoes'])
    ativo        = dados.get('ativo', 1)

    try:
        senha_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        conn   = get_db_connection()
        cursor = conn.cursor()

        # Verificar se já existe
        cursor.execute("SELECT username FROM usuarios WHERE username = ?", username)
        if cursor.fetchone():
            conn.close()
            return jsonify({'mensagem': 'Usuário já existe'}), 409

        cursor.execute("""
            INSERT INTO usuarios (username, senha_hash, display_name, aplicacoes, ativo)
            VALUES (?, ?, ?, ?, ?)
        """, username, senha_hash, display_name, aplicacoes, ativo)

        conn.commit()
        conn.close()

        logger.info(f'Usuário criado: {username}')
        return jsonify({'mensagem': f'Usuário "{username}" criado com sucesso'}), 201

    except Exception as e:
        logger.error(f'Erro em POST /usuarios: {str(e)}')
        return jsonify({'mensagem': f'Erro interno: {str(e)}'}), 500


# PUT /usuarios/<username> — editar usuário
@app.route('/usuarios/<username>', methods=['PUT'])
@token_required
def editar_usuario(username):
    dados = request.get_json()
    if not dados:
        return jsonify({'mensagem': 'Dados inválidos'}), 400

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT username FROM usuarios WHERE username = ?", username)
        if not cursor.fetchone():
            conn.close()
            return jsonify({'mensagem': 'Usuário não encontrado'}), 404

        # Atualizar campos enviados
        if 'password' in dados and dados['password']:
            senha_hash = bcrypt.hashpw(dados['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("UPDATE usuarios SET senha_hash = ?, atualizado_em = GETDATE() WHERE username = ?",
                           senha_hash, username)

        if 'display_name' in dados:
            cursor.execute("UPDATE usuarios SET display_name = ?, atualizado_em = GETDATE() WHERE username = ?",
                           dados['display_name'].strip(), username)

        if 'aplicacoes' in dados:
            cursor.execute("UPDATE usuarios SET aplicacoes = ?, atualizado_em = GETDATE() WHERE username = ?",
                           json.dumps(dados['aplicacoes']), username)

        if 'ativo' in dados:
            cursor.execute("UPDATE usuarios SET ativo = ?, atualizado_em = GETDATE() WHERE username = ?",
                           dados['ativo'], username)

        conn.commit()
        conn.close()

        logger.info(f'Usuário editado: {username}')
        return jsonify({'mensagem': f'Usuário "{username}" atualizado com sucesso'}), 200

    except Exception as e:
        logger.error(f'Erro em PUT /usuarios/{username}: {str(e)}')
        return jsonify({'mensagem': f'Erro interno: {str(e)}'}), 500


# PUT /usuarios/<username>/toggle — alternar ativo/inativo
@app.route('/usuarios/<username>/toggle', methods=['PUT'])
@token_required
def toggle_usuario(username):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT ativo FROM usuarios WHERE username = ?", username)
        row = cursor.fetchone()

        if not row:
            conn.close()
            return jsonify({'mensagem': 'Usuário não encontrado'}), 404

        novo_status = 0 if row.ativo else 1
        cursor.execute("UPDATE usuarios SET ativo = ?, atualizado_em = GETDATE() WHERE username = ?",
                       novo_status, username)
        conn.commit()
        conn.close()

        status_texto = 'ativado' if novo_status else 'desativado'
        logger.info(f'Usuário {status_texto}: {username}')
        return jsonify({'mensagem': f'Usuário "{username}" {status_texto} com sucesso'}), 200

    except Exception as e:
        logger.error(f'Erro em toggle /usuarios/{username}: {str(e)}')
        return jsonify({'mensagem': f'Erro interno: {str(e)}'}), 500










# ============================================
# Manipuladores de erro
# ============================================

@app.errorhandler(404)
def nao_encontrado(error):
    return jsonify({
        'erro': 'Endpoint não encontrado',
        'timestamp': datetime.now().isoformat()
    }), 404


@app.errorhandler(405)
def metodo_nao_permitido(error):
    return jsonify({
        'erro': 'Método HTTP não permitido',
        'timestamp': datetime.now().isoformat()
    }), 405


if __name__ == '__main__':
    logger.info('Iniciando API de atualização do Power BI')
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )