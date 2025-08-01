CLAUDE.md - Grimperium v2 Project Context

Notice: Multi-Agent Context Separation
This file is intended exclusively for Claude Code agent sessions for the Grimperium project.
Do not use or reference this file in AMP (ampcode) agent sessions.
For AMP context, always use AGENT.md in the project directory.

Quick Context
Grimperium v2 is a Python CLI tool for computational chemistry workflow automation that processes molecules through: PubChem → CREST → MOPAC → Database pipeline.

Tech Stack & Architecture
Core Technologies: Python 3.9+ | Typer + Rich + Questionary | Pandas + Pydantic | External: CREST, MOPAC, OpenBabel

Architecture: Service-oriented modular design with clear separation of responsibilities

Pipeline: PubChem API → format conversion → conformational search → quantum calculations → CSV storage

Config: YAML-driven (config.yaml) with validation

Storage: Thread-safe CSV operations with FileLock

CLI: Interactive menu + direct commands

# Multi-Agent Orchestration Framework

## Agent Ecosystem Overview
Grimperium v2 leverages an extensive ecosystem of specialized subagents for optimal workflow orchestration:

**Core Orchestrators**: `task-master`, `studio-producer`, `studio-coach`
**Engineering**: `backend-architect`, `frontend-developer`, `ai-engineer`, `devops-automator`, `mobile-app-builder`
**Quality & Testing**: `test-writer-fixer`, `test-results-analyzer`, `performance-benchmarker`, `api-tester`
**Development Operations**: `git-operationalist`, `rapid-prototyper`, `experiment-tracker`, `workflow-optimizer`
**Project Management**: `sprint-prioritizer`, `project-shipper`, `feedback-synthesizer`, `analytics-reporter`
**Specialized Studio**: `ui-designer`, `ux-researcher`, `whimsy-injector`, `brand-guardian`, `visual-storyteller`
**Support & Compliance**: `support-responder`, `legal-compliance-checker`, `finance-tracker`, `infrastructure-maintainer`
**Strategy & Growth**: `app-store-optimizer`, `tiktok-strategist`, `trend-researcher`

## Code Quality Framework (Multi-Agent Enhanced)

### Before Coding - Intelligence Gathering
- **ASK**: Clarify uncertainties → Use `support-responder` for user requirements analysis
- **PLAN**: Complex tasks → Delegate to `task-master` for decomposition and orchestration
- **COMPARE**: Multiple approaches → Engage `backend-architect` + `studio-coach` for technical review
- **DELEGATE**: Auto-route to specialists:
  - Git/CI/CD issues → `git-operationalist`
  - Sprint planning → `sprint-prioritizer` 
  - Release coordination → `project-shipper`
  - Performance concerns → `performance-benchmarker`
  - UX/UI decisions → `ui-designer` + `ux-researcher`

### During Implementation - Multi-Agent Coordination
- **SIMPLE**: Functional design → `backend-architect` validates service patterns
- **TESTABLE**: Small functions → `test-writer-fixer` ensures coverage automatically
- **CONSISTENT**: Project vocabulary → `brand-guardian` maintains consistency
- **MINIMAL**: Extract judiciously → `workflow-optimizer` identifies refactoring opportunities
- **SPECIALIZED**: Route by domain:
  - Database/API → `backend-architect`
  - Performance → `performance-benchmarker` 
  - CI/CD → `devops-automator`
  - Frontend → `frontend-developer`
  - Mobile → `mobile-app-builder`

### Testing Standards - Automated Quality Assurance
- **UNIT**: `.spec.py` files → `test-writer-fixer` creates and maintains
- **INTEGRATION**: DB tests → `test-results-analyzer` tracks coverage patterns
- **COVERAGE**: Edge cases → `api-tester` validates external integrations
- **MOCKING**: Dependencies → `backend-architect` defines mock strategies
- **PERFORMANCE**: Benchmarks → `performance-benchmarker` establishes baselines

