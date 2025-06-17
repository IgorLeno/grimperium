
# **PRD (Product Requirements Document): Grimperium v2.0**

Documento: PRD-GRIMPERIUM-2.0
Status: Proposta Refatorada

### **1. Visão Geral e Objetivo**

*   **Nome:** Grimperium
*   **Visão:** Um sistema de linha de comando (CLI) em Python para ambientes WSL (Debian/Ubuntu), que automatiza a geração de dados termodinâmicos para moléculas orgânicas. Ele orquestra softwares de química computacional (CREST, MOPAC) para realizar buscas conformacionais e cálculos de entalpia (método PM7), preparando dados para treinar um modelo de Aprendizado Delta (Δ-ML).
*   **Problema:** A geração de grandes bancos de dados termoquímicos é lenta e cara. O Grimperium visa fornecer um pipeline rápido e acessível usando o método semi-empírico PM7 como nível de teoria baixo (LLOT).
*   **Objetivo (MVP):** Automatizar o pipeline de cálculo (CREST + MOPAC), extrair dados do banco de referência `thermo_cbs.csv` e gerar um banco de dados `thermo_pm7.csv` compatível para treinamento de ML.

### **2. Requisitos Funcionais (FR)**

**FR1: Entradas de Moléculas**
*   FR1.1: O sistema deve aceitar uma única molécula como entrada, seja pelo nome químico ou pela notação SMILES.
*   FR1.2: O sistema deve aceitar um lote de moléculas como entrada, seja por uma lista de nomes/SMILES separada por vírgulas ou por um arquivo de texto (`.txt`).

**FR2: Pipeline de Cálculo Automatizado**
*   Para cada molécula, o sistema deve executar o seguinte fluxo:
    *   FR2.1: Obter a estrutura 3D inicial a partir do identificador fornecido (ex: de um banco de dados público como o PubChem para nomes).
    *   FR2.2: Realizar uma busca conformacional para encontrar o confôrmero de menor energia.
    *   FR2.3: Calcular a entalpia de formação para o confôrmero de menor energia usando o método PM7.
    *   FR2.4: Extrair (fazer parsing) o valor da entalpia de formação do arquivo de saída do cálculo.

**FR3: Geração do Banco de Dados de Saída**
*   FR3.1: Os resultados devem ser salvos em um arquivo CSV (`thermo_pm7.csv`).
*   FR3.2: O esquema do CSV de saída deve ser consistente com o do `thermo_cbs.csv`, conforme especificado no `DATABASE_SCHEMA_v2.md`.
*   FR3.3: O sistema deve adicionar novos resultados ao arquivo CSV sem sobrescrever os dados existentes, evitando a inserção de duplicatas baseadas no SMILES.

**FR4: Integração com o Banco de Dados de Referência**
*   FR4.1: O sistema deve ser capaz de ler o `thermo_cbs.csv`.
*   FR4.2: Deve permitir que o usuário inicie um lote de cálculos usando as moléculas do `thermo_cbs.csv`, com a opção de especificar um ponto de início e um número de moléculas.
*   FR4.3: O sistema deve fornecer um relatório de progresso, comparando as moléculas calculadas no `thermo_pm7.csv` com o total de moléculas no `thermo_cbs.csv`.

**FR5: Módulo de Treinamento (Futuro)**
*   (Placeholder) Um módulo será desenvolvido para unir os dados HLOT (`thermo_cbs.csv`) e LLOT (`thermo_pm7.csv`) e treinar um modelo de Δ-ML.

**FR6: Integração com Supabase (Futuro)**
*   (Placeholder) Um módulo será desenvolvido para sincronizar os dados gerados com um banco de dados Supabase.

### **3. Requisitos Não Funcionais (NFR)**

*   **NFR1: Ambiente:** O sistema deve ser projetado para WSL (Debian/Ubuntu).
*   **NFR2: Usabilidade:** A interface deve ser uma CLI clara e interativa.
*   **NFR3: Configuração:** Parâmetros chave (caminhos, keywords de cálculo) devem ser externalizados em um arquivo `config.yaml`.
*   **NFR4: Logging:** O sistema deve gerar logs detalhados em um arquivo e exibir informações de alto nível no console.
*   **NFR5: Modularidade:** O código deve ser organizado em módulos com responsabilidades claras (serviços, core, interfaces), conforme o `ARCHITECTURE_v2.md`.
*   **NFR6: Tratamento de Erros:** O sistema deve ser robusto a falhas em cálculos individuais, logando o erro e continuando para a próxima molécula em modo de lote.
