"""Cria o ludenz.db (SQLite) com o mesmo modelo do Ludenz_360.sql e carrega os CSVs.
Os INSERTs de jogo, acabamento, edição, raridade, usuário, cliente, endereço e forma de pagamento
são lidos direto do seu .sql. As vendas (bloco PL/pgSQL do Postgres) não são geradas aqui."""
import csv, os, random, re, sqlite3
from datetime import date, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "ludenz.db")

# --- TABELAS: mesmo modelo do Ludenz_360.sql, adaptado para SQLite ---
DDL = """
PRAGMA foreign_keys = ON;
CREATE TABLE jogo(id_jogo INTEGER PRIMARY KEY AUTOINCREMENT, nome_jogo TEXT NOT NULL);
CREATE TABLE acabamento(id_acab INTEGER PRIMARY KEY AUTOINCREMENT, tipo_acab TEXT NOT NULL, id_jogo INTEGER REFERENCES jogo(id_jogo));
CREATE TABLE edicao(id_edicao INTEGER PRIMARY KEY AUTOINCREMENT, nome_edicao TEXT NOT NULL, sigla_edicao TEXT NOT NULL,
  numero_edicao INTEGER NOT NULL, id_jogo INTEGER REFERENCES jogo(id_jogo));
CREATE TABLE raridade(id_raridade INTEGER PRIMARY KEY AUTOINCREMENT, id_jogo INTEGER REFERENCES jogo(id_jogo),
  sigla TEXT NOT NULL, nome_exibicao TEXT);
CREATE TABLE carta(id_carta INTEGER PRIMARY KEY AUTOINCREMENT, nome_carta TEXT NOT NULL, numeracao_carta TEXT NOT NULL,
  url_imagem_carta TEXT, preco_mercado NUMERIC, id_edicao INTEGER REFERENCES edicao(id_edicao),
  id_acab INTEGER REFERENCES acabamento(id_acab), id_raridade INTEGER REFERENCES raridade(id_raridade));
CREATE TABLE carta_para_venda(id_carta_venda INTEGER PRIMARY KEY AUTOINCREMENT, id_carta INTEGER REFERENCES carta(id_carta),
  idioma TEXT NOT NULL CHECK (idioma IN ('PT','EN','JP')),
  condicao TEXT NOT NULL CHECK (condicao IN ('M','NM','SP','MP','HP','DMG')),
  estoque INTEGER NOT NULL CHECK (estoque >= 0), preco_negocio NUMERIC);
CREATE TABLE usuario(id_usuario INTEGER PRIMARY KEY, nome_usuario TEXT NOT NULL, email TEXT NOT NULL, senha_hash TEXT NOT NULL,
  status INTEGER NOT NULL, cargo TEXT NOT NULL CHECK (cargo IN ('Admin','Gerente','Vendedor','Estoquista')));
CREATE TABLE cliente(id_cliente INTEGER PRIMARY KEY AUTOINCREMENT, nome_completo TEXT NOT NULL, cpf TEXT UNIQUE NOT NULL,
  telefone TEXT NOT NULL, email TEXT NOT NULL, data_nascimento TEXT NOT NULL, genero TEXT NOT NULL CHECK (genero IN ('F','M')),
  data_cadastro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE endereco(id_endereco INTEGER PRIMARY KEY AUTOINCREMENT, cep TEXT NOT NULL, lagradouro TEXT NOT NULL,
  numero TEXT NOT NULL, bairro TEXT NOT NULL, cidade TEXT NOT NULL, estado TEXT NOT NULL,
  id_cliente INTEGER REFERENCES cliente(id_cliente));
CREATE TABLE forma_pagamento(id_forma_pagamento INTEGER PRIMARY KEY, forma_de_pagamento TEXT NOT NULL);
CREATE TABLE venda(id_venda INTEGER PRIMARY KEY AUTOINCREMENT, data_hora TEXT NOT NULL, valor_total NUMERIC NOT NULL,
  id_usuario INTEGER REFERENCES usuario(id_usuario), id_cliente INTEGER REFERENCES cliente(id_cliente),
  id_forma_pagamento INTEGER REFERENCES forma_pagamento(id_forma_pagamento));
CREATE TABLE item_venda(id_item_venda INTEGER PRIMARY KEY AUTOINCREMENT, quantidade INTEGER NOT NULL,
  preco_unitario NUMERIC NOT NULL, subtotal NUMERIC NOT NULL,
  id_carta_venda INTEGER REFERENCES carta_para_venda(id_carta_venda), id_venda INTEGER REFERENCES venda(id_venda));
CREATE INDEX ix_carta_nome ON carta(nome_carta);
CREATE INDEX ix_cv_carta ON carta_para_venda(id_carta);
"""
# --- Tabelas cujos INSERTs são lidos do .sql (nesta ordem, por causa das chaves estrangeiras) ---
TABELAS = ["jogo", "acabamento", "edicao", "raridade", "usuario", "cliente", "endereco", "forma_pagamento"]


