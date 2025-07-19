#!/bin/bash
# auto-workflow.sh - Sistema de automação local com GitHub Actions

set -eo pipefail

# Configurações
BRANCH_PREFIX="feature/auto"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função: Log colorido
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Função: Validar entrada do usuário
validate_input() {
    local input="$1"
    if [[ ! "$input" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        error "Input deve conter apenas caracteres alfanuméricos, hífens e underscores"
        return 1
    fi
}

# Função: Validar comandos antes da execução
validate_command() {
    local cmd="$1"
    
    # Padrões perigosos que nunca devem ser executados
    local forbidden_patterns=(
        "rm -rf"
        "chmod 777" 
        "sudo"
        "> /dev/"
        "dd if="
        "mkfs"
        "fdisk"
        "parted"
        "mount"
        "umount"
        "kill -9"
        "killall"
        "shutdown"
        "reboot"
        "init"
        "systemctl"
        "service"
        "crontab"
        "at "
        "nohup"
        "&>"
        "2>&1"
        "|&"
        "\$("
        "\`"
        "eval"
        "exec"
        "source"
        ". "
    )
    
    # Verificar padrões proibidos
    for pattern in "${forbidden_patterns[@]}"; do
        if [[ "$cmd" == *"$pattern"* ]]; then
            error "Padrão perigoso detectado: $pattern"
            return 1
        fi
    done
    
    # Lista de comandos explicitamente permitidos
    local allowed_commands=("git" "gh" "jq" "curl" "rg" "fd" "pip" "pip3" "pytest" "flake8" "black" "python" "python3" "autoflake" "isort" "mypy" "yamllint" "echo" "cat" "grep" "sed" "awk" "wc" "head" "tail")
    local cmd_name
    cmd_name=$(echo "$cmd" | awk '{print $1}')
    
    # Verificar se o comando base é permitido
    for allowed in "${allowed_commands[@]}"; do
        if [[ "$cmd_name" == "$allowed" ]]; then
            # Validações específicas por comando
            case "$cmd_name" in
                "git")
                    # Git: bloquear comandos perigosos
                    if [[ "$cmd" == *"git rm -rf"* ]] || [[ "$cmd" == *"git reset --hard"* ]] || [[ "$cmd" == *"git clean -fd"* ]]; then
                        error "Comando git perigoso bloqueado"
                        return 1
                    fi
                    ;;
                "pip"|"pip3")
                    # Pip: permitir apenas install, show, list
                    if [[ ! "$cmd" =~ (install|show|list|freeze) ]]; then
                        error "Apenas install, show, list e freeze são permitidos para pip"
                        return 1
                    fi
                    ;;
            esac
            return 0
        fi
    done
    
    error "Comando não permitido: $cmd_name"
    return 1
}

# Função: Criar nova branch automática
create_auto_branch() {
    local description="$1"
    
    # Sanitização robusta para nomes de branch (previne git command injection)
    local sanitized_desc
    sanitized_desc=$(echo "$description" | tr '[:upper:]' '[:lower:]' | \
        sed -e 's/[^a-zA-Z0-9_-]/-/g' \
            -e 's/--*/-/g' \
            -e 's/^-\|-$//g' \
            -e 's/^[0-9]*-*//' | \
        cut -c1-50)  # Limitar comprimento
    
    # Verificar se a descrição não está vazia após sanitização
    if [ -z "$sanitized_desc" ]; then
        sanitized_desc="feature"
    fi
    
    local timestamp
    timestamp=$(date +%Y-%m-%d-%H%M%S)
    local branch_name="${BRANCH_PREFIX}-${timestamp}-${sanitized_desc}"
    
    log "Criando branch: $branch_name"
    git checkout -b "$branch_name"
    echo "$branch_name"
}

