# =============================================================================
#  LUDENZ 360 (desktop) — main.py
#  Interface em customtkinter. Para abrir:  python main.py
#  O banco é acessado só pelo arquivo banco.py.
#
#    1. CORES E PEÇAS ........ botões, campos, textos e tabela reutilizáveis
#    2. LOGIN ................ tela de entrada
#    3. CARTAS ............... estoque e preço
#    4. CLIENTES ............. cadastro e busca
#    5. VENDAS ............... carrinho e finalizar venda
#    6. PEDIDOS .............. histórico e janela de detalhes
#    7. JANELA PRINCIPAL ..... menu, avisos e troca de telas
# =============================================================================
import customtkinter as ctk

import banco as bd

ctk.set_appearance_mode("dark")

# =============================================================================
#  1. CORES E PEÇAS REUTILIZÁVEIS
# =============================================================================
AM, PR, CARD, BORDA, CAMPO = "#FFC857", "#14120F", "#1F1C17", "#8A826F", "#2A261F"   # amarelo, preto, cartão, borda, campo
TX, MU, LK, OK, ER = "#F5F1E8", "#D9D2C3", "#7DD3FC", "#7EE2A8", "#FF9B9B"            # texto, texto fraco, link, ok, erro


def botao(m, t, cmd, pri=False, **kw):
    """Botão. pri=True deixa amarelo (ação principal); senão fica só com contorno."""
    return ctk.CTkButton(m, text=t, command=cmd, height=kw.pop("height", 38), font=("Segoe UI", 13, "bold"),
                         fg_color=AM if pri else "transparent", text_color=PR if pri else TX,
                         hover_color="#FFD98A" if pri else "#3A352D", border_width=0 if pri else 2,
                         border_color=BORDA, **kw)


def campo(m, ph="", **kw):
    """Caixa de texto."""
    return ctk.CTkEntry(m, placeholder_text=ph, height=36, fg_color=CAMPO, border_color=BORDA,
                        border_width=1.5, text_color=TX, **kw)


def texto(m, t, cor=TX, tam=13, neg=False, **kw):
    return ctk.CTkLabel(m, text=t, text_color=cor, font=("Segoe UI", tam, "bold" if neg else "normal"),
                        anchor="w", justify="left", **kw)


def titulo(m, t):
    return ctk.CTkLabel(m, text=t.upper(), text_color=TX, font=("Bahnschrift", 30, "bold"), anchor="w")


def tx(t, cor=TX, neg=False):
    """Atalho: célula de tabela com texto colorido."""
    return lambda m: texto(m, t, cor, 13, neg)


def cartao(m, **kw):
    return ctk.CTkFrame(m, fg_color=CARD, border_width=1, border_color=BORDA, corner_radius=12, **kw)


class Tabela(ctk.CTkScrollableFrame):
    """Tabela com rolagem. colunas = [(título, largura)]. A 1ª coluna estica."""

    def __init__(self, m, colunas, **kw):
        super().__init__(m, fg_color=CARD, border_width=1, border_color=BORDA, corner_radius=12, **kw)
        self.cols, self.n = colunas, 0
        self.linha([c[0] for c in colunas], cab=True)

    def linha(self, celulas, cab=False):
        """Uma linha. Cada célula é um texto ou uma função f(master) que devolve um widget."""
        r = ctk.CTkFrame(self, fg_color=CAMPO if cab else ("#1A1814" if self.n % 2 else CARD), corner_radius=0)
        r.pack(fill="x")
        for j, (_, larg) in enumerate(self.cols):
            r.grid_columnconfigure(j, minsize=larg, weight=1 if j == 0 else 0)
        for j, c in enumerate(celulas):
            w = texto(r, c, MU if cab else TX, 12 if cab else 13, cab) if isinstance(c, str) else c(r)
            w.grid(row=0, column=j, sticky="ew", padx=6, pady=4)
        if not cab:
            self.n += 1

    def limpar(self):
        for w in self.winfo_children()[1:]:  # mantém o cabeçalho
            w.destroy()
        self.n = 0


def entrada_na_tabela(guarda, chave, valor, larg, alinhar):
    """Cria um campo editável dentro de uma linha e guarda a referência em guarda[chave]."""
    def f(m):
        e = campo(m, width=larg, justify=alinhar)
        e.insert(0, valor)
        guarda[chave] = e
        return e
    return f


