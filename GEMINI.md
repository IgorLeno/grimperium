# Memória do Projeto: Grimperium

> **Notice: Multi-Agent Context Separation** bnm,.
> This file (`GEMINI.md`) contains the instructions for the **Gemini** assistant, which acts as a **Code Analyzer and Prompt Generator**.
> - Do not use or reference this file in sessions with coding agents like AMP (ampcode) or Claude Code.
> - For other agents' context, always use the appropriate context file (e.g., `AGENT.md`, `CLAUDE.md`).
> Keeping context files strictly separated ensures that each agent operates with the correct instructions and memory.

Este arquivo serve como um resumo de alto nível e um guia de contexto para o assistente Gemini. Ele descreve a arquitetura, os principais componentes e os padrões de desenvolvimento do projeto Grimperium.

## 1. Visão Geral do Projeto

O Grimperium parece ser um pipeline de software para química computacional. Ele automatiza o processo de obtenção de informações de moléculas (provavelmente do PubChem), realizando cálculos (possivelmente usando MOPAC, a julgar pelo nome do arquivo `thermo_pm7.csv`), processando os resultados e armazenando-os de forma organizada.

- **Objetivo Principal**: Orquestrar um pipeline de cálculos químicos para um lote de moléculas.
- **Interface do Usuário**: Possui uma interface de linha de comando para processamento em lote interativo (`interactive_batch.py`).
- **Armazenamento de Dados**: Os resultados dos cálculos são armazenados em um diretório `repository/`, organizado por molécula. Dados tabulares (como `thermo_pm7.csv`) são usados como entrada ou referência.

## 2. Módulos e Arquivos Chave

-   **`main.py`**: O ponto de entrada da aplicação.
-   **`config.yaml`**: Arquivo de configuração principal. É gerenciado por `grimperium/utils/config_manager.py`.
-   **`grimperium/`**: O pacote principal do código-fonte.
    -   **`services/`**: Contém a lógica de negócios principal, separada por responsabilidade.
        -   `pipeline_orchestrator.py`: O cérebro do pipeline. Coordena os outros serviços para processar uma molécula. **Este é um arquivo crítico.**
        -   `pubchem_service.py`: Responsável por interagir com a API do PubChem para buscar dados de moléculas.
        -   `calculation_service.py`: Gerencia a execução de cálculos computacionais externos.
        -   `database_service.py`: Lida com a leitura e escrita no arquivo `thermo_pm7.csv`.
        -   `analysis_service.py`: Provavelmente analisa os resultados dos cálculos.
    -   **`core/`**: Contém as estruturas de dados centrais.
        -   `molecule.py`: Define o objeto de domínio `Molecule`, que representa uma molécula ao longo do pipeline.
    -   **`ui/`**: Componentes de interface do usuário.
        -   `interactive_batch.py`: Fornece a interface para os usuários executarem o pipeline em listas de moléculas.
    -   **`utils/`**: Utilitários de baixo nível.
        -   `config_manager.py`: Carrega e fornece acesso às configurações do `config.yaml`.
        -   `subprocess_utils.py`: Utilitário para executar comandos de shell externos, essencial para o `calculation_service`.
-   **`repository/`**: Diretório de saída onde os resultados dos cálculos são armazenados.
-   **`data/lists/`**: Contém as listas de moléculas a serem processadas.

## 3. Fluxo de Trabalho de Desenvolvimento

-   **Configuração**: As configurações são centralizadas em `config.yaml`. Novas configurações devem ser adicionadas lá e acessadas através do `ConfigManager`.
-   **Arquitetura**: O projeto segue uma arquitetura orientada a serviços. A lógica deve ser adicionada ou modificada nos serviços apropriados em `grimperium/services/`.
-   **Testes**: Existem testes (ex: `test_pipeline_orchestrator.py`). Novos recursos ou correções de bugs devem, idealmente, ser acompanhados por testes.
-   **Execução**: A aplicação é executada através de `main.py`, que provavelmente invoca a UI de lote interativo.

## 4. Notas Importantes

-   O `pipeline_orchestrator.py` é o ponto de partida para entender o fluxo de processamento de ponta a ponta.
-   O projeto depende da execução de processos externos (via `subprocess_utils.py`), o que significa que o ambiente de execução deve ter as ferramentas de cálculo necessárias instaladas e no PATH do sistema.
-   A manipulação de erros parece ser centralizada através de `grimperium/utils/error_handler.py` e exceções customizadas em `grimperium/exceptions.py`.

## Agent Context Separation

| File        | Used By           | Purpose                                       | Must Not Be Used By        |
| :---------- | :---------------- | :-------------------------------------------- | :------------------------- |
| `GEMINI.md` | **Gemini** | Code analysis and prompt generation           | Claude Code, AMP (ampcode) |
| `CLAUDE.md` | Claude Code       | Coding memory & instructions for Claude       | Gemini, AMP (ampcode)      |
| `AGENT.md`  | AMP (ampcode)     | Coding memory & instructions for AMP          | Gemini, Claude Code        |
