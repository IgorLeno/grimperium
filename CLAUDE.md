# Memória do Projeto Grimperium

Este arquivo armazena as diretrizes, arquitetura, e workflows para o projeto Grimperium, servindo como a fonte central de verdade para a colaboração com o Claude Code.

---

## 1. Visão Geral do Projeto

O Grimperium é uma ferramenta CLI em Python que automatiza um pipeline de química computacional (PubChem -> CREST -> MOPAC). O status atual é de MVP funcional e completo.

A fonte da verdade para o código é o repositório no GitHub: https://github.com/IgorLeno/grimperium

## 2. Arquitetura e Tecnologias

- **Linguagem:** Python
- **Gerenciador de Pacotes:** Conda
- **CLI Framework:** Typer
- **UI/UX:** Rich
- **Testes:** Pytest
- **Manipulação de Dados:** Pandas
- **Configuração:** YAML

## 3. Padrões de Código e Estilo

- Use indentação de 4 espaços.
- Siga as convenções da PEP 8.
- Adicione docstrings a todas as funções e métodos públicos.
- Os tipos de retorno e de parâmetros devem ser anotados.

## 4. Workflows Comuns

- **Para executar os testes:** `pytest`
- **Para iniciar a aplicação:** `python -m grimperium.main`

## 5. Configuração de MCPs (Model Context Protocol)

- **Objetivo Futuro:** Ativar os MCPs de Filesystem, GitHub e Web Research.
- **Verificação:** O comando `/mcp list` será usado para verificar os servidores ativos assim que forem configurados.

## 6. Imports de Contexto

Para manter este arquivo conciso e sempre atualizado com a documentação principal, importamos o README do projeto.

@./README.md