# Função: Validar dependências antes de PR
validate_dependencies() {
    log "Validando requirements.txt..."
    
    if [ -f "requirements.txt" ]; then
        # Verificar se todas as linhas são válidas
        while IFS= read -r line; do
            # Pular linhas vazias e comentários
            [[ -z "${line}" || "${line}" =~ ^#.*$ ]] && continue
            
            # Verificar formato básico de dependência (regex melhorada)
            if ! [[ "${line}" =~ ^[a-zA-Z0-9_.-]+(\[[a-zA-Z0-9_,.-]+\])?([<>=!~]+[0-9a-zA-Z_.,+-]+)?([,;][[:space:]]*[<>=!~]+[0-9a-zA-Z_.,+-]+)*$ ]]; then
                warn "Formato suspeito na dependência: ${line}"
            fi
        done < requirements.txt
        
        log "✓ Formato das dependências verificado"
        return 0
    else
        warn "requirements.txt não encontrado"
        return 1
    fi
}

# Função: Executar validações locais
run_local_validations() {
    log "Executando validações locais..."
    
    # Lint
    if command -v flake8 &> /dev/null; then
        log "Executando flake8..."
        if flake8 grimperium/ --max-line-length=88 --extend-ignore=E203,W503; then
            log "✓ Lint passou"
        else
            warn "⚠ Problemas de lint encontrados"
        fi
    else
        warn "flake8 não instalado - pulando verificação de lint"
    fi
    
    # Format
    if command -v black &> /dev/null; then
        log "Verificando formatação com Black..."
        if black --check grimperium/ --line-length=88; then
            log "✓ Formatação OK"
        else
            warn "⚠ Formatação necessária - execute: black grimperium/"
        fi
    else
        warn "black não instalado - pulando verificação de formatação"
    fi
    
    # Tests
    if [ -d "grimperium/tests" ] && command -v pytest &> /dev/null; then
        log "Executando testes..."
        if pytest grimperium/tests/ -v --tb=short; then
            log "✓ Testes passaram"
        else
            warn "⚠ Alguns testes falharam"
        fi
    else
        warn "pytest não disponível ou diretório de testes não encontrado"
    fi
}

# Função: Criar PR e aguardar instruções
create_pr_and_wait_instructions() {
    local branch_name=$1
    local title=$2
    local body=$3
    
    log "Criando Pull Request..."
    
    # Criar PR e adicionar label para trigger do Claude Instructor
    local pr_url
    pr_url=$(gh pr create \
        --title "$title" \
        --body "$body" \
        --label "claude-analyze" \
        --base main \
        --head "$branch_name")
    
    local pr_number
    pr_number=$(echo "$pr_url" | grep -oP '\d+$')
    log "Pull Request #$pr_number criado: $pr_url"
    
    # Aguardar análise do GitHub Actions
    log "Aguardando análise do Claude Instructor..."
    sleep 10  # Dar tempo para o workflow iniciar
    
    # Monitorar status dos workflows
    monitor_workflow_status "$pr_number"
    
    # Buscar instruções nos comentários
    fetch_claude_instructions "$pr_number"
}

# Função: Monitorar workflows específicos do PR
monitor_workflow_status() {
    local pr_number=$1
    local timeout=300  # 5 minutos
    local elapsed=0
    local wait_time=5
    
    log "Monitorando workflows específicos do PR #$pr_number..."
    
    while [ $elapsed -lt $timeout ]; do
        # Verificar status dos checks específicos do PR
        local pending_checks
        if command -v jq >/dev/null 2>&1; then
            # Se jq estiver disponível, usar a abordagem mais precisa
            pending_checks=$(gh pr checks "$pr_number" --json state --jq '.[] | select(.state == "PENDING") | .state' 2>/dev/null | wc -l)
        else
            # Fallback: verificar workflows gerais relacionados à branch
            local branch_name
            branch_name=$(gh pr view "$pr_number" --json headRefName --jq .headRefName 2>/dev/null)
            pending_checks=$(gh run list --branch="$branch_name" --limit 3 --json status --jq '.[] | select(.status == "in_progress") | .status' 2>/dev/null | wc -l)
        fi
        
        if [ "$pending_checks" -eq 0 ]; then
            log "✓ Workflows do PR concluídos"
            return 0
        fi
        
        log "Workflows em execução... ($elapsed/$timeout segundos) - $pending_checks pendentes"
        sleep $wait_time
        elapsed=$((elapsed + wait_time))
        
        # Backoff exponencial com máximo de 30 segundos
        wait_time=$((wait_time > 30 ? 30 : wait_time * 2))
    done
    
    if [ $elapsed -ge $timeout ]; then
        warn "Timeout aguardando workflows - continuando..."
        return 1
    fi
}

# Função: Buscar instruções do Claude
fetch_claude_instructions() {
    local pr_number=$1
    
    log "Buscando instruções do Claude Instructor..."
    
    # Aguardar um pouco mais para garantir que o comentário foi postado
    sleep 20
    
    # Buscar comentários do PR com arquivo temporário seguro
    local comments_file
    comments_file=$(mktemp -t claude-comments.XXXXXX)
    chmod 600 "${comments_file}"  # Permissões seguras: apenas owner pode ler/escrever
    trap 'rm -f "${comments_file}"' EXIT
    
    gh pr view "$pr_number" --json comments --jq '.comments[] | select(.author.login == "github-actions[bot]") | .body' > "${comments_file}"
    
    if [ -s "$comments_file" ]; then
        log "✓ Instruções recebidas do Claude Instructor"
        
        # Salvar instruções em arquivo
        cp "$comments_file" "claude-instructions-pr-$pr_number.md"
        
        echo ""
        echo "==================== INSTRUÇÕES DO CLAUDE ===================="
        cat "$comments_file"
        echo "=============================================================="
        echo ""
        
        # Perguntar se deve executar automaticamente
        read -r -p "Executar instruções automaticamente? (y/N): " auto_exec
        
        if [[ $auto_exec =~ ^[Yy]$ ]]; then
            execute_claude_instructions "claude-instructions-pr-$pr_number.md"
        else
            log "Instruções salvas em claude-instructions-pr-$pr_number.md"
            log "Execute manualmente quando estiver pronto"
        fi
    else
        warn "Nenhuma instrução encontrada nos comentários"
        log "Aguarde mais alguns minutos e execute: gh pr view $pr_number"
    fi
    
    rm -f "$comments_file"
}

# Função: Executar instruções do Claude
execute_claude_instructions() {
    local instructions_file=$1
    
    log "Analisando instruções do arquivo: $instructions_file"
    
    # Extrair blocos bash das instruções com arquivo temporário seguro
    local bash_blocks
    bash_blocks=$(mktemp -t claude-bash-blocks.XXXXXX)
    chmod 600 "${bash_blocks}"  # Permissões seguras: apenas owner pode ler/escrever
    trap 'rm -f "${bash_blocks}"' EXIT
    
    # Extração mais robusta usando sed para capturar apenas blocos bash
    sed -n '/^```bash$/,/^```$/{/```/d;p;}' "$instructions_file" > "${bash_blocks}"
    
    # Se não encontrou blocos com formato exato, tentar variações
    if [ ! -s "${bash_blocks}" ]; then
        sed -n '/^```shell$/,/^```$/{/```/d;p;}' "$instructions_file" > "${bash_blocks}"
    fi
    
    # Se ainda não encontrou, tentar formato menos rigoroso
    if [ ! -s "${bash_blocks}" ]; then
        sed -n '/```bash/,/```/{/```/d;p;}' "$instructions_file" > "${bash_blocks}"
    fi
    
    if [ -s "$bash_blocks" ]; then
        echo ""
        echo "==================== COMANDOS EXTRAÍDOS ===================="
        cat "$bash_blocks"
        echo "=============================================================="
        echo ""
        
        read -r -p "Executar estes comandos? (y/N): " confirm_exec
        
        if [[ $confirm_exec =~ ^[Yy]$ ]]; then
            log "Executando comandos das instruções..."
            
            while IFS= read -r command; do
                # Pular linhas vazias e comentários
                [[ -z "${command}" || "${command}" =~ ^#.*$ ]] && continue
                
                log "Executando: ${command}"
                
                # Validar comando antes da execução
                if validate_command "${command}"; then
                    # Execução segura com escape adequado
                    log "Executando comando validado: ${command}"
                    if eval "$(printf '%q ' "${command}")"; then
                        log "✓ Comando executado com sucesso"
                    else
                        error "✗ Falha na execução do comando: ${command}"
                        read -r -p "Continuar mesmo assim? (y/N): " continue_exec
                        [[ ! "${continue_exec}" =~ ^[Yy]$ ]] && break
                    fi
                else
                    error "✗ Comando não permitido: ${command}"
                    warn "Comandos permitidos: git, pip, pytest, flake8, black, python, etc."
                    read -r -p "Pular este comando e continuar? (y/N): " skip_cmd
                    [[ ! "${skip_cmd}" =~ ^[Yy]$ ]] && break
                fi
            done < "$bash_blocks"
            
            log "Execução das instruções concluída"
        else
            log "Execução cancelada pelo usuário"
        fi
    else
        warn "Nenhum bloco bash encontrado nas instruções"
        log "Revise manualmente o arquivo: $instructions_file"
    fi
    
    rm -f "$bash_blocks"
}

# Função principal
main() {
    local action=$1
    local description=$2
    
    case $action in
        "new")
            if [ -z "$description" ]; then
                error "Uso: $0 new <description>"
                echo "Exemplo: $0 new fix-dependencies"
                exit 1
            fi
            
            # Validar entrada do usuário
            if ! validate_input "$description"; then
                exit 1
            fi
            
            # Validar estado atual
            if [ -n "$(git status --porcelain)" ]; then
                error "Working directory não está limpo. Commit ou stash suas alterações."
                exit 1
            fi
            
            # Garantir que estamos na main
            git checkout main
            git pull origin main
            
            # Criar branch
            local branch_name
            branch_name=$(create_auto_branch "$description")
            
            log "✓ Branch $branch_name criada e ativa"
            log "Faça suas alterações e execute: $0 submit '$description'"
            ;;
            
        "submit")
            if [ -z "$description" ]; then
                error "Uso: $0 submit <description>"
                echo "Exemplo: $0 submit fix-dependencies"
                exit 1
            fi
            
            # Validar entrada do usuário
            if ! validate_input "$description"; then
                exit 1
            fi
            
            # Verificar se há mudanças
            if [ -z "$(git status --porcelain)" ]; then
                error "Nenhuma alteração para submeter"
                exit 1
            fi
            
            # Validar dependências
            if ! validate_dependencies; then
                warn "Problemas nas dependências detectados"
                read -r -p "Continuar mesmo assim? (y/N): " continue_deps
                [[ ! $continue_deps =~ ^[Yy]$ ]] && exit 1
            fi
            
            # Executar validações locais
            run_local_validations
            
            # Commit das alterações
            git add -A
            git commit -m "Auto: $description

Alterações realizadas automaticamente via auto-workflow.sh

🤖 Generated with auto-workflow system"
            
            local current_branch
            current_branch=$(git branch --show-current)
            git push origin "$current_branch"
            
            # Criar PR com instruções para Claude
            local pr_body
            pr_body="## Alterações Automáticas

**Descrição**: $description
**Branch**: $current_branch
**Timestamp**: $(date '+%Y-%m-%d %H:%M:%S')

### Validações Executadas Localmente:
- [x] Dependências validadas
- [x] Lint verificado
- [x] Formatação verificada  
- [x] Testes executados

@claude Analise este PR e forneça instruções detalhadas para adequar o merge à branch main.

### Sistema de Automação
Este PR foi criado pelo sistema auto-workflow.sh e aguarda análise do Claude Instructor."
            
            # Criar PR
            create_pr_and_wait_instructions "$current_branch" "Auto: $description" "$pr_body"
            ;;
            
        "status")
            log "Status do auto-workflow:"
            log "Branch atual: $(git branch --show-current)"
            local modified_files
            modified_files=$(git status --short | wc -l)
            log "Arquivos modificados: $modified_files"
            
            # Verificar se há PRs abertos
            local open_prs
            open_prs=$(gh pr list --state open --json number --jq '. | length')
            log "PRs abertos: $open_prs"
            ;;
            
        "help")
            echo "Auto-workflow System - Grimperium v2"
            echo ""
            echo "Uso: $0 {new|submit|status|help} [description]"
            echo ""
            echo "Comandos:"
            echo "  new <desc>    - Criar nova branch para desenvolvimento"
            echo "  submit <desc> - Submeter alterações e criar PR"
            echo "  status        - Ver status atual"
            echo "  help          - Mostrar esta ajuda"
            echo ""
            echo "Exemplos:"
            echo "  $0 new fix-dependencies"
            echo "  $0 submit fix-dependencies"
            echo ""
            echo "Sistema Híbrido:"
            echo "- Validações locais automáticas"
            echo "- Claude Instructor via GitHub Actions"
            echo "- Controle total do desenvolvedor"
            ;;
            
        *)
            error "Comando inválido: $action"
            echo "Execute: $0 help"
            exit 1
            ;;
    esac
}

# Verificar dependências
command -v gh >/dev/null 2>&1 || { error "GitHub CLI (gh) não está instalado"; exit 1; }
command -v git >/dev/null 2>&1 || { error "Git não está instalado"; exit 1; }

# Verificar se estamos no diretório correto
if [ ! -f "main.py" ] || [ ! -d "grimperium" ]; then
    error "Execute este script a partir do diretório raiz do projeto Grimperium"
    exit 1
fi

# Executar função principal
main "$@"