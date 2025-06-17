
# **Guia de Instalação do Grimperium v2**

Este guia fornece instruções detalhadas para configurar o ambiente completo para o Grimperium a partir do zero em um ambiente WSL (Debian/Ubuntu) no Windows.

## **1. Requisitos Prévios**

*   Windows 10 ou 11 com virtualização de hardware habilitada na BIOS.
*   Acesso à internet para download dos pacotes.
*   Terminal com poderes de administrador (PowerShell) para a instalação inicial do WSL.

## **2. Passo a Passo da Instalação**

### **Passo 1: Instalar o WSL (Windows Subsystem for Linux)**
1.  Abra o **PowerShell** ou o **Prompt de Comando do Windows** como **Administrador**.
2.  Execute o seguinte comando para instalar o WSL com a distribuição Ubuntu (recomendada):
    `wsl --install -d Ubuntu`
    (Se preferir Debian, use: `wsl --install -d Debian`).
3.  Após a instalação, reinicie o computador. O WSL finalizará a configuração na primeira inicialização, pedindo para você criar um nome de usuário e senha para o ambiente Linux.

### **Passo 2: Atualizar o Ambiente WSL e Instalar Dependências Base**
1.  Abra o terminal do seu ambiente Linux (Ubuntu/Debian).
2.  Atualize os repositórios de pacotes e instale as ferramentas de compilação essenciais:
    `sudo apt update && sudo apt upgrade -y`
    `sudo apt install build-essential gfortran -y`

### **Passo 3: Instalar o Miniconda**
1.  No terminal do WSL, baixe o instalador mais recente do Miniconda para Linux:
    `wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh`
2.  Execute o script de instalação:
    `bash Miniconda3-latest-Linux-x86_64.sh`
    Siga as instruções na tela. Aceite os termos da licença e, quando perguntado se deseja inicializar o `conda init`, digite `yes`.
3.  Feche e reabra seu terminal WSL para que as mudanças do conda entrem em vigor.

### **Passo 4: Instalar CREST, OpenBabel e Dependências**
1.  **Crie um ambiente Conda dedicado**:
    `conda create -n grimperium python=3.9 -y`
    `conda activate grimperium`
2.  **Instale os pacotes científicos** do canal conda-forge:
    `conda install -c conda-forge crest xtb openbabel rdkit pubchempy pyyaml pandas typer rich -y`

### **Passo 5: Instalar o MOPAC**
1.  Visite o site oficial [OpenMOPAC](http://openmopac.net/MOPAC2016.html) para obter a versão acadêmica gratuita do MOPAC2016 para Linux.
2.  No terminal do WSL, use `wget` para baixar o arquivo.
    `wget http://openmopac.net/MOPAC2016_for_Linux_64_bit.zip`
3.  Descompacte o arquivo (instale `unzip` se necessário: `sudo apt install unzip`):
    `unzip MOPAC2016_for_Linux_64_bit.zip`
4.  Mova o executável para um local no seu PATH:
    `sudo mv MOPAC2016.exe /usr/local/bin/mopac`
5.  Dê permissão de execução:
    `sudo chmod +x /usr/local/bin/mopac`
6.  Teste a instalação: `mopac`

### **Passo 6: Obter o Código do Grimperium**
1.  Clone o repositório do projeto:
    `git clone <URL_DO_SEU_REPOSITORIO_GIT>`
    `cd grimperium`

**Parabéns! O ambiente está pronto para executar o Grimperium.**
