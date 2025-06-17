
# **Grimperium**

## **📋 Visão Geral**

**Grimperium** é um sistema científico automatizado em Python (para WSL) que orquestra um pipeline de química computacional (CREST, MOPAC) para gerar dados termodinâmicos (entalpias de formação PM7). O objetivo é criar um banco de dados de baixo nível de teoria (LLOT) para treinar modelos de Aprendizado Delta (Δ-ML).

### **🎯 Funcionalidades Principais**

*   **Entrada Flexível**: Processa moléculas via nomes (PubChem), SMILES, listas ou arquivos.
*   **Pipeline Automatizado**: Orquestra o fluxo completo: PubChem → OpenBabel → CREST → MOPAC.
*   **Busca Conformacional Robusta**: Usa CREST para encontrar os confôrmeros de menor energia.
*   **Cálculos Rápidos**: Utiliza o método semi-empírico PM7 no MOPAC.
*   **Geração de Banco de Dados para ML**: Produz um arquivo `thermo_pm7.csv` pronto para uso.
*   **Monitoramento de Progresso**: Compara o progresso com um banco de dados de referência.

### **💻 Tecnologias**

*   **Linguagem**: Python 3.9+
*   **Ambiente**: WSL (Debian/Ubuntu)
*   **Química**: CREST, MOPAC, OpenBabel
*   **Bibliotecas Chave**: Pandas, RDKit, Typer, Rich, PyYAML

### **⚡ Instalação, Uso e Desenvolvimento**

Para o desenvolvimento guiado por IA, o documento principal é o plano de ação:
*   [**Plano de Ação para Desenvolvimento (ACTION_PLAN.md)**](ACTION_PLAN.md)

Para configurar o ambiente e entender a estrutura do projeto:
*   [**Guia de Instalação (INSTALL_v2.md)**](INSTALL_v2.md)
*   [**Arquitetura do Software (ARCHITECTURE_v2.md)**](ARCHITECTURE_v2.md)
*   [**Esquema do Banco de Dados (DATABASE_SCHEMA_v2.md)**](DATABASE_SCHEMA_v2.md)

### **🗺️ Roadmap Futuro**

*   **Fase 2:** Integração com Supabase para gerenciamento de dados na nuvem.
*   **Fase 3:** Implementação do módulo de treinamento do modelo Δ-ML.
*   **Fase 4:** Desenvolvimento de uma interface gráfica (GUI).

### **📄 Licença**

Este projeto está licenciado sob a Licença MIT.
