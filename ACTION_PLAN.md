
# **Plano de Ação (Action Plan) para Desenvolvimento do Grimperium v2**

Este documento é o guia mestre para o desenvolvimento do Grimperium. Cada item é uma tarefa de desenvolvimento que pode ser fornecida a uma IA (como Gemini ou Claude) para gerar o código correspondente. As tarefas são organizadas em fases para garantir um desenvolvimento lógico e incremental.

---

### **Fase 0: Estrutura e Configuração Inicial**

O objetivo desta fase é criar o esqueleto do projeto, a configuração e o ponto de entrada principal.

1.  **Tarefa 0.1: Criar a Estrutura de Diretórios**
    *   **Ação:** Crie a estrutura de diretórios conforme definido no `ARCHITECTURE_v2.md`.
    *   **Diretórios:** `grimperium/config`, `grimperium/core`, `grimperium/interfaces`, `grimperium/services`, `grimperium/services/analysis`, `grimperium/utils`, `grimperium/repository/sdf`, `grimperium/repository/xyz`, `grimperium/repository/crest`, `grimperium/repository/mopac`, `grimperium/data`, `grimperium/logs`, `grimperium/tests`.
    *   **Arquivos Iniciais:** Crie arquivos `__init__.py` vazios em cada subdiretório de `grimperium` para que sejam reconhecidos como módulos Python.

2.  **Tarefa 0.2: Criar o Arquivo de Configuração (`config.yaml`)**
    *   **Ação:** Crie o arquivo `config.yaml` na raiz do projeto.
    *   **Conteúdo:**
        ```yaml
        # Caminhos para executáveis (usar nomes se estiverem no PATH do WSL)
        executables:
          crest: 'crest'
          mopac: 'mopac'
          obabel: 'obabel'

        # Parâmetros de cálculo
        mopac_keywords: 'PM7 PRECISE XYZ'
        crest_keywords: '--gfn2' # Exemplo, pode ser ajustado

        # Configurações de logging
        logging:
          log_file: 'logs/grim_details.log'
          console_level: 'INFO'
          file_level: 'DEBUG'

        # Configurações de banco de dados
        database:
          cbs_db_path: 'data/thermo_cbs.csv'
          pm7_db_path: 'data/thermo_pm7.csv'
        ```

3.  **Tarefa 0.3: Módulo de Gerenciamento de Configuração (`utils/config_manager.py`)**
    *   **Ação:** Crie um módulo para carregar o `config.yaml` de forma segura.
    *   **Requisitos:**
        *   Use a biblioteca `PyYAML`.
        *   Crie uma função `load_config()` que lê `config.yaml` e retorna um dicionário.
        *   A função deve tratar o erro `FileNotFoundError` e levantar uma exceção clara se o arquivo não existir.

4.  **Tarefa 0.4: Módulo de Logging (`utils/logging_config.py`)**
    *   **Ação:** Crie um módulo para configurar o logging.
    *   **Requisitos:**
        *   Use o módulo `logging` do Python.
        *   Crie uma função `setup_logging()` que leia as configurações do `config_manager`.
        *   Configure dois handlers:
            1.  Um `StreamHandler` para o console com nível `INFO`.
            2.  Um `FileHandler` para o arquivo de log com nível `DEBUG`.
        *   O formato do log deve incluir timestamp, nível e mensagem.

5.  **Tarefa 0.5: Ponto de Entrada (`main.py`)**
    *   **Ação:** Crie o arquivo `main.py` na raiz do projeto.
    *   **Requisitos:**
        *   Deve importar e chamar `setup_logging()` e `load_config()` no início.
        *   Deve usar a biblioteca `Typer` para criar uma CLI básica.
        *   Crie uma função `main()` decorada com `@app.command()` que, por enquanto, apenas imprime uma mensagem de boas-vindas e exibe a configuração carregada.

---

### **Fase 1: Lógica Central e Serviços de Base**

Foco em criar os serviços que lidam com a obtenção e conversão de dados moleculares.

1.  **Tarefa 1.1: Classe de Domínio (`core/molecule.py`)**
    *   **Ação:** Defina uma classe `Molecule` usando `dataclasses` ou `pydantic`.
    *   **Atributos:** `identifier` (str, pode ser nome ou SMILES), `smiles` (str, opcional), `sdf_path` (str, opcional), `xyz_path` (str, opcional), `crest_best_xyz_path` (str, opcional), `pm7_energy` (float, opcional), etc. Esta classe servirá para rastrear o estado de uma molécula através do pipeline.

2.  **Tarefa 1.2: Serviço do PubChem (`services/pubchem_service.py`)**
    *   **Ação:** Crie um serviço para interagir com o PubChem.
    *   **Requisitos:**
        *   Use a biblioteca `pubchempy`.
        *   Crie uma função `download_sdf_by_name(name: str, output_dir: str) -> str`.
        *   A função deve baixar o SDF 3D para o `output_dir`.
        *   Deve retornar o caminho do arquivo salvo.
        *   Implemente tratamento de erros para nomes não encontrados.

