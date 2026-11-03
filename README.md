# Ludenz 360 — versão desktop (Python + customtkinter)

## Como rodar (Windows)
1. Instale o Python 3.10+ (python.org) marcando "Add Python to PATH".
2. Abra o terminal dentro desta pasta e rode:

       pip install -r requirements.txt
       python main.py

3. Login de teste: **mateus@ludenz360.com.br** / senha que você definiu (padrão do banco: admin123).

O arquivo `ludenz.db` (SQLite) é criado sozinho na primeira vez, a partir da pasta `data/`.
Para recriar do zero (apaga tudo): `python setup_db.py`.

## Arquivos
- `main.py`  — interface (login, cartas, clientes, vendas, pedidos)
- `banco.py` — toda a comunicação com o banco de dados
- `setup_db.py` e `data/` — criação do banco com seus dados
