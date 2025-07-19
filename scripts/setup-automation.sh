#!/bin/bash
# setup-automation.sh - Configuração inicial do sistema de automação

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[SETUP] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Função: Verificar dependências do sistema
check_system_dependencies() {
    log "Verificando dependências do sistema..."
    
    local missing_deps=()
    
    # Verificar Git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    # Verificar GitHub CLI
    if ! command -v gh &> /dev/null; then
        missing_deps+=("gh")
    fi
    
    # Verificar Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Verificar pip
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        missing_deps+=("pip")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        error "Dependências ausentes: ${missing_deps[*]}"
        echo ""
        echo "Instale as dependências ausentes:"
        echo "  Ubuntu/Debian: sudo apt install git python3 python3-pip"
        echo "  GitHub CLI: https://cli.github.com/"
        echo ""
        exit 1
    fi
    
    log "✓ Todas as dependências do sistema estão instaladas"
}

# Função: Instalar dependências Python
install_python_dependencies() {
    log "Instalando dependências Python para desenvolvimento..."
    
    # Dependências essenciais para o sistema de automação
    local dev_deps=(
        "flake8"
        "black"
        "pytest"
        "pytest-cov"
        "pytest-mock"
    )
    
    # Verificar quais dependências já estão instaladas
    local to_install=()
    for dep in "${dev_deps[@]}"; do
        if ! pip show "$dep" &> /dev/null && ! pip3 show "$dep" &> /dev/null; then
            to_install+=("$dep")
        fi
    done
    
    if [ ${#to_install[@]} -gt 0 ]; then
        log "Instalando: ${to_install[*]}"
        
        # Usar pip3 se disponível, senão pip
        local pip_cmd="pip"
        if command -v pip3 &> /dev/null; then
            pip_cmd="pip3"
        fi
        
        if $pip_cmd install "${to_install[@]}"; then
            log "✓ Dependências Python instaladas com sucesso"
        else
            warn "Algumas dependências falharam na instalação"
            info "Tente instalar manualmente: $pip_cmd install ${to_install[*]}"
        fi
    else
        log "✓ Todas as dependências Python já estão instaladas"
    fi
}

# Função: Configurar permissões
setup_permissions() {
    log "Configurando permissões dos scripts..."
    
    # Dar permissão de execução ao script principal
    if [ -f "scripts/auto-workflow.sh" ]; then
        chmod +x scripts/auto-workflow.sh
        log "✓ Permissões configuradas para auto-workflow.sh"
    else
        error "Script auto-workflow.sh não encontrado"
        exit 1
    fi
    
    # Dar permissão de execução ao próprio setup
    chmod +x scripts/setup-automation.sh
}

# Função: Configurar aliases úteis
setup_aliases() {
    log "Configurando aliases úteis..."
    
    local alias_file="$HOME/.bash_aliases"
    local grimperium_aliases="
# Grimperium Auto-Workflow Aliases
alias grim-new='./scripts/auto-workflow.sh new'
alias grim-submit='./scripts/auto-workflow.sh submit'
alias grim-status='./scripts/auto-workflow.sh status'
alias grim-help='./scripts/auto-workflow.sh help'
"
    
    # Verificar se os aliases já existem
    if [ -f "$alias_file" ] && grep -q "Grimperium Auto-Workflow" "$alias_file"; then
        log "✓ Aliases já configurados"
    else
        echo "$grimperium_aliases" >> "$alias_file"
        log "✓ Aliases adicionados a $alias_file"
        info "Execute 'source ~/.bash_aliases' ou reinicie o terminal para usar os aliases"
    fi
}

# Função: Verificar configuração do GitHub CLI
check_github_auth() {
    log "Verificando autenticação do GitHub CLI..."
    
    if gh auth status &> /dev/null; then
        log "✓ GitHub CLI autenticado"
        local user
        user=$(gh api user --jq .login)
        info "Usuário logado: $user"
    else
        warn "GitHub CLI não está autenticado"
        info "Execute: gh auth login"
        echo ""
        read -r -p "Configurar autenticação agora? (y/N): " setup_auth
        
        if [[ $setup_auth =~ ^[Yy]$ ]]; then
            gh auth login
        else
            warn "Configure a autenticação depois com: gh auth login"
        fi
    fi
}

# Função: Teste básico do sistema
test_basic_functionality() {
    log "Testando funcionalidade básica..."
    
    # Testar se o script principal executa
    if ./scripts/auto-workflow.sh help &> /dev/null; then
        log "✓ Script auto-workflow.sh executando corretamente"
    else
        error "Problema na execução do auto-workflow.sh"
        exit 1
    fi
    
    # Testar dependências Python básicas
    local python_cmd="python3"
    if ! command -v python3 &> /dev/null; then
        python_cmd="python"
    fi
    
    if $python_cmd -c "import flake8, black, pytest" 2> /dev/null; then
        log "✓ Dependências Python importando corretamente"
    else
        warn "Algumas dependências Python podem não estar funcionando"
    fi
    
    # Testar se estamos no diretório correto do projeto
    if [ -f "main.py" ] && [ -d "grimperium" ]; then
        log "✓ Diretório do projeto Grimperium detectado"
    else
        error "Execute este setup a partir do diretório raiz do projeto Grimperium"
        exit 1
    fi
}

# Função: Mostrar resumo da configuração
show_setup_summary() {
    echo ""
    echo "=========================================="
    log "CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!"
    echo "=========================================="
    echo ""
    info "Sistema híbrido de automação configurado:"
    echo "  ✓ Claude Instructor (GitHub Actions)"
    echo "  ✓ Validações locais automáticas"
    echo "  ✓ Scripts de workflow"
    echo "  ✓ Configurações personalizadas"
    echo ""
    info "Comandos disponíveis:"
    echo "  ./scripts/auto-workflow.sh new <descrição>"
    echo "  ./scripts/auto-workflow.sh submit <descrição>"
    echo "  ./scripts/auto-workflow.sh status"
    echo "  ./scripts/auto-workflow.sh help"
    echo ""
    info "Aliases configurados (após source ~/.bash_aliases):"
    echo "  grim-new <descrição>"
    echo "  grim-submit <descrição>"
    echo "  grim-status"
    echo "  grim-help"
    echo ""
    info "Arquivos de configuração:"
    echo "  .claude/config/local-automation.yml"
    echo "  .github/workflows/claude.yml (modo instrutor)"
    echo ""
    warn "Próximos passos:"
    echo "  1. Teste com: ./scripts/auto-workflow.sh help"
    echo "  2. Crie uma feature: ./scripts/auto-workflow.sh new test-feature"
    echo "  3. Faça alterações e submit: ./scripts/auto-workflow.sh submit test-feature"
    echo ""
}

# Função principal
main() {
    echo "=========================================="
    log "CONFIGURAÇÃO DO SISTEMA DE AUTOMAÇÃO"
    log "Grimperium v2 - Sistema Híbrido"
    echo "=========================================="
    echo ""
    
    # Executar todas as verificações e configurações
    check_system_dependencies
    install_python_dependencies
    setup_permissions
    setup_aliases
    check_github_auth
    test_basic_functionality
    show_setup_summary
}

# Verificar se estamos no diretório correto antes de começar
if [ ! -f "main.py" ] || [ ! -d "grimperium" ]; then
    error "Execute este script a partir do diretório raiz do projeto Grimperium"
    exit 1
fi

# Executar configuração
main "$@"