def paginador(m, anterior, proxima):
    """Devolve (frame, rótulo, botão anterior, botão próxima)."""
    f = ctk.CTkFrame(m, fg_color="transparent")
    ba, info, bp = botao(f, "Anterior", anterior, width=90), texto(f, "", MU), botao(f, "Próxima", proxima, width=90)
    ba.pack(side="left", padx=6); info.pack(side="left", padx=6); bp.pack(side="left", padx=6)
    return f, info, ba, bp


# =============================================================================
#  2. LOGIN
# =============================================================================
class TelaLogin(ctk.CTkFrame):
    def __init__(self, m, ao_entrar):
        super().__init__(m, fg_color=PR)
        self.ao_entrar = ao_entrar
        self.grid_columnconfigure((0, 1), weight=1, uniform="a"); self.grid_rowconfigure(0, weight=1)
        # Esquerda: painel amarelo da marca
        marca = ctk.CTkFrame(self, fg_color=AM, corner_radius=0); marca.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(marca, text="LUDENZ 360", text_color=PR, font=("Bahnschrift", 44, "bold")).pack(anchor="w", padx=48, pady=(48, 0))
        ctk.CTkLabel(marca, text="SUA LOJA DE TCG\nEM UMA TELA SÓ", text_color=PR, justify="left",
                     font=("Bahnschrift", 46, "bold")).pack(anchor="w", padx=48, pady=(140, 8))
        ctk.CTkLabel(marca, text="Estoque, cartas, vendas e clientes\nem um painel simples de usar.", text_color=PR,
                     justify="left", font=("Segoe UI", 16)).pack(anchor="w", padx=48)
        # Direita: formulário
        lado = ctk.CTkFrame(self, fg_color=PR, corner_radius=0); lado.grid(row=0, column=1, sticky="nsew")
        f = ctk.CTkFrame(lado, fg_color="transparent"); f.place(relx=.5, rely=.5, anchor="center")
        titulo(f, "Entrar").pack(anchor="w")
        texto(f, "Acesse o painel da sua loja.", MU).pack(anchor="w", pady=(0, 18))
        self.erro = texto(f, "", ER); self.erro.pack(anchor="w")
        texto(f, "Login", MU, 12, True).pack(anchor="w", pady=(8, 2))
        self.u = campo(f, "e-mail ou nome de usuário", width=360); self.u.pack()
        texto(f, "Senha", MU, 12, True).pack(anchor="w", pady=(12, 2))
        self.s = campo(f, "Digite sua senha", width=360, show="•"); self.s.pack()
        botao(f, "Entrar", self.entrar, pri=True, height=48, width=360).pack(pady=(24, 0))
        self.u.bind("<Return>", lambda e: self.entrar()); self.s.bind("<Return>", lambda e: self.entrar())
        self.u.focus_set()

    def entrar(self):
        u = bd.entrar(self.u.get(), self.s.get())
        if u:
            self.ao_entrar(u["nome_usuario"])
        else:
            self.erro.configure(text="Login ou senha incorretos. Confira os dados e tente de novo.")


