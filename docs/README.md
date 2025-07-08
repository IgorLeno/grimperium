# Grimperium

Ferramenta CLI para automação de cálculos em química computacional.

## Objetivo do Projeto

Grimperium orquestra a integração entre PubChem, CREST e MOPAC para automatizar a geração de dados termodinâmicos moleculares através de uma interface de linha de comando amigável.

## Tecnologias Principais

- **Python 3.9+** - Linguagem principal
- **Conda** - Gerenciamento de ambiente
- **Typer** - Interface de linha de comando
- **Questionary** - Menu interativo
- **Rich** - Interface de usuário colorida
- **Pandas** - Manipulação de dados
- **CREST** - Busca conformacional
- **MOPAC** - Cálculos quânticos
- **OpenBabel** - Manipulação de estruturas moleculares

## Instalação e Execução

### Configuração do Ambiente

```bash
conda create --name grimoire python=3.9
conda activate grimoire
pip install -r requirements.txt
```

### Executar o Grimperium

**Modo Interativo** (Recomendado):
```bash
python main.py
```

**Comandos Diretos**:
```bash
# Processar uma única molécula
python main.py run-single --name "propanol"
python main.py run-single --smiles "CCO"

# Processar lote de moléculas
python main.py run-batch molecules.txt

# Ver informações do sistema
python main.py info

# Gerar relatório de progresso
python main.py report --detailed
```

## Estrutura do Projeto

O Grimperium utiliza um layout src-layout com código organizado em:
- `grimperium/services/` - Lógica de negócio (PubChem, CREST, MOPAC, Database)
- `grimperium/utils/` - Utilitários de configuração
- `grimperium/core/` - Classes principais do domínio
- `config.yaml` - Configuração central
- `data/` - Persistência local em CSV

## Contribuição

Para desenvolvedores: consulte o arquivo `claude.md` para contexto detalhado sobre arquitetura e padrões de desenvolvimento.