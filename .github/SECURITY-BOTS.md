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

## 🚨 Ações Imediatas se Bots Estiverem Fazendo Commits Indevidos

1. **Desabilitar bot temporariamente**
2. **Revisar últimos commits** para alterações não autorizadas
3. **Ajustar configurações** conforme documentado
4. **Reativar bot** apenas após confirmação de configuração correta

## 📞 Suporte

Se os bots continuarem fazendo commits após essas configurações:
1. Verificar configurações do repositório no GitHub
2. Revisar integrações ativas no repositório
3. Contatar suporte das ferramentas específicas