# =============================================================================
#  3. CARTAS — estoque e preço
# =============================================================================
class PaginaCartas(ctk.CTkFrame):
    def __init__(self, m, app):
        super().__init__(m, fg_color="transparent")
        self.app, self.jogos, self.q, self.pag, self.campos = app, bd.jogos(), "", 1, []
        self.jogo = self.jogos[0]["id_jogo"]
        topo = ctk.CTkFrame(self, fg_color="transparent"); topo.pack(fill="x")
        titulo(topo, "Cadastrar cartas").pack(side="left")
        self.abas = {}
        for j in reversed(self.jogos):  # botões dos jogos (Magic, One Piece, Pokémon)
            b = botao(topo, j["nome_jogo"], lambda i=j["id_jogo"]: self.trocar(i), width=110)
            b.pack(side="right", padx=4); self.abas[j["id_jogo"]] = b
        busca = ctk.CTkFrame(self, fg_color="transparent"); busca.pack(fill="x", pady=10)
        self.busca = campo(busca, "Buscar card pelo nome"); self.busca.pack(side="left", fill="x", expand=True)
        self.busca.bind("<Return>", lambda e: self.buscar())
        botao(busca, "Buscar", self.buscar, pri=True, width=100).pack(side="left", padx=(10, 0))
        self.tab = Tabela(self, [("Card", 300), ("Edição", 100), ("Idioma", 70), ("Condição", 80),
                                 ("Acabamento", 110), ("Estoque", 90), ("Preço da loja", 130)])
        self.tab.pack(fill="both", expand=True)
        rod = ctk.CTkFrame(self, fg_color="transparent"); rod.pack(fill="x", pady=(10, 0))
        botao(rod, "Descartar alterações", self.carregar).pack(side="left")
        botao(rod, "Salvar alterações", self.salvar, pri=True, height=46, width=200).pack(side="right")
        self.pg, self.info, self.ba, self.bp = paginador(rod, lambda: self.mover(-1), lambda: self.mover(1))
        self.pg.pack(side="right", padx=20)
        self.carregar()

    def trocar(self, i):
        self.jogo, self.pag, self.q = i, 1, ""
        self.busca.delete(0, "end"); self.carregar()

    def buscar(self):
        self.q, self.pag = self.busca.get().strip(), 1; self.carregar()

    def mover(self, d):
        self.pag += d; self.carregar()

    def carregar(self):
        """Lê do banco e redesenha a tabela da página atual."""
        for i, b in self.abas.items():
            sel = i == self.jogo
            b.configure(fg_color=AM if sel else "transparent", text_color=PR if sel else TX, border_width=0 if sel else 2)
        rows, total = bd.listar_cartas(self.jogo, self.q, self.pag)
        self.tab.limpar(); self.campos = []
        for r in rows:
            ent = {}
            falta = " · Sem estoque" if r["estoque"] == 0 else ""
            self.tab.linha([tx(f"{r['nome_carta']}\nMercado: {bd.usd(r['preco_mercado'])}{falta}", LK, True),
                            f"{r['sigla_edicao']}  {r['raridade']}", r["idioma"], r["condicao"], r["tipo_acab"],
                            entrada_na_tabela(ent, "e", str(r["estoque"]), 70, "center"),
                            entrada_na_tabela(ent, "p", bd.brl(r["preco_negocio"]), 110, "right")])
            self.campos.append((r["id_carta_venda"], ent["e"], ent["p"]))
        ini = (self.pag - 1) * bd.POR_PAGINA + 1 if total else 0
        fim = min(self.pag * bd.POR_PAGINA, total)
        self.info.configure(text=f"{ini}–{fim} de {total}")
        self.ba.configure(state="normal" if self.pag > 1 else "disabled")
        self.bp.configure(state="normal" if fim < total else "disabled")

    def salvar(self):
        try:
            bd.salvar_estoque([(i, e.get(), p.get()) for i, e, p in self.campos])
            self.app.aviso(f"{len(self.campos)} itens de estoque salvos."); self.carregar()
        except ValueError as e:
            self.app.aviso(str(e), True)


