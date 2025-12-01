# controle_estoque_app.py
# Aplicativo de controle de estoque usando linguagem python, Tkinter e SQLite
# Autor: Cristian Finger
# data_inicio: 17.11.2025

from tkinter import *
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import os
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "dados", "estoque.db")

def ensure_db():
    os.makedirs(os.path.join(BASE_DIR, "dados"), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE NOT NULL
                );""")
    c.execute("""CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    categoria_id INTEGER,
                    preco REAL DEFAULT 0,
                    quantidade INTEGER DEFAULT 0,
                    min_estoque INTEGER DEFAULT 0,
                    FOREIGN KEY(categoria_id) REFERENCES categorias(id)
                );""")
    c.execute("""CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    quantidade INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    observacao TEXT,
                    FOREIGN KEY(produto_id) REFERENCES produtos(id)
                );""")
    conn.commit()
    conn.close()


def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        rows = c.fetchall()
        conn.close()
        return rows
    conn.commit()
    conn.close()

def add_categoria(nome):
    try:
        run_query("INSERT INTO categorias (nome) VALUES (?)", (nome,))
        return True
    except sqlite3.IntegrityError:
        return False

def list_categorias():
    return run_query("SELECT id, nome FROM categorias ORDER BY nome", fetch=True)

def add_produto(nome, categoria_id, preco, quantidade, min_estoque):
    run_query("""INSERT INTO produtos (nome, categoria_id, preco, quantidade, min_estoque)
                 VALUES (?, ?, ?, ?, ?)""", (nome, categoria_id, preco, quantidade, min_estoque))

def update_produto(pid, nome, categoria_id, preco, quantidade, min_estoque):
    run_query("""UPDATE produtos SET nome=?, categoria_id=?, preco=?, quantidade=?, min_estoque=?
                 WHERE id=?""", (nome, categoria_id, preco, quantidade, min_estoque, pid))

def delete_produto(pid):
    run_query("DELETE FROM produtos WHERE id=?", (pid,))

def list_produtos(search=None):
    if search:
        term = f"%{search}%"
        return run_query("""SELECT p.id, p.nome, c.nome, p.preco, p.quantidade, p.min_estoque
                            FROM produtos p LEFT JOIN categorias c ON p.categoria_id=c.id
                            WHERE p.nome LIKE ? OR c.nome LIKE ?
                            ORDER BY p.nome""", (term, term), fetch=True)
    return run_query("""SELECT p.id, p.nome, c.nome, p.preco, p.quantidade, p.min_estoque
                        FROM produtos p LEFT JOIN categorias c ON p.categoria_id=c.id
                        ORDER BY p.nome""", fetch=True)

def get_produto(pid):
    res = run_query("SELECT id, nome, categoria_id, preco, quantidade, min_estoque FROM produtos WHERE id=?", (pid,), fetch=True)
    return res[0] if res else None

def add_movimentacao(produto_id, tipo, quantidade, observacao=""):
    data = datetime.now().isoformat(sep=' ', timespec='seconds')
    run_query("""INSERT INTO movimentacoes (produto_id, tipo, quantidade, data, observacao)
                 VALUES (?, ?, ?, ?, ?)""", (produto_id, tipo, quantidade, data, observacao))
    # Atualizar quantidade no produto
    prod = get_produto(produto_id)
    if not prod:
        return
    current_qty = prod[4]
    new_qty = current_qty + quantidade if tipo == 'entrada' else current_qty - quantidade
    run_query("UPDATE produtos SET quantidade=? WHERE id=?", (new_qty, produto_id))

def list_movimentacoes(limit=100):
    return run_query("""SELECT m.id, p.nome, m.tipo, m.quantidade, m.data, m.observacao
                        FROM movimentacoes m JOIN produtos p ON m.produto_id = p.id
                        ORDER BY m.data DESC LIMIT ?""", (limit,), fetch=True)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Controle de Estoque - Python")
        root.geometry("900x600")
        self.create_widgets()
        self.refresh_produtos()
        self.check_alerts()

    def excluir_produto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um produto para excluir.")
            return

        item = sel[0]
        pid = int(self.tree.item(item, "values")[0])

        resp = messagebox.askyesno("Excluir Produto", f"Tem certeza que deseja excluir o produto ID {pid}?")
        if not resp:
            return

        
        delete_produto(pid)

        messagebox.showinfo("Sucesso", "Produto removido com sucesso.")
        self.refresh_produtos()

    def create_widgets(self):
        
        header = Frame(self.root, bg="#10f21c", height=50)
        header.pack(fill=X)

        Label(
            header,
            text="AVITEC - Controle de Estoque",
            font=("Arial", 20),
            bg="#edda0e"
        ).pack(pady=10)

        frm = Frame(self.root)
        frm.pack(fill=X, padx=8, pady=6)

        Button(frm, text="Nova Categoria", command=self.nova_categoria).pack(side=LEFT, padx=4)
        Button(frm, text="Novo Produto", command=self.novo_produto).pack(side=LEFT, padx=4)
        Button(frm, text="Excluir Produto", command=self.excluir_produto).pack(side=LEFT, padx=4)
        Button(frm, text="Registrar Entrada", command=lambda: self.registrar_mov('entrada')).pack(side=LEFT, padx=4)
        Button(frm, text="Registrar Saída", command=lambda: self.registrar_mov('saida')).pack(side=LEFT, padx=4)
        Button(frm, text="Exportar CSV", command=self.export_csv).pack(side=LEFT, padx=4)

        # Busca
        self.search_var = StringVar()
        Entry(frm, textvariable=self.search_var).pack(side=LEFT, padx=6)
        Button(frm, text="Buscar", command=self.on_search).pack(side=LEFT, padx=4)
        Button(frm, text="Limpar", command=self.on_clear_search).pack(side=LEFT, padx=4)

        cols = ("ID","Nome","Categoria","Preço","Qtd","MinQtd")
        self.tree = ttk.Treeview(self.root, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor=W, width=100)
        self.tree.pack(fill=BOTH, expand=True, padx=8, pady=6)
        self.tree.bind("<Double-1>", self.on_edit_produto)

        # Movimentações
        lbl = Label(self.root, text="Últimas movimentações:")
        lbl.pack(anchor=W, padx=8)
        self.mov_text = Text(self.root, height=8)
        self.mov_text.pack(fill=X, padx=8, pady=4)

    def nova_categoria(self):
        nome = simpledialog.askstring("Nova Categoria", "Nome da categoria:")
        if nome:
            ok = add_categoria(nome.strip())
            if ok:
                messagebox.showinfo("Sucesso", "Categoria adicionada.")
            else:
                messagebox.showwarning("Erro", "Categoria já existe.")
        self.refresh_produtos()

    def novo_produto(self):
        dlg = ProdutoDialog(self.root)
        self.root.wait_window(dlg.top)
        if dlg.result:
            nome, cat_id, preco, qtd, minq = dlg.result
            add_produto(nome, cat_id, preco, qtd, minq)
            messagebox.showinfo("Sucesso", "Produto cadastrado.")
        self.refresh_produtos()

    def on_edit_produto(self, event):
        sel = self.tree.selection()
        if not sel: return
        pid = int(self.tree.item(sel[0])['values'][0])
        prod = get_produto(pid)
        dlg = ProdutoDialog(self.root, produto=prod)
        self.root.wait_window(dlg.top)
        if dlg.result:
            nome, cat_id, preco, qtd, minq = dlg.result
            update_produto(pid, nome, cat_id, preco, qtd, minq)
            messagebox.showinfo("Sucesso", "Produto atualizado.")
        self.refresh_produtos()

    def registrar_mov(self, tipo):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Seleção", "Selecione um produto na lista.")
            return
        pid = int(self.tree.item(sel[0])['values'][0])
        qty = simpledialog.askinteger("Quantidade", f"Quantidade para {tipo}:")
        if qty is None: return
        obs = simpledialog.askstring("Observação (opcional)", "Observação:")
        
        add_movimentacao(pid, tipo, qty, obs or "")
        messagebox.showinfo("Registrado", f"{tipo.capitalize()} registrado.")
        self.refresh_produtos()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if not path: return
        rows = list_produtos()
        with open(path, "w", newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["ID","Nome","Categoria","Preco","Quantidade","MinEstoque"])
            for r in rows:
                w.writerow(r)
        messagebox.showinfo("Exportado", f"Arquivo salvo em: {path}")

    def on_search(self):
        term = self.search_var.get().strip()
        self.refresh_produtos(search=term)

    def on_clear_search(self):
        self.search_var.set("")
        self.refresh_produtos()

    def refresh_produtos(self, search=None):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = list_produtos(search=search)
        for r in rows:
            self.tree.insert("", "end", values=r)
        # atualizar movimentações
        self.mov_text.delete("1.0", END)
        movs = list_movimentacoes(20)
        for m in movs:
            self.mov_text.insert(END, f"{m[4]} | {m[1]} | {m[2]} | {m[3]} | {m[5]}\n")

    def check_alerts(self):
        rows = list_produtos()
        alerts = []
        for r in rows:
            pid, nome, cat, preco, qtd, minq = r
            if minq is not None and qtd is not None and qtd <= minq:
                alerts.append(f"{nome} (Qtd: {qtd} / Min: {minq})")
        if alerts:
            messagebox.showwarning("Alerta de Estoque Mínimo", "Produtos com estoque baixo:\n" + "\n".join(alerts))
        
        self.root.after(10800000, self.check_alerts)

class ProdutoDialog:
    def __init__(self, parent, produto=None):
        top = self.top = Toplevel(parent)
        top.title("Produto")
        Label(top, text="Nome:").grid(row=0, column=0, sticky=W)
        self.nome = Entry(top, width=40)
        self.nome.grid(row=0, column=1, padx=4, pady=2)
        Label(top, text="Categoria:").grid(row=1, column=0, sticky=W)
        self.cat_cb = ttk.Combobox(top, values=[c[1] for c in list_categorias()])
        self.cat_cb.grid(row=1, column=1, padx=4, pady=2)
        Label(top, text="Preço:").grid(row=2, column=0, sticky=W)
        self.preco = Entry(top); self.preco.grid(row=2, column=1, padx=4, pady=2)
        Label(top, text="Quantidade:").grid(row=3, column=0, sticky=W)
        self.qtd = Entry(top); self.qtd.grid(row=3, column=1, padx=4, pady=2)
        Label(top, text="Min. Estoque:").grid(row=4, column=0, sticky=W)
        self.minq = Entry(top); self.minq.grid(row=4, column=1, padx=4, pady=2)

        btn = Button(top, text="Salvar", command=self.on_save)
        btn.grid(row=5, column=0, columnspan=2, pady=6)

        self.result = None
        if produto:
            pid, nome, cat_id, preco, qtd, minq = produto
            self.nome.insert(0, nome)
            
            cats = list_categorias()
            cat_names = [c[1] for c in cats]
            if cat_id:
                for i,c in enumerate(cats):
                    if c[0] == cat_id:
                        self.cat_cb.current(i)
                        break
            self.preco.insert(0, str(preco))
            self.qtd.insert(0, str(qtd))
            self.minq.insert(0, str(minq))

    def on_save(self):
        nome = self.nome.get().strip()
        cat_name = self.cat_cb.get().strip()
        cat_id = None
        for c in list_categorias():
            if c[1] == cat_name:
                cat_id = c[0]; break
        try:
            preco = float(self.preco.get() or 0)
        except:
            preco = 0.0
        try:
            qtd = int(self.qtd.get() or 0)
        except:
            qtd = 0
        try:
            minq = int(self.minq.get() or 0)
        except:
            minq = 0
        if not nome:
            messagebox.showwarning("Validação", "Informe o nome do produto.")
            return
        self.result = (nome, cat_id, preco, qtd, minq)
        self.top.destroy()

def main():
    ensure_db()
    root = Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
