# ⚽ Search-SRI-Football: Sistema de Recuperação de Informação

Este projeto foi desenvolvido para a disciplina de **Sistemas de Recuperação de Informação (SRI)**. Ele consiste em um motor de busca especializado em dados de futebol, capaz de processar consultas textuais e retornar os resultados mais relevantes dentro de um conjunto de dados.

## 📌 Sobre o Projeto
O objetivo principal é aplicar conceitos de **Processamento de Linguagem Natural (PLN)** e algoritmos de ranqueamento para encontrar informações específicas em um dataset de futebol. O sistema não faz apenas uma busca por "palavra exata", mas analisa a relevância dos termos nos documentos.

## 🚀 Funcionalidades
- **Processamento de Texto:** Limpeza de dados, remoção de caracteres especiais e normalização.
- **Indexação:** Criação de um índice para busca eficiente.
- **Ranqueamento de Resultados:** Algoritmos para determinar quais linhas do dataset melhor correspondem à consulta do usuário.
- **Interface de Busca:** Sistema interativo via terminal ou script para entrada de queries.

## 🛠️ Tecnologias Utilizadas
- **Python 3.x:** Linguagem base do projeto.
- **Pandas:** Para manipulação e filtragem da base de dados (CSV).
- **NLTK / Re:** Para tratamento de strings e expressões regulares.
- **Matemática de SRI:** Implementação de lógica de pesos e frequências de termos.

## 📂 Estrutura do Repositório
- `main.py` / `Search.py`: Script principal que executa a lógica de busca.
- `Bases/`: Pasta contendo os arquivos CSV com os dados dos jogadores/partidas.

## ⚙️ Como Executar
1. Clone o repositório:
   ```bash
   git clone [https://github.com/P3nido/Search-SRI-Football.git](https://github.com/P3nido/Search-SRI-Football.git)