# =============================================================================
#  4. CLIENTES
# =============================================================================
class PaginaClientes(ctk.CTkFrame):
    CAMPOS = [("nome_completo", "Nome completo *"), ("cpf", "CPF *"), ("data_nascimento", "Nascimento * (dd/mm/aaaa)"),
              ("email", "E-mail *"), ("telefone", "Telefone *"), ("cep", "CEP"), ("logradouro", "Rua"),
              ("numero", "Número"), ("bairro", "Bairro"), ("cidade", "Cidade"), ("estado", "UF")]

    def __init__(self, m, app):
        super().__init__(m, fg_color="transparent")
        self.app, self.c = app, {}
        titulo(self, "Cadastrar clientes").pack(anchor="w")
        corpo = ctk.CTkFrame(self, fg_color="transparent"); corpo.pack(fill="both", expand=True, pady=10)
        # Esquerda: formulário
        form = ctk.CTkScrollableFrame(corpo, fg_color=CARD, border_width=1, border_color=BORDA, corner_radius=12, width=380)
        form.pack(side="left", fill="y", padx=(0, 14))
        for k, rot in self.CAMPOS:
            texto(form, rot, MU, 12, True).pack(anchor="w", pady=(8, 2))
            self.c[k] = campo(form, width=340); self.c[k].pack(anchor="w")
            if k == "data_nascimento":
                texto(form, "Gênero *", MU, 12, True).pack(anchor="w", pady=(8, 2))
                self.genero = ctk.CTkOptionMenu(form, values=["Selecione", "Feminino", "Masculino"], width=340,
                                                fg_color=CAMPO, button_color=BORDA, text_color=TX)
                self.genero.pack(anchor="w")
        rod = ctk.CTkFrame(form, fg_color="transparent"); rod.pack(fill="x", pady=16)
        botao(rod, "Limpar", self.limpar, width=100).pack(side="left")
        botao(rod, "Salvar cliente", self.salvar, pri=True, height=44, width=200).pack(side="right")
        # Direita: busca e lista
        dir_ = ctk.CTkFrame(corpo, fg_color="transparent"); dir_.pack(side="left", fill="both", expand=True)
        b = ctk.CTkFrame(dir_, fg_color="transparent"); b.pack(fill="x", pady=(0, 10))
        self.busca = campo(b, "Buscar por nome, CPF, telefone ou e-mail"); self.busca.pack(side="left", fill="x", expand=True)
        self.busca.bind("<Return>", lambda e: self.carregar())
        botao(b, "Buscar", self.carregar, pri=True, width=100).pack(side="left", padx=(10, 0))
        self.tab = Tabela(dir_, [("Nome", 200), ("CPF", 130), ("Telefone", 120), ("E-mail", 200), ("Cidade", 110)])
        self.tab.pack(fill="both", expand=True)
        self.carregar()

    def carregar(self):
        self.tab.limpar()
        for r in bd.listar_clientes(self.busca.get().strip()):
            self.tab.linha([tx(r["nome_completo"], TX, True), bd.cpf_fmt(r["cpf"]), r["telefone"], r["email"], r["cidade"] or "—"])

    def limpar(self):
        for e in self.c.values():
            e.delete(0, "end")
        self.genero.set("Selecione")

    def salvar(self):
        f = {k: e.get() for k, e in self.c.items()}
        f["genero"] = {"Feminino": "F", "Masculino": "M"}.get(self.genero.get(), "")
        try:
            bd.salvar_cliente(f)
            self.app.aviso(f"Cliente {f['nome_completo'].strip()} salvo."); self.limpar(); self.carregar()
        except ValueError as e:
            self.app.aviso(str(e), True)


