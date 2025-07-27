## 📝 Resumo das Alterações
<!-- Descreva brevemente as mudanças implementadas -->

## 🔧 Tipo de Mudança
- [ ] 🐛 **Bug fix** - Correção de funcionalidade
- [ ] ✨ **Nova feature** - Adição de funcionalidade
- [ ] 🔄 **Refatoração** - Melhoria de código existente
- [ ] 📚 **Documentação** - Atualização de docs
- [ ] 🧪 **Testes** - Adição/correção de testes
- [ ] ⚡ **Performance** - Otimização de performance
- [ ] 🔒 **Segurança** - Correção de vulnerabilidade

## ✅ Checklist Pré-Review
- [ ] **Formatação**: Código segue PEP 8 (verificado com `black . && flake8 .`)
- [ ] **Testes**: Cobertura mantida/melhorada (`pytest --cov=grimperium`)
- [ ] **Linting**: Sem erros de lint (`flake8 grimperium/`)
- [ ] **Type Hints**: Anotações de tipo adicionadas quando apropriado
- [ ] **Logs**: Logging adequado implementado nos services
- [ ] **Docs**: Docstrings atualizadas (formato Google-style)

## 🤖 Fluxo de Review Automatizado

### **CodeRabbit**: Revisor Read-Only 📋
- ✅ **APENAS REVISÃO**: Análise de código em português
- ✅ **FEEDBACK TEXTUAL**: Sugestões e comentários
- ❌ **NÃO FAZ**: Commits, branches, alterações de código
- 🎯 **Função**: Identificar problemas e sugerir melhorias

### **Gemini Code Assist**: Formatação Automática 🔧
- ✅ **AUTO-CORREÇÃO**: Formatação (Black, isort) quando necessário
- ✅ **COMMITS AUTOMÁTICOS**: Apenas para formatação
- 🎯 **Função**: Manter consistência de estilo

### **Claude Code**: Implementação Manual 💻
- 🔧 **USO LOCAL**: Terminal para implementar correções
- 📋 **PROMPTS ESTRUTURADOS**: Baseados no feedback dos bots
- 🎯 **Função**: Implementação das sugestões de revisão

## 📊 Comandos de Verificação Local

```bash
# Verificação completa antes do push
pytest --cov=grimperium --cov-report=html
black . && flake8 grimperium/
python main.py info  # Verificar configuração do sistema
```

## 🎯 Arquivos Modificados
<!-- Liste os principais arquivos alterados e o motivo -->

## 🧠 Contexto para Review
<!-- Informações relevantes que ajudem na análise do código -->

---
**💡 Dica**: Os bots irão gerar automaticamente prompts estruturados para facilitar a implementação das correções sugeridas no Claude Code local.
