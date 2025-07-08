
# **Arquitetura do Software Grimperium v2**

Este documento descreve a arquitetura de software modular e baseada em serviços do Grimperium.

## **1. Filosofia de Design**

*   **Modularidade e Responsabilidade Única:** Código dividido em módulos com propósitos bem definidos.
*   **Arquitetura de Serviços:** A lógica de negócios é encapsulada em serviços (ex: `CalculationService`, `DatabaseService`) que são independentes da interface do usuário.
*   **Configuração Externalizada:** Parâmetros dinâmicos residem em um arquivo `config.yaml`, desacoplando a configuração do código.
*   **Interface Clara:** A interação com o usuário é gerenciada por um módulo de CLI, que orquestra as chamadas aos serviços.
*   **Tratamento de Erros Robusto:** Cada serviço implementa tratamento de erros específico e logging detalhado.
*   **Thread Safety:** Operações críticas como escrita em banco de dados são thread-safe usando FileLocker.

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

### **3.1 Ponto de Entrada**
*   **main.py**: Ponto de entrada da aplicação. Responsável por inicializar a CLI (Typer), carregar a configuração e delegar comandos para os módulos de interface. Inclui modo interativo com Questionary e comandos diretos.

### **3.2 Modelos de Domínio**
*   **core/molecule.py**: Define a estrutura de dados central, a classe `Molecule`, que representa uma molécula e seus dados associados ao longo do pipeline. Usa Pydantic para validação de dados.

### **3.3 Serviços de Negócio**
*   **services/pubchem_service.py**: Responsável por toda a comunicação com a API do PubChem para buscar e baixar estruturas moleculares. Inclui cache e tratamento de erros.
*   **services/conversion_service.py**: Responsável por encapsular as chamadas ao OpenBabel, realizando conversões de formato de arquivo (ex: SDF → XYZ).
*   **services/calculation_service.py**: Responsável por executar os programas de química computacional (CREST, MOPAC) via chamadas de subprocesso e fazer o parsing dos arquivos de saída para extrair resultados.
*   **services/database_service.py**: Responsável por todas as operações de leitura e escrita nos arquivos CSV, utilizando Pandas. Garante a consistência e a prevenção de duplicatas com FileLock.
*   **services/analysis_service.py**: Responsável por ler os bancos de dados e gerar relatórios de progresso e outras análises.
*   **services/pipeline_orchestrator.py**: Orquestra as chamadas aos diferentes serviços para executar o pipeline completo para uma ou mais moléculas.

### **3.4 Utilitários**
*   **utils/config_manager.py**: Utilitário para carregar e validar o `config.yaml`. Inclui validação de executáveis.
*   **utils/base_service.py**: Classe base para serviços com funcionalidade comum.
*   **utils/error_handler.py**: Tratamento centralizado de erros.
*   **utils/file_utils.py**: Utilitários para manipulação de arquivos.
*   **utils/subprocess_utils.py**: Utilitários para execução de subprocessos.

### **3.5 Testes**
*   **tests/test_pipeline_orchestrator.py**: Testes automatizados com mocks inteligentes para subprocess.