# =============================================================================
#  5. VENDAS — buscar carta -> carrinho -> cliente e pagamento -> finalizar
# =============================================================================
class PaginaVendas(ctk.CTkFrame):
    def __init__(self, m, app):
        super().__init__(m, fg_color="transparent")
        self.app, self.carrinho = app, {}   # carrinho = {id_carta_venda: {nome, preco, estoque, qtd}}
        titulo(self, "Vendas").pack(anchor="w")
        # Indicadores do topo
        k = ctk.CTkFrame(self, fg_color="transparent"); k.pack(fill="x", pady=8)
        self.kpi = []
        for rot in ("Vendido hoje", "Vendido no mês", "Vendas no mês"):
            c = cartao(k); c.pack(side="left", expand=True, fill="x", padx=(0, 10))
            texto(c, rot, MU).pack(anchor="w", padx=14, pady=(8, 0))
            v = ctk.CTkLabel(c, text="", text_color=TX, font=("Segoe UI", 24, "bold"), anchor="w"); v.pack(anchor="w", padx=14, pady=(0, 8))
            self.kpi.append(v)
        corpo = ctk.CTkFrame(self, fg_color="transparent"); corpo.pack(fill="both", expand=True)
        corpo.grid_columnconfigure(0, weight=3); corpo.grid_columnconfigure(1, weight=2); corpo.grid_rowconfigure(0, weight=1)
        # Esquerda: busca de cartas
        esq = ctk.CTkFrame(corpo, fg_color="transparent"); esq.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        texto(esq, "1. Buscar carta", AM, 16, True).pack(anchor="w", pady=(0, 6))
        b = ctk.CTkFrame(esq, fg_color="transparent"); b.pack(fill="x", pady=(0, 8))
        self.busca = campo(b, "Nome da carta (ex.: Lótus Preto)"); self.busca.pack(side="left", fill="x", expand=True)
        self.busca.bind("<Return>", lambda e: self.buscar())
        botao(b, "Buscar", self.buscar, pri=True, width=100).pack(side="left", padx=(10, 0))
        self.achados = Tabela(esq, [("Carta", 240), ("Ed.", 60), ("Estoque", 70), ("Preço", 100), ("Qtd", 60), ("", 100)])
        self.achados.pack(fill="both", expand=True)
        # Direita: carrinho
        dir_ = ctk.CTkFrame(corpo, fg_color="transparent"); dir_.grid(row=0, column=1, sticky="nsew")
        texto(dir_, "2. Carrinho", AM, 16, True).pack(anchor="w", pady=(0, 6))
        self.cart = Tabela(dir_, [("Carta", 170), ("Qtd", 45), ("Subtotal", 100), ("", 90)], height=150)
        self.cart.pack(fill="both", expand=True)
        self.total = ctk.CTkLabel(dir_, text="Total  R$ 0,00", text_color=TX, font=("Segoe UI", 22, "bold"), anchor="e")
        self.total.pack(fill="x", pady=6)
        self.cli = {f"{c['id_cliente']} · {c['nome_completo']}": c["id_cliente"] for c in bd.clientes_opcoes()}
        self.frm = {f["forma_de_pagamento"]: f["id_forma_pagamento"] for f in bd.formas_pagamento()}
        texto(dir_, "Cliente", MU, 12, True).pack(anchor="w")
        self.o_cli = ctk.CTkOptionMenu(dir_, values=list(self.cli), fg_color=CAMPO, button_color=BORDA, text_color=TX); self.o_cli.pack(fill="x", pady=(2, 8))
        texto(dir_, "Forma de pagamento", MU, 12, True).pack(anchor="w")
        self.o_frm = ctk.CTkOptionMenu(dir_, values=list(self.frm), fg_color=CAMPO, button_color=BORDA, text_color=TX); self.o_frm.pack(fill="x", pady=2)
        # Rodapé: esvaziar (esquerda) e finalizar (direita)
        rod = ctk.CTkFrame(self, fg_color="transparent"); rod.pack(fill="x", pady=(10, 0))
        botao(rod, "Esvaziar carrinho", self.esvaziar).pack(side="left")
        botao(rod, "Finalizar venda", self.finalizar, pri=True, height=46, width=200).pack(side="right")
        self.indicadores(); self.desenhar_carrinho()

    def indicadores(self):
        i = bd.indicadores()
        for lbl, v in zip(self.kpi, (bd.brl(i["hoje"]), bd.brl(i["mes"]), str(i["qtd"]))):
            lbl.configure(text=v)

    def buscar(self):
        self.achados.limpar()
        q = self.busca.get().strip()
        for r in (bd.buscar_para_venda(q) if q else []):
            ent = {}
            self.achados.linha([tx(f"{r['nome_carta']}\n{r['idioma']} · {r['condicao']}", LK, True), r["sigla_edicao"], str(r["estoque"]),
                                tx(bd.brl(r["preco"]), TX, True), entrada_na_tabela(ent, "q", "1", 50, "center"),
                                lambda m, r=r, ent=ent: botao(m, "Adicionar", lambda: self.adicionar(r, ent["q"].get()), height=32)])

    def adicionar(self, r, qtd):
        try:
            qtd = int(qtd)
        except ValueError:
            qtd = 0
        i = r["id_carta_venda"]; atual = self.carrinho.get(i, {}).get("qtd", 0)
        if qtd < 1:
            return self.app.aviso("Escolha uma quantidade maior que zero.", True)
        if atual + qtd > r["estoque"]:
            return self.app.aviso(f"Estoque insuficiente: só há {r['estoque']} unidade(s) dessa carta.", True)
        self.carrinho[i] = {"nome": r["nome_carta"], "preco": r["preco"], "estoque": r["estoque"], "qtd": atual + qtd}
        self.desenhar_carrinho(); self.app.aviso("Item adicionado ao carrinho.")

    def desenhar_carrinho(self):
        self.cart.limpar(); total = 0.0
        for i, it in self.carrinho.items():
            sub = round(it["preco"] * it["qtd"], 2); total += sub
            self.cart.linha([tx(it["nome"], TX, True), str(it["qtd"]), bd.brl(sub),
                             lambda m, i=i: botao(m, "Remover", lambda: self.remover(i), height=30)])
        self.total.configure(text=f"Total  {bd.brl(round(total, 2))}")

    def remover(self, i):
        self.carrinho.pop(i, None); self.desenhar_carrinho()

    def esvaziar(self):
        self.carrinho.clear(); self.desenhar_carrinho(); self.app.aviso("Carrinho esvaziado.")

    def finalizar(self):
        try:
            id_venda, total = bd.finalizar_venda(self.app.usuario, self.cli[self.o_cli.get()], self.frm[self.o_frm.get()],
                                                 [(i, it["qtd"]) for i, it in self.carrinho.items()])
        except ValueError as e:
            return self.app.aviso(str(e), True)
        self.carrinho.clear(); self.desenhar_carrinho(); self.indicadores(); self.buscar()
        self.app.aviso(f"Venda #{id_venda} registrada: {bd.brl(total)}.")
        JanelaPedido(self.app, id_venda)


