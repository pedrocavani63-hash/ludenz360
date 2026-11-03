# =============================================================================
#  LUDENZ 360 (desktop) — banco.py
#  TODA a conversa com o banco de dados (ludenz.db) fica neste arquivo.
#  A interface (main.py) só chama estas funções e nunca escreve SQL.
#
#    1. CONEXÃO E FORMATOS ... abrir o banco, R$, datas
#    2. LOGIN ................ conferir usuário e senha
#    3. CARTAS ............... listar e salvar estoque/preço
#    4. CLIENTES ............. listar e cadastrar
#    5. VENDAS ............... buscar cartas, indicadores e finalizar venda
#    6. PEDIDOS .............. histórico e detalhes
# =============================================================================
import hashlib, hmac, os, re, sqlite3
from datetime import datetime

import setup_db  # cria o ludenz.db a partir da pasta data/ na primeira vez

POR_PAGINA = 25  # itens por página nas listas


# ---------------------------------------------------------------------------
#  1. CONEXÃO E FORMATOS
# ---------------------------------------------------------------------------
_vendas_ok = False  # só confere o histórico de vendas uma vez por execução


def conectar():
    """Abre o banco (e cria na primeira execução). Linhas acessíveis por nome de coluna."""
    global _vendas_ok
    if not os.path.exists(setup_db.DB):
        setup_db.criar()
    if not _vendas_ok:
        setup_db.garantir_vendas()  # se faltar o histórico de vendas, gera (sem apagar nada)
        _vendas_ok = True
    con = sqlite3.connect(setup_db.DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def consulta(sql, args=()):
    """Roda um SELECT e devolve todas as linhas."""
    con = conectar()
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def brl(v):
    """1234.5 -> 'R$ 1.234,50'"""
    if v is None:
        return "—"
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def usd(v):
    """900.48 -> 'US$ 900,48' (o preço de mercado das cartas é em dólar; o preço da loja é em reais)"""
    if v is None:
        return "—"
    return "US$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def para_float(txt):
    """'R$ 1.234,56' -> 1234.56"""
    return float((txt or "0").replace("R$", "").replace(".", "").replace(",", ".").strip() or 0)


def dt(v):
    """'2026-10-28 20:15:00' -> '28/10/2026 20:15'"""
    try:
        return datetime.strptime(v[:19], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return v or "—"


def cpf_fmt(c):
    """'12345678909' -> '123.456.789-09'"""
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" if len(c) == 11 else c


# ---------------------------------------------------------------------------
#  2. LOGIN
# ---------------------------------------------------------------------------
def entrar(ident, senha):
    """Confere e-mail/usuário + senha (hash SHA-256). Devolve o usuário ou None."""
    ident = ident.strip().lower()
    h = hashlib.sha256(senha.encode()).hexdigest()
    for u in consulta("SELECT * FROM usuario WHERE (lower(email)=? OR lower(nome_usuario)=?) AND status=1", (ident, ident)):
        if hmac.compare_digest(u["senha_hash"], h):
            return u
    return None


# ---------------------------------------------------------------------------
#  3. CARTAS
# ---------------------------------------------------------------------------
def jogos():
    return consulta("SELECT * FROM jogo ORDER BY id_jogo")


def listar_cartas(jogo, q, pagina):
    """Estoque de um jogo, com busca por nome. Devolve (linhas, total)."""
    base = """FROM carta_para_venda cv JOIN carta c ON c.id_carta=cv.id_carta
              JOIN edicao e ON e.id_edicao=c.id_edicao JOIN raridade r ON r.id_raridade=c.id_raridade
              JOIN acabamento a ON a.id_acab=c.id_acab WHERE e.id_jogo=? AND c.nome_carta LIKE ?"""
    args = (jogo, f"%{q}%")
    total = consulta("SELECT COUNT(*) AS n " + base, args)[0]["n"]
    rows = consulta(f"""SELECT cv.id_carta_venda, c.nome_carta, c.preco_mercado, e.sigla_edicao, r.sigla AS raridade,
        a.tipo_acab, cv.idioma, cv.condicao, cv.estoque, cv.preco_negocio {base}
        ORDER BY c.nome_carta, cv.id_carta_venda LIMIT ? OFFSET ?""", args + (POR_PAGINA, (pagina - 1) * POR_PAGINA))
    return rows, total


def salvar_estoque(itens):
    """itens = [(id_carta_venda, 'estoque', 'preço')]. Tudo ou nada."""
    con = conectar()
    try:
        for i, est, preco in itens:
            con.execute("UPDATE carta_para_venda SET estoque=?, preco_negocio=? WHERE id_carta_venda=?",
                        (int(est or 0), para_float(preco), i))
        con.commit()
    except (ValueError, sqlite3.IntegrityError):
        con.rollback()
        raise ValueError("Não salvou: confira se estoque e preço são números e se o estoque não é negativo.")
    finally:
        con.close()


# ---------------------------------------------------------------------------
#  4. CLIENTES
# ---------------------------------------------------------------------------
def listar_clientes(q=""):
    like = f"%{q}%"
    return consulta("""SELECT c.*, e.cidade FROM cliente c LEFT JOIN endereco e ON e.id_cliente=c.id_cliente
        WHERE c.nome_completo LIKE ? OR c.cpf LIKE ? OR c.telefone LIKE ? OR c.email LIKE ?
        ORDER BY c.nome_completo LIMIT 100""", (like,) * 4)


def salvar_cliente(f):
    """f = dicionário com os campos do formulário. Levanta ValueError com a mensagem de erro."""
    f = {k: (v or "").strip() for k, v in f.items()}
    f["cpf"] = re.sub(r"\D", "", f.get("cpf", ""))
    obrig = ["nome_completo", "cpf", "telefone", "email", "data_nascimento", "genero"]
    end = ["cep", "logradouro", "numero", "bairro", "cidade", "estado"]
    if not all(f.get(k) for k in obrig) or len(f["cpf"]) != 11:
        raise ValueError("Preencha nome, CPF (11 números), telefone, e-mail, nascimento e gênero.")
    try:
        f["data_nascimento"] = datetime.strptime(f["data_nascimento"], "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Data de nascimento inválida. Use dd/mm/aaaa.")
    if any(f.get(k) for k in end) and not all(f.get(k) for k in end):
        raise ValueError("Para salvar o endereço, preencha CEP, rua, número, bairro, cidade e UF.")
    con = conectar()
    try:
        cur = con.execute("""INSERT INTO cliente(nome_completo,cpf,telefone,email,data_nascimento,genero)
                             VALUES(?,?,?,?,?,?)""", [f[k] for k in obrig])
        if f.get("cep"):
            con.execute("""INSERT INTO endereco(cep,lagradouro,numero,bairro,cidade,estado,id_cliente)
                           VALUES(?,?,?,?,?,?,?)""", [f[k] for k in end] + [cur.lastrowid])
        con.commit()
    except sqlite3.IntegrityError:
        con.rollback()
        raise ValueError("Esse CPF já está cadastrado.")
    finally:
        con.close()


# ---------------------------------------------------------------------------
#  5. VENDAS
# ---------------------------------------------------------------------------
def clientes_opcoes():
    return consulta("SELECT id_cliente, nome_completo FROM cliente ORDER BY nome_completo")


def formas_pagamento():
    return consulta("SELECT * FROM forma_pagamento ORDER BY id_forma_pagamento")


def indicadores():
    """Vendido hoje, vendido no mês e quantidade de vendas no mês."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    mes = hoje[:7]
    return consulta("""SELECT
        COALESCE(SUM(CASE WHEN substr(data_hora,1,10)=? THEN valor_total END),0) AS hoje,
        COALESCE(SUM(CASE WHEN substr(data_hora,1,7)=? THEN valor_total END),0) AS mes,
        COUNT(CASE WHEN substr(data_hora,1,7)=? THEN 1 END) AS qtd FROM venda""", (hoje, mes, mes))[0]


def buscar_para_venda(q):
    """Cartas com estoque cujo nome contém q (máx. 20)."""
    return consulta("""SELECT cv.id_carta_venda, c.nome_carta, e.sigla_edicao, cv.idioma, cv.condicao, cv.estoque,
        cv.preco_negocio AS preco
        FROM carta_para_venda cv JOIN carta c ON c.id_carta=cv.id_carta JOIN edicao e ON e.id_edicao=c.id_edicao
        WHERE c.nome_carta LIKE ? AND cv.estoque>0 AND cv.preco_negocio IS NOT NULL ORDER BY c.nome_carta LIMIT 20""", (f"%{q}%",))


def finalizar_venda(usuario, id_cliente, id_forma, carrinho):
    """carrinho = [(id_carta_venda, quantidade)]. Cria a venda, os itens e baixa o estoque.
    Tudo ou nada. O preço é lido do banco na hora. Devolve (id_venda, total)."""
    if not carrinho:
        raise ValueError("O carrinho está vazio. Adicione pelo menos uma carta.")
    con = conectar()
    try:
        uid = con.execute("SELECT id_usuario FROM usuario WHERE nome_usuario=?", (usuario,)).fetchone()["id_usuario"]
        itens, total = [], 0.0
        for i, q in carrinho:
            r = con.execute("""SELECT cv.id_carta_venda, c.nome_carta, cv.preco_negocio AS preco
                FROM carta_para_venda cv JOIN carta c ON c.id_carta=cv.id_carta WHERE cv.id_carta_venda=?""", (i,)).fetchone()
            itens.append((r, q, round(r["preco"] * q, 2)))
            total += round(r["preco"] * q, 2)
        total = round(total, 2)
        cur = con.execute("INSERT INTO venda(data_hora,valor_total,id_usuario,id_cliente,id_forma_pagamento) VALUES(?,?,?,?,?)",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, uid, id_cliente, id_forma))
        for r, q, sub in itens:
            ok = con.execute("UPDATE carta_para_venda SET estoque=estoque-? WHERE id_carta_venda=? AND estoque>=?",
                             (q, r["id_carta_venda"], q)).rowcount
            if not ok:
                raise ValueError(f"Estoque insuficiente para {r['nome_carta']}.")
            con.execute("INSERT INTO item_venda(quantidade,preco_unitario,subtotal,id_carta_venda,id_venda) VALUES(?,?,?,?,?)",
                        (q, r["preco"], sub, r["id_carta_venda"], cur.lastrowid))
        con.commit()
        return cur.lastrowid, total
    except sqlite3.IntegrityError:
        con.rollback()
        raise ValueError("Não foi possível finalizar: confira o cliente e a forma de pagamento.")
    except ValueError:
        con.rollback()
        raise
    finally:
        con.close()


# ---------------------------------------------------------------------------
#  6. PEDIDOS
# ---------------------------------------------------------------------------
def listar_pedidos(q, pagina):
    """Vendas (mais recentes primeiro), com busca por cliente ou número. Devolve (linhas, total)."""
    base = """FROM venda v JOIN cliente c ON c.id_cliente=v.id_cliente JOIN usuario u ON u.id_usuario=v.id_usuario
              JOIN forma_pagamento f ON f.id_forma_pagamento=v.id_forma_pagamento
              WHERE c.nome_completo LIKE ? OR CAST(v.id_venda AS TEXT)=?"""
    args = (f"%{q}%", q)
    total = consulta("SELECT COUNT(*) AS n " + base, args)[0]["n"]
    rows = consulta(f"""SELECT v.id_venda, v.data_hora, v.valor_total, c.nome_completo AS cliente,
        u.nome_usuario AS vendedor, f.forma_de_pagamento AS forma {base}
        ORDER BY v.data_hora DESC, v.id_venda DESC LIMIT ? OFFSET ?""", args + (POR_PAGINA, (pagina - 1) * POR_PAGINA))
    return rows, total


def detalhe_pedido(id_venda):
    """Devolve (venda, itens) de um pedido."""
    v = consulta("""SELECT v.*, c.nome_completo AS cliente, u.nome_usuario AS vendedor, f.forma_de_pagamento AS forma
        FROM venda v JOIN cliente c ON c.id_cliente=v.id_cliente JOIN usuario u ON u.id_usuario=v.id_usuario
        JOIN forma_pagamento f ON f.id_forma_pagamento=v.id_forma_pagamento WHERE v.id_venda=?""", (id_venda,))
    itens = consulta("""SELECT i.*, ca.nome_carta, e.sigla_edicao, cv.idioma, cv.condicao
        FROM item_venda i JOIN carta_para_venda cv ON cv.id_carta_venda=i.id_carta_venda
        JOIN carta ca ON ca.id_carta=cv.id_carta JOIN edicao e ON e.id_edicao=ca.id_edicao
        WHERE i.id_venda=? ORDER BY i.id_item_venda""", (id_venda,))
    return (v[0] if v else None), itens