### Post-Implementation - Quality Gates
- **LINT**: Code quality → `git-operationalist` enforces standards in PR reviews
- **SECURITY**: Compliance → `legal-compliance-checker` validates security practices
- **DEPLOY**: Release → `project-shipper` coordinates deployment pipeline
- **MONITOR**: Performance → `infrastructure-maintainer` tracks system health
- **ANALYZE**: Metrics → `analytics-reporter` generates insights

# Enhanced Workflow Commands with Multi-Agent Orchestration

## `qnew` - New Development Session (Multi-Agent Orchestrated)
**Orchestrator**: `task-master` (primary) + `studio-coach` (coordination)
**Workflow**: Context Analysis → Agent Routing → Specialized Implementation → Quality Gates → Integration

**Multi-Agent Flow**:
1. **Context Gathering**: Read `docs/` → `feedback-synthesizer` analyzes requirements
2. **Task Classification**: "Feature/Bug/Refactor?" → `sprint-prioritizer` assesses scope
3. **Agent Orchestration**: `task-master` composes optimal agent team:
   - Complex features → `backend-architect` + `ui-designer`
   - Performance issues → `performance-benchmarker` + `infrastructure-maintainer`
   - CI/CD problems → `git-operationalist` + `devops-automator`
   - Release preparation → `project-shipper` + `test-results-analyzer`
4. **Implementation Coordination**: `studio-producer` manages agent handoffs
5. **Quality Assurance**: Auto-trigger `test-writer-fixer` → `performance-benchmarker`
6. **Git Integration**: `git-operationalist` handles commits, PRs, and CI validation
7. **Release Readiness**: `project-shipper` coordinates deployment strategy
8. **Team Health**: `studio-coach` monitors workload and celebrates wins

**Agent Selection Logic**:
```
if (git_issue or ci_cd_issue): primary = git-operationalist
elif (performance_bottleneck): primary = performance-benchmarker  
elif (complex_architecture): primary = backend-architect
elif (user_experience): primary = ui-designer + ux-researcher
elif (release_coordination): primary = project-shipper
else: primary = task-master  # For general orchestration
```

## `qtest` - Comprehensive Testing Orchestration
**Primary**: `test-writer-fixer` (executor) + `test-results-analyzer` (insights)
**Pipeline**: Test Execution → Coverage Analysis → Performance Validation → Quality Reporting
- `test-writer-fixer`: Automatically runs after code changes, fixes failures
- `api-tester`: Validates PubChem API integration under load
- `performance-benchmarker`: Profiles CREST/MOPAC execution times
- `test-results-analyzer`: Generates coverage trends and quality metrics
- `git-operationalist`: Ensures CI pipeline integration and PR validation

## `qperf` - Multi-Dimensional Performance Analysis  
**Primary**: `performance-benchmarker` (analysis) + `infrastructure-maintainer` (monitoring)
**Pipeline**: Profiling → Bottleneck Identification → Architecture Review → Optimization
- `performance-benchmarker`: Profile computational pipeline bottlenecks
- `backend-architect`: Redesign inefficient service architectures  
- `infrastructure-maintainer`: Monitor system resources and scaling
- `analytics-reporter`: Track performance improvements over time
- `devops-automator`: Implement performance monitoring and alerting

## `qrelease` - End-to-End Release Orchestration
**Primary**: `project-shipper` (coordination) + `git-operationalist` (validation)
**Pipeline**: Planning → Validation → Deployment → Monitoring → Retrospective
- `sprint-prioritizer`: Validate release scope and feature priorities
- `test-results-analyzer`: Ensure comprehensive test coverage and quality gates
- `git-operationalist`: Manage release branches, tags, and CI/CD pipeline
- `project-shipper`: Coordinate deployment strategy and rollback plans
- `infrastructure-maintainer`: Monitor post-deployment system health
- `analytics-reporter`: Track deployment success metrics and user impact
- `studio-coach`: Facilitate release retrospectives and team learnings

## `qgit` - Git & CI/CD Operations (New)
**Primary**: `git-operationalist` (all Git operations)
**Pipeline**: Repository Health → CI/CD Optimization → PR Management → Branch Strategy
- Audit and optimize GitHub workflows and actions
- Review and improve branch protection rules
- Analyze PR patterns and suggest workflow improvements
- Troubleshoot CI/CD failures and performance issues
- Establish Git best practices and commit standards