# =============================================================================
#  6. PEDIDOS — histórico das vendas
# =============================================================================
class PaginaPedidos(ctk.CTkFrame):
    def __init__(self, m, app):
        super().__init__(m, fg_color="transparent")
        self.app, self.q, self.pag = app, "", 1
        titulo(self, "Pedidos").pack(anchor="w")
        b = ctk.CTkFrame(self, fg_color="transparent"); b.pack(fill="x", pady=10)
        self.busca = campo(b, "Buscar por nome do cliente ou número do pedido"); self.busca.pack(side="left", fill="x", expand=True)
        self.busca.bind("<Return>", lambda e: self.buscar())
        botao(b, "Buscar", self.buscar, pri=True, width=100).pack(side="left", padx=(10, 0))
        self.tab = Tabela(self, [("Pedido", 90), ("Data", 140), ("Cliente", 220), ("Vendedor", 110),
                                 ("Pagamento", 110), ("Total", 110), ("", 100)])
        self.tab.pack(fill="both", expand=True)
        rod = ctk.CTkFrame(self, fg_color="transparent"); rod.pack(fill="x", pady=(10, 0))
        self.pg, self.info, self.ba, self.bp = paginador(rod, lambda: self.mover(-1), lambda: self.mover(1))
        self.pg.pack(side="right")
        self.carregar()

    def buscar(self):
        self.q, self.pag = self.busca.get().strip(), 1; self.carregar()

    def mover(self, d):
        self.pag += d; self.carregar()

    def carregar(self):
        rows, total = bd.listar_pedidos(self.q, self.pag)
        self.tab.limpar()
        for r in rows:
            self.tab.linha([tx(f"#{r['id_venda']}", TX, True), bd.dt(r["data_hora"]), r["cliente"], r["vendedor"], r["forma"],
                            tx(bd.brl(r["valor_total"]), TX, True),
                            lambda m, i=r["id_venda"]: botao(m, "Detalhes", lambda: JanelaPedido(self.app, i), height=30)])
        if not rows:
            self.tab.linha([tx("Nenhum pedido encontrado. Registre a primeira venda em Vendas.", MU)])
        ini = (self.pag - 1) * bd.POR_PAGINA + 1 if total else 0
        fim = min(self.pag * bd.POR_PAGINA, total)
        self.info.configure(text=f"{ini}–{fim} de {total}")
        self.ba.configure(state="normal" if self.pag > 1 else "disabled")
        self.bp.configure(state="normal" if fim < total else "disabled")


