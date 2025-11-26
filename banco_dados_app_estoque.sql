
-- SCRIPT DDL - Definição de Dados
-- Banco de Dados: estoque.db


-- Criar tabela de categorias
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
);

-- Criar tabela de produtos
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria_id INTEGER,
    preco REAL DEFAULT 0,
    quantidade INTEGER DEFAULT 0,
    min_estoque INTEGER DEFAULT 0,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

-- Criar tabela de movimentações
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    tipo TEXT NOT NULL, -- entrada | saida
    quantidade INTEGER NOT NULL,
    data TEXT NOT NULL,
    observacao TEXT,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);


INSERT INTO categorias (nome) VALUES ('Nome da Categoria');

INSERT INTO produtos (nome, categoria_id, preco, quantidade, min_estoque)
VALUES ('Nome do Produto', 1, 10.50, 100, 5);

UPDATE produtos
SET nome = 'Novo Nome',
    categoria_id = 1,
    preco = 20.99,
    quantidade = 50,
    min_estoque = 10
WHERE id = 1;

DELETE FROM produtos WHERE id = 1;

INSERT INTO movimentacoes (produto_id, tipo, quantidade, data, observacao)
VALUES (1, 'entrada', 50, '2025-11-25 12:00:00', 'Entrada de estoque');

INSERT INTO movimentacoes (produto_id, tipo, quantidade, data, observacao)
VALUES (1, 'saida', 10, '2025-11-25 12:30:00', 'Saída para venda');


SELECT id, nome FROM categorias ORDER BY nome;


SELECT p.id, p.nome, c.nome, p.preco, p.quantidade, p.min_estoque
FROM produtos p
LEFT JOIN categorias c ON p.categoria_id = c.id
ORDER BY p.nome;

SELECT p.id, p.nome, c.nome, p.preco, p.quantidade, p.min_estoque
FROM produtos p
LEFT JOIN categorias c ON p.categoria_id = c.id
WHERE p.nome LIKE '%termo%' OR c.nome LIKE '%termo%'
ORDER BY p.nome;


SELECT m.id, p.nome, m.tipo, m.quantidade, m.data, m.observacao
FROM movimentacoes m
JOIN produtos p ON m.produto_id = p.id
ORDER BY m.data DESC
LIMIT 100;