## `qsprint` - Sprint Planning & Management (New)
**Primary**: `sprint-prioritizer` (planning) + `studio-producer` (execution)
**Pipeline**: Backlog Analysis → Capacity Planning → Task Allocation → Progress Tracking
- Analyze and prioritize feature backlog for maximum impact
- Balance technical debt vs. new features within 6-day cycles
- Optimize team capacity and prevent burnout
- Track sprint velocity and identify bottlenecks
- Coordinate cross-team dependencies and handoffs

Essential Commands
bash
# System check (always run first)
python main.py info

# Single molecule processing
python main.py run-single --name "ethanol"
python main.py run-single --smiles "CCO"

# Batch processing
python main.py run-batch molecules.txt

# Progress analysis
python main.py report
python main.py report --detailed
python main.py report --missing 10

# Interactive mode
python main.py
Project Structure
text
grimperium/
├── grimperium/
│   ├── core/molecule.py          # Pydantic Molecule model
│   ├── services/                 # Business logic
│   │   ├── pubchem_service.py    # PubChem API integration
│   │   ├── conversion_service.py # OpenBabel format conversion
│   │   ├── calculation_service.py # CREST/MOPAC execution
│   │   ├── database_service.py   # Thread-safe CSV operations
│   │   ├── pipeline_orchestrator.py # Workflow coordination
│   │   └── analysis_service.py   # Progress reports
│   ├── utils/config_manager.py   # YAML config handling
│   └── tests/                    # Test suite
├── docs/                         # Project documentation
├── data/                         # CSV databases
├── repository/                   # Calculation workspace
├── logs/                         # Application logs
├── config.yaml                   # Main configuration
└── main.py                       # CLI entry point

# Key Development Patterns
Service Pattern
Inherit from BaseService in utils/base_service.py
Each service has single responsibility
Comprehensive error handling and logging
Use Pydantic for data validation

# Configuration
All external programs configured in config.yaml
Validation on startup via config_manager.py
Never hardcode paths or executable names

# Database Operations
Use database_service.py for all CSV operations
FileLock ensures thread-safe writes
Check for existing entries before processing

# Testing
Mock external programs (CREST, MOPAC, OpenBabel)
Use pytest with intelligent mocks
Test service logic independently
Critical Files & Locations

# Don't Touch:

