CREATE DATABASE IF NOT EXISTS personal_finance;
USE personal_finance;

CREATE TABLE IF NOT EXISTS transactions (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  nome_item      VARCHAR(255) NOT NULL,
  preco_unitario DECIMAL(10,2) NOT NULL,
  quantidade     DECIMAL(10,3) NOT NULL,
  data_compra    DATE NOT NULL
);

INSERT INTO transactions (nome_item, preco_unitario, quantidade, data_compra) VALUES
('Arroz 5kg', 28.90, 2, '2026-01-03'),
('Feijão carioca 1kg', 12.90, 3, '2026-01-03'),
('Frango inteiro 1kg', 15.90, 2, '2026-01-10'),
('Leite integral 1L', 5.90, 6, '2026-01-10'),
('Café em pó 500g', 27.90, 1, '2026-01-31'),
('Arroz 5kg', 35.50, 2, '2026-02-07'),
('Azeite extra virgem 500ml', 42.90, 1, '2026-02-14'),
('Tomate 1kg', 8.90, 2, '2026-02-28'),
('Arroz 5kg', 36.90, 2, '2026-03-07'),
('Frango peito 1kg', 19.90, 2, '2026-03-14'),
('Queijo mussarela 200g', 13.90, 2, '2026-03-21'),
('Manteiga 200g', 15.90, 2, '2026-03-28'),
('Arroz 5kg', 37.90, 2, '2026-04-04'),
('Frango coxa 1kg', 17.90, 2, '2026-04-11'),
('Leite integral 1L', 6.20, 6, '2026-04-18'),
('Ovos brancos dúzia', 16.90, 2, '2026-04-18');
