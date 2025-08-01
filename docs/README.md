# Grimperium v2

Ferramenta CLI para automação de cálculos em química computacional.

## Objetivo do Projeto

Grimperium orquestra a integração entre PubChem, CREST e MOPAC para automatizar a geração de dados termodinâmicos moleculares através de uma interface de linha de comando amigável. O sistema processa moléculas através de um pipeline completo: busca estrutural → busca conformacional → cálculos quânticos → armazenamento em banco de dados.

## Tecnologias Principais

- **Python 3.9+** - Linguagem principal
- **Conda** - Gerenciamento de ambiente
- **Typer** - Interface de linha de comando
- **Questionary** - Menu interativo
- **Rich** - Interface de usuário colorida
- **Pandas** - Manipulação de dados
- **CREST** - Busca conformacional
- **MOPAC** - Cálculos quânticos semi-empíricos
- **OpenBabel** - Manipulação de estruturas moleculares
- **PubChemPy** - Integração com PubChem

## Pré-requisitos

### Dependências Externas
- **CREST** - Para busca conformacional
- **MOPAC** - Para cálculos quânticos PM7
- **OpenBabel** - Para conversão de formatos moleculares

### Instalação das Dependências Python
```bash
# Criar ambiente conda
conda create --name grimperium python=3.9
conda activate grimperium

# Instalar dependências Python
pip install -r requirements.txt
```

## Configuração e Execução

### 1. Configuração Inicial
O arquivo `config.yaml` contém as configurações principais:
```yaml
executables:
  crest: 'crest'      # Comando para CREST
  mopac: 'mopac'      # Comando para MOPAC
  obabel: 'obabel'    # Comando para OpenBabel

mopac_keywords: 'PM7 EF PRECISE GNORM=0.01 NOINTER GRAPHF VECTORS MMOK CYCLES=20000'
crest_keywords: '--gfn2'
repository_base_path: 'repository'

logging:
  log_file: 'logs/grim_details.log'
  console_level: 'INFO'
  file_level: 'DEBUG'

database:
  cbs_db_path: 'data/thermo_cbs.csv'
  pm7_db_path: 'data/thermo_pm7.csv'
```

### 2. Verificação do Sistema
```bash
# Verificar se todas as dependências estão instaladas
python main.py info
```

### 3. Executar o Grimperium

**Modo Interativo** (Recomendado):
```bash
python main.py
```

**Comandos Diretos**:
```bash
# Processar uma única molécula por nome
python main.py run-single --name "propanol"

# Processar uma única molécula por SMILES
python main.py run-single --smiles "CCO"

# Processar lote de moléculas de um arquivo
python main.py run-batch molecules.txt

# Ver informações detalhadas do sistema
python main.py info

# Gerar relatório de progresso
python main.py report
python main.py report --detailed
python main.py report --missing 10
```

## Estrutura do Projeto

O Grimperium utiliza uma arquitetura modular com separação clara de responsabilidades:

```
grimperium/
├── main.py                  # Ponto de entrada da aplicação
├── config.yaml              # Arquivo de configuração principal
├── requirements.txt         # Dependências Python
├── grimperium/              # Pacote principal do código-fonte
│   ├── config/              # Módulo de configuração
│   ├── core/                # Classes de domínio (ex: Molecule)
│   ├── services/            # Lógica de negócios
│   ├── tests/               # Testes automatizados
│   ├── ui/                  # Componentes de interface (CLI)
│   └── utils/               # Utilitários (logging, config_manager)
├── data/                    # Dados de entrada (listas, CSVs)
├── docs/                    # Documentação do projeto
├── logs/                    # Arquivos de log
├── repository/              # Saída dos cálculos
└── scripts/                 # Scripts de automação e utilitários
```

## Fluxo de Trabalho

1. **Entrada**: Nome químico ou SMILES
2. **PubChem**: Busca e download da estrutura 3D (SDF)
3. **Conversão**: SDF → XYZ (OpenBabel)
4. **CREST**: Busca conformacional (XYZ → PDB)
5. **MOPAC**: Cálculo quântico PM7 (PDB → dados termodinâmicos)
6. **Armazenamento**: Dados salvos em `data/thermo_pm7.csv`

## Arquivos de Dados

- **`data/thermo_cbs.csv`** - Banco de dados de referência CBS
- **`data/thermo_pm7.csv`** - Resultados dos cálculos PM7
- **`repository/`** - Arquivos temporários de cálculo organizados por molécula

## Contribuição

Para desenvolvedores: consulte o arquivo `CLAUDE.md` para contexto detalhado sobre arquitetura e padrões de desenvolvimento.

## Logs e Debugging

O sistema gera logs detalhados em `logs/grim_details.log`. Use o comando `info` para diagnóstico do sistema e verificação de dependências.

![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/IgorLeno/grimperium?utm_source=oss&utm_medium=github&utm_campaign=IgorLeno%2Fgrimperium&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)

## Licença

Este projeto é desenvolvido para uso acadêmico e de pesquisa em química computacional.