Files in repository/ directory (calculation workspace)
Database files directly (data/*.csv)
External program paths without config update

# Essential for Development:

logs/grim_details.log - Detailed execution logs
config.yaml - External program configuration
main.py - CLI commands and interactive menu

# Complete Agent Ecosystem & Orchestration Protocols

## Multi-Agent Routing Matrix

### Core Orchestrators (Always Available)
- **task-master**: Multi-agent workflow orchestration, complex task decomposition
- **studio-producer**: Cross-team coordination, resource allocation, process optimization  
- **studio-coach**: Team performance coaching, motivation, conflict resolution

### Engineering Specialists
- **backend-architect**: API design, database architecture, service patterns, system design
- **frontend-developer**: React/Vue/Angular, state management, responsive design
- **ai-engineer**: ML/AI features, molecular property predictions, recommendation systems
- **devops-automator**: CI/CD pipelines, infrastructure as code, deployment automation
- **mobile-app-builder**: iOS/Android development, React Native, mobile optimization
- **rapid-prototyper**: MVP development, proof-of-concepts, trending feature validation

### Quality & Testing Specialists  
- **test-writer-fixer**: Automated test creation, failure resolution, coverage optimization
- **test-results-analyzer**: Test suite health analysis, quality metrics, trend reporting
- **performance-benchmarker**: System profiling, bottleneck identification, optimization
- **api-tester**: External API validation, load testing, integration reliability

### Development Operations
- **git-operationalist**: Git workflows, CI/CD troubleshooting, repository optimization
- **experiment-tracker**: A/B testing, feature flags, experimental rollouts
- **workflow-optimizer**: Process improvement, efficiency analysis, bottleneck removal

### Project & Product Management
- **sprint-prioritizer**: Feature prioritization, capacity planning, technical debt balance
- **project-shipper**: Release coordination, deployment strategies, launch management
- **feedback-synthesizer**: User feedback analysis, feature request prioritization
- **analytics-reporter**: Performance metrics, usage analytics, business intelligence

### Specialized Studio Services
- **ui-designer**: Interface design, component systems, visual aesthetics
- **ux-researcher**: User research, behavior analysis, journey mapping, usability testing
- **whimsy-injector**: Delightful user experiences, personality injection, memorable moments
- **brand-guardian**: Brand consistency, visual identity, style guide management
- **visual-storyteller**: Infographics, presentations, visual communication

### Support & Compliance
- **support-responder**: Customer support automation, documentation, issue analysis
- **legal-compliance-checker**: Regulatory compliance, privacy policies, terms of service
- **finance-tracker**: Budget management, cost optimization, revenue forecasting
- **infrastructure-maintainer**: System monitoring, scaling, reliability, disaster recovery

### Growth & Strategy
- **app-store-optimizer**: App store optimization, keyword research, conversion rates
- **tiktok-strategist**: Viral content strategy, TikTok marketing, creator partnerships
- **trend-researcher**: Market analysis, viral trend identification, opportunity detection
- **tool-evaluator**: Technology assessment, framework evaluation, tool selection

## Advanced Multi-Agent Orchestration Patterns

### Automatic Agent Routing (Smart Delegation)
```yaml
routing_rules:
  git_issues: [git-operationalist, devops-automator]
  performance_problems: [performance-benchmarker, infrastructure-maintainer, backend-architect]
  testing_failures: [test-writer-fixer, test-results-analyzer, api-tester]
  release_planning: [project-shipper, sprint-prioritizer, test-results-analyzer]
  architecture_decisions: [backend-architect, studio-producer, task-master]
  user_experience: [ux-researcher, ui-designer, whimsy-injector]
  team_coordination: [studio-coach, studio-producer, task-master]
```

### Complex Multi-Agent Workflows

#### New Feature Development (Full Pipeline)
**Orchestrator**: `task-master` → **Coordination**: `studio-producer`
1. **Requirements Analysis**: `feedback-synthesizer` + `ux-researcher`
2. **Technical Planning**: `backend-architect` + `sprint-prioritizer`  
3. **Design Phase**: `ui-designer` + `brand-guardian`
4. **Implementation**: `backend-architect` + `frontend-developer`
5. **Testing**: `test-writer-fixer` + `api-tester` + `performance-benchmarker`
6. **Integration**: `git-operationalist` + `devops-automator`
7. **Release**: `project-shipper` + `analytics-reporter`
8. **Post-Launch**: `infrastructure-maintainer` + `feedback-synthesizer`

#### Performance Crisis Resolution
**Emergency Coordinator**: `studio-coach` → **Technical Lead**: `performance-benchmarker`
1. **Immediate Triage**: `infrastructure-maintainer` (system health)
2. **Root Cause Analysis**: `performance-benchmarker` + `analytics-reporter`
3. **Architecture Review**: `backend-architect` + `devops-automator`
4. **Hotfix Development**: `rapid-prototyper` + `test-writer-fixer`
5. **Emergency Deploy**: `git-operationalist` + `project-shipper`
6. **Monitoring**: `infrastructure-maintainer` + `analytics-reporter`
7. **Post-Mortem**: `studio-coach` + `workflow-optimizer`

#### Release Coordination (End-to-End)
**Release Manager**: `project-shipper` → **Quality Gate**: `test-results-analyzer`
1. **Pre-Release**: `sprint-prioritizer` (feature freeze) + `git-operationalist` (branch strategy)
2. **Quality Validation**: `test-writer-fixer` + `performance-benchmarker` + `api-tester`
3. **Security Review**: `legal-compliance-checker` + `infrastructure-maintainer`
4. **Deployment**: `devops-automator` + `infrastructure-maintainer`
5. **Launch Communications**: `visual-storyteller` + `support-responder`
6. **Monitoring**: `analytics-reporter` + `infrastructure-maintainer`
7. **Retrospective**: `studio-coach` + `workflow-optimizer`

#### Git & CI/CD Optimization
**Git Specialist**: `git-operationalist` → **Infrastructure**: `devops-automator`
1. **Repository Audit**: Analyze branch strategies, PR patterns, commit quality
2. **CI/CD Pipeline Review**: Optimize GitHub Actions, reduce build times
3. **Quality Gates**: Implement automated testing, security scans, performance benchmarks
4. **Branch Protection**: Configure proper rules, required reviews, status checks
5. **Workflow Optimization**: Streamline development processes, reduce friction
6. **Team Training**: Document best practices, automate common tasks

### Agent Collaboration Protocols

#### Information Handoffs
- **Structured Data Exchange**: JSON contracts between agents
- **Context Preservation**: Maintain task history and decision rationale
- **Escalation Paths**: Clear protocols for complex issues requiring coordination
- **Quality Gates**: Each agent validates inputs and outputs

#### Conflict Resolution
- **Technical Disagreements**: `backend-architect` + `studio-coach` mediation
- **Resource Conflicts**: `studio-producer` allocation decisions
- **Timeline Issues**: `sprint-prioritizer` + `project-shipper` coordination
- **Quality vs Speed**: `test-results-analyzer` + `performance-benchmarker` balance

## Agent Context Separation & Multi-Agent Coordination

| Context File | Primary Agent | Purpose | Never Used By | Multi-Agent Role |
|--------------|---------------|---------|---------------|------------------|
| CLAUDE.md | Claude Code | Global memory & instructions | AMP (ampcode) | **Orchestrator**: Routes to specialized agents |
| AGENT.md | AMP/ampcode | Project memory & instructions | Claude Code | **Specialist**: Domain-specific execution |

### Multi-Agent Session Management
- **Session Initialization**: `studio-coach` establishes team objectives and performance baselines
- **Agent Handoffs**: `task-master` manages transitions and context preservation
- **Progress Tracking**: `analytics-reporter` monitors multi-agent workflow efficiency
- **Conflict Resolution**: `studio-producer` mediates resource conflicts and priority disputes
- **Quality Assurance**: Each agent validates inputs/outputs before handoff

### Cross-Agent Communication Standards
```json
{
  "agent_handoff": {
    "from_agent": "backend-architect",
    "to_agent": "test-writer-fixer", 
    "context": "Service architecture completed",
    "deliverables": ["API endpoints", "data models", "service patterns"],
    "next_actions": ["Unit tests", "Integration tests", "Performance tests"],
    "quality_gates": ["Code review passed", "Architecture approved"]
  }
}
```

Common Development Tasks (Multi-Agent Enhanced)

### Adding New Services (Orchestrated Pipeline)
**Primary**: `backend-architect` → **Testing**: `test-writer-fixer` → **Integration**: `git-operationalist`
1. **Architecture Design**: `backend-architect` designs service patterns and data models
2. **Implementation**: Follow BaseService inheritance, update pipeline_orchestrator.py
3. **Configuration**: `devops-automator` updates config.yaml with validation
4. **Testing**: `test-writer-fixer` creates comprehensive test coverage
5. **Performance**: `performance-benchmarker` validates computational requirements
6. **Integration**: `git-operationalist` manages PR review and CI/CD integration
7. **Documentation**: `visual-storyteller` creates service documentation

### Debugging Issues (Multi-Dimensional Analysis)
**Triage**: `infrastructure-maintainer` → **Analysis**: `performance-benchmarker` → **Resolution**: Domain specialist
1. **System Health**: Check `python main.py info` → `infrastructure-maintainer` monitors
2. **Log Analysis**: Review `logs/grim_details.log` → `analytics-reporter` identifies patterns
3. **Performance Profiling**: `performance-benchmarker` analyzes bottlenecks
4. **Error Correlation**: `test-results-analyzer` links failures to code changes
5. **Root Cause**: Domain-appropriate agent (backend-architect, api-tester, etc.)
6. **Resolution Tracking**: `experiment-tracker` monitors fix effectiveness

### Configuration Changes (Validated Pipeline)
**Design**: `devops-automator` → **Validation**: `backend-architect` → **Testing**: `test-writer-fixer`
1. **Schema Design**: `devops-automator` plans config.yaml structure changes
2. **Validation Logic**: `backend-architect` updates config_manager.py validation
3. **Testing**: `test-writer-fixer` creates config validation tests
4. **Integration**: Test with `python main.py info`
5. **Deployment**: `git-operationalist` manages configuration rollout
6. **Monitoring**: `infrastructure-maintainer` tracks configuration health

### Git & CI/CD Operations (Specialized Workflows)
**Git Expert**: `git-operationalist` handles all repository and CI/CD operations
1. **Repository Health**: Audit branch strategies, commit quality, PR patterns
2. **CI/CD Optimization**: Improve GitHub Actions performance and reliability
3. **Quality Gates**: Implement automated testing, security scans, performance checks
4. **Branch Management**: Optimize branch protection rules and merge strategies
5. **Workflow Automation**: Streamline common development tasks and processes
6. **Team Practices**: Document and enforce Git best practices across the team

### Release Management (End-to-End Coordination)
**Release Coordinator**: `project-shipper` orchestrates multi-agent release pipeline
1. **Planning**: `sprint-prioritizer` validates scope and priorities
2. **Quality Gates**: `test-results-analyzer` ensures comprehensive coverage
3. **Performance**: `performance-benchmarker` validates system requirements
4. **Security**: `legal-compliance-checker` reviews compliance requirements
5. **Deployment**: `devops-automator` + `infrastructure-maintainer` handle rollout
6. **Monitoring**: `analytics-reporter` tracks post-release metrics
7. **Support**: `support-responder` handles user issues and feedback
8. **Retrospective**: `studio-coach` facilitates team learning and process improvement

Development Context
Project Focus: Academic/research chemistry automation
Data Flow: Molecule identifier → 3D structure → conformational search → quantum calculation → thermodynamic data
External Dependencies: Requires CREST, MOPAC, OpenBabel installed
Database Schema: CSV files with SMILES, coordinates, and calculated properties

## New Orchestration Commands & Auto-Routing

### Smart Agent Routing (Automatic Delegation)
The system automatically routes tasks to optimal agents based on keywords and context:

**Git/Version Control Triggers**: `git`, `commit`, `PR`, `CI/CD`, `pipeline`, `actions`
→ **Auto-route to**: `git-operationalist` (primary) + `devops-automator` (support)

**Performance Issues**: `slow`, `bottleneck`, `optimization`, `memory`, `CPU`, `latency`  
→ **Auto-route to**: `performance-benchmarker` + `infrastructure-maintainer`

**Testing Concerns**: `test`, `coverage`, `failing`, `mock`, `integration`
→ **Auto-route to**: `test-writer-fixer` + `test-results-analyzer`

**Architecture Decisions**: `design`, `architecture`, `API`, `database`, `service`
→ **Auto-route to**: `backend-architect` + `studio-producer`

**Release Activities**: `release`, `deploy`, `launch`, `shipping`, `rollout`
→ **Auto-route to**: `project-shipper` + `git-operationalist`

**Team Coordination**: `sprint`, `planning`, `coordination`, `blocked`, `priorities`
→ **Auto-route to**: `sprint-prioritizer` + `studio-producer` + `studio-coach`

### Enhanced Command Set

#### `qorchestrate` - Dynamic Multi-Agent Composition
**Purpose**: Analyze complex requests and compose optimal agent teams
**Syntax**: `qorchestrate [task_description]`
**Process**:
1. `task-master` analyzes task complexity and requirements
2. `studio-producer` identifies required agent specialties  
3. Auto-compose agent team with defined roles and handoffs
4. `studio-coach` monitors collaboration and resolves conflicts
5. `analytics-reporter` tracks multi-agent workflow efficiency

**Example**:
```bash
qorchestrate "Implement user authentication with OAuth, add comprehensive tests, optimize performance, and prepare for release"

# Auto-composes team:
# - backend-architect (OAuth implementation)
# - test-writer-fixer (comprehensive testing)
# - performance-benchmarker (optimization)
# - git-operationalist (PR management)
# - project-shipper (release preparation)
```

#### `qaudit` - Comprehensive System Analysis
**Purpose**: Multi-dimensional project health assessment
**Agents**: `git-operationalist` + `performance-benchmarker` + `test-results-analyzer` + `infrastructure-maintainer`
**Analysis Dimensions**:
- Git repository health and workflow optimization
- Performance bottlenecks and system resource utilization
- Test coverage gaps and quality metrics trends
- Infrastructure reliability and scaling readiness
- Security compliance and vulnerability assessment

#### `qoptimize` - Intelligent Process Improvement
**Purpose**: Identify and resolve workflow inefficiencies
**Agents**: `workflow-optimizer` + `studio-producer` + `analytics-reporter`
**Optimization Areas**:
- Development workflow bottlenecks
- Agent collaboration patterns
- Resource allocation efficiency
- Communication overhead reduction
- Quality gate streamlining

#### `qescalate` - Smart Issue Escalation
**Purpose**: Route complex problems to appropriate specialist combinations
**Escalation Matrix**:
- **Technical Architecture**: `backend-architect` + `studio-coach`
- **Performance Crisis**: `performance-benchmarker` + `infrastructure-maintainer` + `studio-coach`
- **Release Blockers**: `project-shipper` + `git-operationalist` + `test-results-analyzer`
- **Team Coordination**: `studio-producer` + `studio-coach` + `task-master`
- **Quality Issues**: `test-writer-fixer` + `test-results-analyzer` + `performance-benchmarker`

### Agent Collaboration Standards

#### Multi-Agent Communication Protocol
```json
{
  "workflow_handoff": {
    "timestamp": "2025-01-01T10:00:00Z",
    "from_agent": "backend-architect",
    "to_agent": "test-writer-fixer",
    "task_context": "OAuth service implementation completed",
    "deliverables": {
      "completed": ["AuthService class", "JWT middleware", "OAuth endpoints"],
      "artifacts": ["auth_service.py", "auth_middleware.py", "auth_routes.py"],
      "documentation": ["API endpoints", "Authentication flow"],
      "requirements": ["Test all endpoints", "Mock external OAuth providers"]
    },
    "quality_gates_passed": ["Code review", "Architecture validation", "Security review"],
    "next_actions": ["Unit tests", "Integration tests", "Security tests"],
    "estimated_effort": "4 hours",
    "dependencies": ["Mock OAuth providers", "Test database setup"],
    "success_criteria": ["95% test coverage", "All security tests pass"]
  }
}
```

#### Agent Performance Metrics
- **Task Completion Rate**: Percentage of assigned tasks completed successfully
- **Handoff Quality**: Success rate of agent-to-agent task transitions  
- **Context Preservation**: Accuracy of information transfer between agents
- **Collaboration Efficiency**: Time spent on coordination vs. execution
- **Escalation Frequency**: Rate of issues requiring multi-agent resolution

### Emergency Response Protocols

#### System Crisis Response Team
**Incident Commander**: `studio-coach` (overall coordination)
**Technical Lead**: `infrastructure-maintainer` (system stability)
**Analysis Team**: `performance-benchmarker` + `analytics-reporter` 
**Resolution Team**: Domain-appropriate specialists
**Communication**: `support-responder` (user communication)
**Documentation**: `visual-storyteller` (incident reports)

#### Post-Incident Process
1. **Immediate Response**: `infrastructure-maintainer` stabilizes system
2. **Root Cause Analysis**: `performance-benchmarker` + domain specialists
3. **Resolution Implementation**: Appropriate technical agents
4. **Testing Validation**: `test-writer-fixer` + `api-tester`
5. **Deployment**: `git-operationalist` + `devops-automator`
6. **Monitoring**: `analytics-reporter` + `infrastructure-maintainer`
7. **Post-Mortem**: `studio-coach` + `workflow-optimizer`
8. **Process Improvement**: `studio-producer` implements learnings

This enhanced multi-agent orchestration framework ensures optimal resource allocation, maintains quality standards, and provides comprehensive coverage for all project aspects while preserving the focused, chemistry-specific context of Grimperium v2.

