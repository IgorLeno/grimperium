
# **Arquitetura do Software Grimperium v2**

Este documento descreve a arquitetura de software modular e baseada em serviços do Grimperium.

## **1. Filosofia de Design**

*   **Modularidade e Responsabilidade Única:** Código dividido em módulos com propósitos bem definidos.
*   **Arquitetura de Serviços:** A lógica de negócios é encapsulada em serviços (ex: `CalculationService`, `DatabaseService`) que são independentes da interface do usuário.
*   **Configuração Externalizada:** Parâmetros dinâmicos residem em um arquivo `config.yaml`, desacoplando a configuração do código.
*   **Interface Clara:** A interação com o usuário é gerenciada por um módulo de CLI, que orquestra as chamadas aos serviços.

## **2. Estrutura de Diretórios Proposta**

```
grimperium/
├── config/                  # (Opcional) Pode conter schemas de configuração
├── core/                    # Classes de domínio (ex: Molecule)
├── interfaces/              # Interface com o usuário (CLI com Typer/Rich)
├── services/                # Lógica de negócios
│   └── analysis/            # Lógicas de análise de dados
├── utils/                   # Utilitários (logging, config_manager)
├── repository/              # Arquivos de cálculo temporários
│   ├── sdf/
│   ├── xyz/
│   ├── crest/
│   └── mopac/
├── data/                    # Arquivos CSV de entrada e saída
├── logs/                    # Arquivos de log
├── tests/                   # Testes
├── main.py                  # Ponto de entrada da CLI
├── config.yaml              # Arquivo de configuração
└── requirements.txt         # Dependências Python
```

## **3. Descrição dos Módulos Principais**

*   **main.py**: Ponto de entrada da aplicação. Responsável por inicializar a CLI (Typer), carregar a configuração e delegar comandos para os módulos de interface.
*   **core/molecule.py**: Define a estrutura de dados central, a classe `Molecule`, que representa uma molécula e seus dados associados ao longo do pipeline.
*   **services/pubchem_service.py**: Responsável por toda a comunicação com a API do PubChem para buscar e baixar estruturas moleculares.
*   **services/conversion_service.py**: Responsável por encapsular as chamadas ao OpenBabel, realizando conversões de formato de arquivo (ex: SDF -> XYZ).
*   **services/calculation_service.py**: Responsável por executar os programas de química computacional (CREST, MOPAC) via chamadas de subprocesso e fazer o parsing dos arquivos de saída para extrair resultados.
*   **services/database_service.py**: Responsável por todas as operações de leitura e escrita nos arquivos CSV, utilizando Pandas. Garante a consistência e a prevenção de duplicatas.
*   **services/analysis_service.py**: Responsável por ler os bancos de dados e gerar relatórios de progresso e outras análises.
*   **services/pipeline_orchestrator.py**: (Pode ser um módulo ou uma classe) Orquestra as chamadas aos diferentes serviços para executar o pipeline completo para uma ou mais moléculas.
*   **interfaces/cli.py**: Define os comandos, argumentos e opções da CLI usando Typer. Traduz as interações do usuário em chamadas para o `pipeline_orchestrator`.
*   **utils/config_manager.py**: Utilitário para carregar e validar o `config.yaml`.
*   **utils/logging_config.py**: Utilitário para configurar o sistema de logging.