# --- Lê um CSV da pasta data/ (trocando o texto NULL por vazio de verdade) ---
def ler_csv(nome):
    with open(os.path.join(BASE, "data", nome), encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            yield {k: (None if v == "NULL" else v) for k, v in r.items()}


# --- Histórico de vendas de exemplo (de 19/04/2026 a 19/10/2026) ---
# O .sql original gera as vendas com um bloco do PostgreSQL (DO $$ ... $$) que o SQLite não entende.
# Esta função faz o mesmo em Python, com as mesmas regras: 40 a 60 vendas por dia, entre 9h e 21h59,
# 28% no "Cliente Balcão", 1 a 3 cartas diferentes por venda (só cartas de até R$ 20, as mais
# baratas saem mais), quantidade limitada ao estoque, e o estoque é baixado a cada venda.
def gerar_vendas(con, semente=2026):
    rnd = random.Random(semente)
    r = rnd.random
    clientes = [(i, str(c)[:19]) for i, c in con.execute("SELECT id_cliente, data_cadastro FROM cliente WHERE id_cliente<>1")]
    pool = {i: [1.0 + p * 2.5, p, e] for i, p, e in con.execute(
        "SELECT id_carta_venda, preco_negocio, estoque FROM carta_para_venda "
        "WHERE estoque>0 AND preco_negocio BETWEEN 0.01 AND 20")}   # id -> [peso, preço, estoque]
    mudou, dia = {}, date(2026, 4, 19)
    while dia <= date(2026, 10, 19):
        for _ in range(40 + int(r() * 21)):
            hora = datetime(dia.year, dia.month, dia.day, 9 + int(r() * 13), int(r() * 60), int(r() * 60)).strftime("%Y-%m-%d %H:%M:%S")
            cli = 1
            if r() >= 0.28:  # clientes só compram depois da data de cadastro
                ok = [i for i, c in clientes if c <= hora]
                cli = rnd.choice(ok) if ok else 1
            usuario = 1 if r() < 0.65 else 2
            pgto = 1 if r() < 0.42 else 2 if r() < 0.72 else 3 if r() < 0.88 else 4
            itens, usados = [], set()
            for _ in range(1 + int(r() * 3)):
                cand = [(r() * w, i) for i, (w, p, e) in pool.items() if i not in usados]
                if not cand:
                    break
                i = min(cand)[1]
                _, p, e = pool[i]
                qtd = min(1 + int(r() * (4 if p <= 1 else 3 if p <= 5 else 2)), e)
                itens.append((i, qtd, p, round(p * qtd, 2))); usados.add(i)
            total = round(sum(x[3] for x in itens), 2)
            if total <= 0:
                continue
            vid = con.execute("INSERT INTO venda(data_hora,valor_total,id_usuario,id_cliente,id_forma_pagamento) VALUES(?,?,?,?,?)",
                              (hora, total, usuario, cli, pgto)).lastrowid
            con.executemany("INSERT INTO item_venda(quantidade,preco_unitario,subtotal,id_carta_venda,id_venda) VALUES(?,?,?,?,?)",
                            [(q, p, sub, i, vid) for i, q, p, sub in itens])
            for i, q, p, sub in itens:  # baixa o estoque
                pool[i][2] -= q
                mudou[i] = pool[i][2]
                if pool[i][2] <= 0:
                    del pool[i]
        dia = date.fromordinal(dia.toordinal() + 1)
    con.executemany("UPDATE carta_para_venda SET estoque=? WHERE id_carta_venda=?", [(e, i) for i, e in mudou.items()])


# --- Garante que o histórico existe. Se o banco ainda não tem vendas antigas, gera (sem apagar nada). ---
def garantir_vendas():
    con = sqlite3.connect(DB, timeout=120)
    try:
        con.execute("BEGIN IMMEDIATE")  # trava o banco: evita gerar duas vezes se dois processos abrirem juntos
        if con.execute("SELECT COUNT(*) FROM venda WHERE data_hora < '2026-10-20 00:00:00'").fetchone()[0] == 0:
            gerar_vendas(con)
        con.commit()
    finally:
        con.close()


# --- Apaga e recria o ludenz.db do zero (CUIDADO: perde tudo o que foi cadastrado) ---
def criar():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(DDL)
    sql = open(os.path.join(BASE, "data", "Ludenz_360.sql"), encoding="utf-8").read().replace("\r\n", "\n")
    for t in TABELAS:  # na ordem das chaves estrangeiras
        for m in re.finditer(rf"^INSERT INTO {t}\b.*?\n\s*;", sql, re.S | re.M | re.I):
            con.executescript(m.group(0))
    cols = ["id_carta", "nome_carta", "numeracao_carta", "url_imagem_carta", "preco_mercado", "id_edicao", "id_acab", "id_raridade"]
    con.executemany(f"INSERT INTO carta({','.join(cols)}) VALUES({','.join('?'*len(cols))})",
                    [[r[c] for c in cols] for r in ler_csv("carta.csv")])
    cols = ["id_carta", "idioma", "condicao", "estoque", "preco_negocio"]
    con.executemany(f"INSERT INTO carta_para_venda({','.join(cols)}) VALUES({','.join('?'*len(cols))})",
                    [[r[c] for c in cols] for r in ler_csv("estoque_tcg_completo.csv")])
    gerar_vendas(con)
    con.commit()
    con.close()


if __name__ == "__main__":
    criar()
    print("ludenz.db criado.")