class JanelaPedido(ctk.CTkToplevel):
    """Janela com os detalhes de um pedido: dados da venda e cartas vendidas."""

    def __init__(self, app, id_venda):
        super().__init__(app, fg_color=PR)
        v, itens = bd.detalhe_pedido(id_venda)
        self.title(f"Pedido #{id_venda}"); self.geometry("700x480"); self.attributes("-topmost", True)
        titulo(self, f"Pedido #{id_venda}").pack(anchor="w", padx=20, pady=(16, 4))
        texto(self, f"{bd.dt(v['data_hora'])}   ·   Cliente: {v['cliente']}   ·   Vendedor: {v['vendedor']}   ·   {v['forma']}", MU).pack(anchor="w", padx=20)
        tab = Tabela(self, [("Carta", 300), ("Qtd", 50), ("Unitário", 110), ("Subtotal", 110)])
        tab.pack(fill="both", expand=True, padx=20, pady=12)
        for i in itens:
            tab.linha([tx(f"{i['nome_carta']}\n{i['sigla_edicao']} · {i['idioma']} · {i['condicao']}", TX, True),
                       str(i["quantidade"]), bd.brl(i["preco_unitario"]), bd.brl(i["subtotal"])])
        ctk.CTkLabel(self, text=f"Total  {bd.brl(v['valor_total'])}", text_color=TX, font=("Segoe UI", 22, "bold")).pack(anchor="e", padx=20)
        botao(self, "Fechar", self.destroy, pri=True, width=120).pack(anchor="e", padx=20, pady=12)


# =============================================================================
#  7. JANELA PRINCIPAL — menu, avisos e troca de telas
# =============================================================================
class Aplicativo(ctk.CTk):
    PAGINAS = {"cartas": ("Cards e Produtos", PaginaCartas), "pedidos": ("Pedidos", PaginaPedidos),
               "vendas": ("Vendas", PaginaVendas), "clientes": ("Clientes", PaginaClientes)}

    def __init__(self):
        super().__init__(fg_color=PR)
        self.title("Ludenz 360"); self.geometry("1280x780"); self.minsize(1100, 700)
        self.usuario, self.pagina, self._aviso_id = None, None, None
        self.mostrar_login()

    def mostrar_login(self):
        for w in self.winfo_children():
            w.destroy()
        TelaLogin(self, self.entrou).pack(fill="both", expand=True)

    def entrou(self, nome):
        """Depois do login: monta o topo amarelo com o menu e abre a tela de cartas."""
        self.usuario = nome
        for w in self.winfo_children():
            w.destroy()
        topo = ctk.CTkFrame(self, fg_color=AM, corner_radius=0, height=60); topo.pack(fill="x")
        ctk.CTkLabel(topo, text="LUDENZ 360", text_color=PR, font=("Bahnschrift", 26, "bold")).pack(side="left", padx=20, pady=10)
        self.menu = {}
        for k, (rot, _) in self.PAGINAS.items():
            b = ctk.CTkButton(topo, text=rot, command=lambda k=k: self.ir(k), fg_color="transparent", text_color=PR,
                              hover_color="#FFD98A", font=("Segoe UI", 14, "bold"), width=130, corner_radius=6)
            b.pack(side="left", padx=2); self.menu[k] = b
        ctk.CTkButton(topo, text="Sair", command=self.mostrar_login, fg_color=PR, text_color=AM, hover_color="#2A261F",
                      width=80).pack(side="right", padx=20)
        ctk.CTkLabel(topo, text=nome, text_color=PR, font=("Segoe UI", 14, "bold")).pack(side="right")
        self.aviso_lbl = ctk.CTkLabel(self, text="", anchor="w", text_color=TX, fg_color="transparent", height=26)
        self.aviso_lbl.pack(fill="x", padx=24, pady=(6, 0))
        self.corpo = ctk.CTkFrame(self, fg_color="transparent"); self.corpo.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        self.ir("cartas")

    def ir(self, nome):
        """Troca a tela mostrada (cada tela é recriada e relê o banco)."""
        if self.pagina:
            self.pagina.destroy()
        for k, b in self.menu.items():
            b.configure(fg_color=PR if k == nome else "transparent", text_color=AM if k == nome else PR)
        self.aviso("")
        self.pagina = self.PAGINAS[nome][1](self.corpo, self)
        self.pagina.pack(fill="both", expand=True)

    def aviso(self, msg, erro=False):
        """Mensagem curta abaixo do menu (some sozinha depois de 6 segundos)."""
        self.aviso_lbl.configure(text=msg, text_color=ER if erro else OK)
        if self._aviso_id:
            self.after_cancel(self._aviso_id)
        self._aviso_id = self.after(6000, lambda: self.aviso_lbl.configure(text="")) if msg else None


if __name__ == "__main__":
    Aplicativo().mainloop()
