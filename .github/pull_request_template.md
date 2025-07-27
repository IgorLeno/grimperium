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

### **CodeRabbit**: Revisor Principal
- ✅ Análise automática de código em português
- ✅ Verificação de padrões Python e Pydantic
- ✅ Validação de arquitetura de services

### **Gemini Code Assist**: Formatação Automática  
- ✅ Correções automáticas de formatação (Black, isort)
- ✅ Aplicação apenas quando necessário

### **Claude Code**: Implementação Local
- 🔧 Use no terminal para implementar correções sugeridas
- 📋 Consulte os prompts estruturados gerados pelos bots

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