3.  **Tarefa 1.3: Serviço de Conversão (`services/conversion_service.py`)**
    *   **Ação:** Crie um serviço para encapsular as chamadas ao OpenBabel.
    *   **Requisitos:**
        *   Use o módulo `subprocess` para chamar o executável `obabel`.
        *   Crie uma função `convert_file(input_path: str, output_format: str) -> str`.
        *   Exemplo: `convert_file('mol.sdf', 'xyz')` deve executar `obabel mol.sdf -O mol.xyz`.
        *   A função deve retornar o caminho do arquivo de saída.
        *   Deve capturar a saída do `subprocess` para logar erros.

---

### **Fase 2: Pipeline de Cálculo**

Implementar o coração do projeto: a orquestração dos softwares de química.

1.  **Tarefa 2.1: Serviço de Cálculo (`services/calculation_service.py`)**
    *   **Ação:** Crie o serviço que executa CREST e MOPAC.
    *   **Requisitos:**
        *   **Função CREST:** Crie uma função `run_crest(input_xyz_path: str, output_dir: str, crest_keywords: str) -> str`.
            *   Ela deve executar o CREST via `subprocess`.
            *   Após a execução, deve identificar o arquivo `crest_best.xyz`.
            *   Deve retornar o caminho para `crest_best.xyz`.
        *   **Função MOPAC:** Crie uma função `run_mopac(input_pdb_path: str, output_dir: str, mopac_keywords: str) -> str`.
            *   Ela deve gerar o arquivo de input para o MOPAC (se necessário, o PDB já pode ser o input direto).
            *   Deve executar o MOPAC via `subprocess`.
            *   Deve retornar o caminho do arquivo de output (`.out`).
        *   **Função de Parsing:** Crie uma função `parse_mopac_output(output_file_path: str) -> float`.
            *   Ela deve ler o arquivo `.out` e extrair o valor de "FINAL HEAT OF FORMATION".
            *   Deve retornar o valor como `float`.

---

### **Fase 3: Persistência de Dados**

Foco em ler e escrever os dados nos arquivos CSV.

1.  **Tarefa 3.1: Serviço de Banco de Dados (`services/database_service.py`)**
    *   **Ação:** Crie um serviço para gerenciar os arquivos CSV.
    *   **Requisitos:**
        *   Use a biblioteca `pandas`.
        *   **Função de Leitura:** Crie `read_database(path: str) -> pd.DataFrame`.
        *   **Função de Escrita/Append:** Crie `append_to_database(new_data: dict, path: str)`.
            *   Esta função deve verificar se o arquivo em `path` existe.
            *   Se não existir, cria o arquivo com o cabeçalho correto (conforme `DATABASE_SCHEMA_v2.md`).
            *   Se existir, carrega o CSV, adiciona a nova linha (`new_data`) e salva sem sobrescrever.
            *   **Importante:** Implemente um mecanismo para evitar duplicatas, checando se um SMILES já existe no CSV antes de adicionar.

---

### **Fase 4: Interface do Usuário e Orquestração**

Montar tudo em uma aplicação funcional e interativa.

1.  **Tarefa 4.1: Orquestrador do Pipeline (`services/pipeline_orchestrator.py`)**
    *   **Ação:** Crie um serviço de alto nível que gerencia o fluxo completo para uma molécula.
    *   **Requisitos:**
        *   Crie uma função `process_single_molecule(identifier: str)`.
        *   Esta função chamará, em ordem:
            1.  `pubchem_service` (se `identifier` for um nome).
            2.  `conversion_service` (SDF -> XYZ).
            3.  `calculation_service.run_crest`.
            4.  `conversion_service` (crest_best.xyz -> PDB).
            5.  `calculation_service.run_mopac`.
            6.  `calculation_service.parse_mopac_output`.
            7.  `database_service.append_to_database` com todos os resultados coletados.
        *   Deve logar cada passo do processo.

2.  **Tarefa 4.2: Melhorar a CLI (`main.py`)**
    *   **Ação:** Expanda a CLI com comandos funcionais usando `Typer`.
    *   **Requisitos:**
        *   **Comando `run-single`:**
            *   `python main.py run-single --name "ethanol"`
            *   `python main.py run-single --smiles "CCO"`
            *   Este comando deve invocar o `pipeline_orchestrator.process_single_molecule`.
        *   **Comando `run-batch`:**
            *   `python main.py run-batch --file "molecules.txt"`
            *   Este comando deve ler o arquivo, iterar sobre cada molécula e chamar o orquestrador para cada uma.
        *   Use a biblioteca `rich` para exibir o progresso e os resultados de forma clara no console.

---

### **Fase 5: Análise e Integração**

Adicionar as funcionalidades de análise e verificação de progresso.

1.  **Tarefa 5.1: Serviço de Análise (`services/analysis_service.py`)**
    *   **Ação:** Crie o serviço para comparar os bancos de dados.
    *   **Requisitos:**
        *   Crie uma função `generate_progress_report(cbs_db_path: str, pm7_db_path: str)`.
        *   Ela deve ler os dois CSVs.
        *   Comparar os SMILES presentes em ambos.
        *   Imprimir um relatório no console: "X de Y moléculas calculadas (Z.Z%)".

2.  **Tarefa 5.2: Adicionar Comando de Análise à CLI (`main.py`)**
    *   **Ação:** Adicione um novo comando à CLI.
    *   **Requisitos:**
        *   **Comando `report`:**
            *   `python main.py report`
            *   Este comando chama a função `generate_progress_report`.
