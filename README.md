# Melhores Ações da B3

## Stack

- **Python** – Linguagem principal do projeto.  
- **POO** – Utilizada para gerenciamento do banco de dados.  
- **Pytest** – Testes automatizados para validação do código.  
- **Streamlit** – Interface gráfica para interação com os dados.  
- **SQLite** – Banco de dados utilizado, armazenado em um único arquivo.  
- **GitHub** – Repositório do projeto.  

🔗 [Repositório no GitHub](https://github.com/MartonPadilha/best_stocks/tree/main)

---

## Conceitual

### Problema

- Dificuldade em identificar as melhores empresas para investir na bolsa.  
- Falta de alternativas além das mesmas grandes empresas de sempre.

### Objetivo

- Descobrir as melhores oportunidades com base em indicadores fundamentalistas.  
- Encontrar boas empresas que passam despercebidas pelo mercado.

### Como

- Coletar e analisar indicadores financeiros de cada empresa.  
- Aplicar análise multifatorial para ponderar os indicadores e gerar um ranking.

---

## Análise Multifatorial

### Ajuste dos Indicadores

- Cada indicador recebe um peso baseado em sua relevância (ex: priorização do ROE).  
- Fórmula: `Indicador x Peso = Indicador Ajustado`.

### Cálculo do Score

- A soma dos indicadores ajustados gera um score para cada empresa.

---

## Técnicas

### Fontes de Dados

- **API (Yahoo Finance):**
  - Lista de todos os tickers da bolsa (ex: PETR4, VALE3, KEPL3).  
  - Fácil de implementar.  
  - Poucos indicadores.  
  - Bom para teste inicial.

- **Webscraping (Status Invest):**
  - Mais complexo de codar.  
  - Muitos indicadores disponíveis.  
  - Maior risco de quebra com alterações no site.

---

### Outliers

- **IQR (Intervalo Interquartil)**  
- **Z-Score (Desvio padrão)**

### Normalização

- **Min-Max Normalization**  
  Todos os valores são convertidos para uma escala entre 0 e 1.

### Score Final

- Score Geral + Score por Setor = **SCORE FINAL**

---

## Notícias

### Fontes de Dados

- API do [newsapi.org](https://newsapi.org): retorna data, título e URL da notícia.  
- Webscraping da notícia completa a partir da URL.  
- Integração com GenAI da Google para interpretar o conteúdo e atribuir uma nota qualitativa ao impacto da notícia.

---

## Futuro

- Implementar Machine Learning para melhorar a atribuição dos pesos dos indicadores.  
- Incluir dados macroeconômicos e correlação com eventos de mercado.  
- Colocar o código em um orquestrador para alimentação contínua dos dados.  
- Melhorar os testes unitários.



- Verificar historico do valor da ação e agregar no score
- Verificar ações que entraram na bolsa (IPO)
- CDI - Títulos Públicos

# Como executar? 
cd C:\Users\marton\Desktop\projects\best_stocks
poetry env use C:\Users\marton\AppData\Local\Programs\Python\Python312\python.exe
poetry install
poetry run streamlit run src/app.py