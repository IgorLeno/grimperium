#!/bin/bash

# Script para corrigir permissões do CodeRabbit
# Execute este script se o CodeRabbit continuar fazendo commits

echo "🔧 Script de Correção - CodeRabbit Read-Only"
echo "==========================================="

# Verificar se o repositório está limpo
if ! git diff --quiet; then
    echo "⚠️  Há alterações não commitadas. Faça commit ou stash primeiro."
    exit 1
fi

echo "📋 Verificando configurações atuais..."

# 1. Verificar configuração do CodeRabbit
if [ -f ".coderabbit.yaml" ]; then
    echo "✅ Arquivo .coderabbit.yaml encontrado"
    
    # Verificar se contém as configurações restritivas
    if grep -q "MODO SOMENTE LEITURA" .coderabbit.yaml; then
        echo "✅ Configurações restritivas presentes"
    else
        echo "❌ Configurações restritivas ausentes"
    fi
else
    echo "❌ Arquivo .coderabbit.yaml não encontrado"
fi

# 2. Verificar últimos commits para identificar commits de bots
echo ""
echo "🔍 Verificando últimos 10 commits..."
git log --oneline -10 --pretty=format:"%h %an <%ae> %s" | while read line; do
    if echo "$line" | grep -iE "coderabbit|claude-code"; then
        echo "🚨 COMMIT SUSPEITO: $line"
    fi
done

# 3. Instruções para o GitHub
echo ""
echo "🔧 INSTRUÇÕES PARA CORRIGIR NO GITHUB:"
echo "=====================================+"
echo ""
echo "1. Acesse: https://github.com/$(git remote get-url origin | sed 's|.*github.com[:/]||' | sed 's|\.git||')/settings"
echo ""
echo "2. Vá em 'Integrations and services' ou 'Developer settings'"
echo ""
echo "3. Encontre 'CodeRabbit' na lista"
echo ""
echo "4. Clique em 'Configure' ou 'Settings'"
echo ""
echo "5. REMOVA as seguintes permissões se estiverem ativas:"
echo "   ❌ Write access to code"
echo "   ❌ Write access to pull requests (modificação)"
echo "   ❌ Write access to issues (criação)"
echo ""
echo "6. MANTENHA apenas:"
echo "   ✅ Read access to code"
echo "   ✅ Read access to metadata"
echo "   ✅ Write access to pull requests (comentários apenas)"
echo ""
echo "7. ATIVE Branch Protection Rules:"
echo "   - Settings → Branches → Add rule"
echo "   - Branch name pattern: main"
echo "   - ✅ Require pull request reviews before merging"
echo "   - ✅ Require status checks to pass before merging"
echo "   - ✅ Restrict pushes that create files"
echo ""
echo "8. Se o problema persistir:"
echo "   - Desinstale completamente o CodeRabbit"
echo "   - Reinstale com permissões mínimas"
echo ""
echo "📧 VERIFICAR EMAIL DE COMMITS:"
echo "Se você encontrou commits suspeitos, verifique o email do commit:"
echo "git log -1 --pretty=format:'%ae'"
echo ""
echo "Emails suspeitos geralmente contêm:"
echo "- @coderabbit"
echo "- @anthropic (para Claude)"
echo "- noreply@github.com (para GitHub Actions malconfigurados)"

# 4. Verificar se existe branch protection
echo ""
echo "🛡️  Para verificar Branch Protection Rules:"
echo "Execute: gh api repos/:owner/:repo/branches/main/protection"
echo "(Requer GitHub CLI instalado)"

echo ""
echo "✅ Script concluído. Siga as instruções acima para corrigir no GitHub."