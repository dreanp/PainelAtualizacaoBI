"""
Script auxiliar para gerar os hashes bcrypt das senhas atuais.
Execute este script UMA VEZ, copie os hashes gerados e cole no SQL acima.

Instalação: pip install bcrypt
Execução:   python gerar_hashes.py
"""

import bcrypt

senhas = {
    'financeiro':    'fin@mar_27',
    'suprimentos':   'sup@mar_27',
    'manutencao':    'man@mar_27',
    'controladoria': 'con@mar_27',
    'admin':         'vJ7QiTygo9nUL3oo3KaF',
}

print("=" * 60)
print("Hashes gerados — cole nos INSERTs do SQL:")
print("=" * 60)

for usuario, senha in senhas.items():
    hash_gerado = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"\nUsuário: {usuario}")
    print(f"Hash:    {hash_gerado}")
