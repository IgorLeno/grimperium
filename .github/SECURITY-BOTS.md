# 🔒 Configurações de Segurança dos Bots

## ⚠️ REGRAS CRÍTICAS

### **CodeRabbit: APENAS LEITURA**
- ❌ **PROIBIDO**: Fazer commits, criar branches, modificar arquivos
- ✅ **PERMITIDO**: Comentários de revisão, análise de código
- 🔧 **Configuração**: `.coderabbit.yaml` + `.github/coderabbit.config.yaml`

### **Gemini Code Assist: FORMATAÇÃO APENAS**
- ✅ **PERMITIDO**: Auto-formatação (Black, isort)
- ✅ **COMMITS**: Apenas para correções de estilo
- ❌ **PROIBIDO**: Alterações lógicas de código

### **Claude Code: LOCAL APENAS**
- 🏠 **USO**: Exclusivamente no terminal local
- ❌ **GITHUB**: Não deve ter workflows no repositório
- 🔧 **FUNÇÃO**: Implementação manual das sugestões

## 📋 Checklist de Verificação

### Se CodeRabbit estiver fazendo commits:

1. **Verificar configuração**: `.coderabbit.yaml`
   ```yaml
   auto_commit: false
   auto_merge: false
   auto_fix: false
   ```

2. **Verificar permissões no GitHub**:
   - Settings → Integrations → CodeRabbit
   - Remover permissões de escrita se existirem

3. **CODEOWNERS**: Arquivo `.github/CODEOWNERS` deve exigir aprovação humana

4. **Branch Protection**: Configure branch protection rules no GitHub

## 🚨 PROBLEMA: CodeRabbit Fazendo Commits

### **Solução Imediata**

1. **Execute o script de diagnóstico**:
   ```bash
   ./scripts/fix-coderabbit-permissions.sh
   ```

2. **Acesse GitHub Settings**:
   - Vá em `Settings` → `Integrations and services`
   - Encontre `CodeRabbit` → `Configure`
   - **REMOVA**: Write access to code, branches, pull requests
   - **MANTENHA**: Read access apenas

3. **Ative Branch Protection**:
   - `Settings` → `Branches` → `Add rule`
   - Branch: `main`
   - ✅ `Require pull request reviews before merging`
   - ✅ `Restrict pushes that create files`

### **Verificação**

```bash
# Verificar últimos commits suspeitos
git log --oneline -10 --pretty=format:"%h %an <%ae> %s" | grep -i coderabbit

# Verificar configuração atual
cat .coderabbit.yaml | grep -A5 -B5 "read_only\|auto_merge\|auto_commit"
```

### **Se o Problema Persistir**

1. **Desinstalar CodeRabbit** completamente do repositório
2. **Aguardar 24h** para propagação das alterações
3. **Reinstalar** com permissões mínimas (somente leitura)
4. **Testar** com um PR pequeno antes de uso completo

## 📞 Contatos de Suporte

- **CodeRabbit**: https://docs.coderabbit.ai/
- **GitHub Support**: https://support.github.com/
- **Configuração do Projeto**: Execute `./scripts/fix-coderabbit-permissions.sh`