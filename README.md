# 🛡️ CleanPC — Mega Limpador & Otimizador de PC

> **Utilitário de sistema desktop para Windows**, desenvolvido em Python, focado em limpeza de armazenamento, diagnóstico de desempenho, auditoria transparente e detecção inteligente de pastas órfãs — **com segurança absoluta e reversibilidade total (Quarentena + Desfazer/Undo)**.

---

## 💡 Por que o CleanPC é diferente?

A maioria dos limpadores de PC tradicionais funciona como uma "caixa preta": apagam arquivos sem explicar o motivo e muitas vezes quebram dependências do sistema. 

O **CleanPC** foi projetado sob a premissa de **nunca destruir nada por padrão**:

- 🛡️ **Whitelist Blindada:** Pastas críticas do Windows (`C:\Windows`, `System32`, `SysWOW64`, `Boot`, `Program Files\WindowsApps`, etc.) e pastas pessoais (`Documentos`, `Desktop`, `Imagens`) são 100% protegidas e ignoradas por qualquer ação de limpeza.
- 📦 **Quarentena Reversível (1-Click Undo):** Nenhum arquivo é excluído definitivamente direto do disco. Ao limpar, os itens vão para uma pasta de quarentena segura com manifesto criptográfico. Você pode restaurar qualquer arquivo ou lote inteiro de volta para o caminho original a qualquer momento.
- 📁 **Detecção Inteligente de Pastas Órfãs:** Cruza a lista de programas instalados no Registro do Windows (`HKLM`/`HKCU`/`WOW6432Node`) com as pastas em `Program Files`, `ProgramData`, `%AppData%` e `%LocalAppData%`, identificando resíduos deixados para trás por desinstaladores incompletos.
- 🎯 **Classificação Transparente com Níveis de Confiança:**
  - 🟢 **Seguro (Safe):** Caches puros de renderização de navegadores, arquivos temporários antigos (> 24h), caches de ferramentas dev (`npm`, `pip`, `yarn`, `gradle`), relatórios de erro antigos.
  - 🟡 **Moderado (Moderate):** Lixeira do Windows, temporários recentes, pastas órfãs que contêm apenas configurações/logs.
  - 🔴 **Arriscado (Risky):** Itens com DLLs ou arquivos que possam ser compartilhados por outros aplicativos.
  - 🟣 **Requer Análise Manual (Unknown):** Pastas que contêm executáveis `.exe`, mas não estão registradas no Windows (ex.: programas portáteis).
- 🌐 **Dashboard Visual em HTML:** Gera relatórios interativos com pesquisa em tempo real, badges de risco e detalhamento do motivo de cada item encontrado.
- 🔒 **100% Local & Sem Telemetria:** Não envia dados para a internet nem coleta informações pessoais.

---

## 📋 Pré-requisitos

- **Sistema Operacional:** Windows 10 ou Windows 11 (64-bit)
- **Python:** Versão 3.10 ou superior ([Download Python](https://www.python.org/downloads/))  
  *(Certifique-se de marcar a opção **"Add python.exe to PATH"** durante a instalação)*
- **Git:** ([Download Git](https://git-scm.com/downloads))

---

## 🚀 Guia Rápido de Instalação e Uso (Passo a Passo)

### 1. Clonar o Repositório
Abra o **Terminal / PowerShell** e execute:
```bash
git clone https://github.com/Trindaddy/CleanPC.git
cd CleanPC
```

### 2. (Opcional, mas recomendado) Criar e Ativar um Ambiente Virtual
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(Se o PowerShell bloquear a execução de scripts, execute antes: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar o CleanPC
```bash
python cleanpc.py
```

> 💡 **Dica para Testes Completos:**  
> Para permitir que o CleanPC analise pastas protegidas do sistema (como `C:\Windows\Temp`) ou execute o comando de reotimização de SSD (**TRIM**), abra o PowerShell/Terminal como **Administrador**.

---

## 🖥️ Como Usar a Ferramenta

Ao executar `python cleanpc.py`, você verá o menu interativo no seu terminal:

```text
╔════════════════════════════════════════════════════════════════╗
║   🛡️  MEGA LIMPADOR & OTIMIZADOR DE PC  v1.0.0                 ║
║   Segurança Absoluta • Quarentena Reversível • Sem Telemetria  ║
╚════════════════════════════════════════════════════════════════╝

MENU PRINCIPAL:
 1. 🔍 Varredura Completa do Sistema (Temp, Caches, Órfãos, Dumps, Startup)
 2. ⚡ Varredura Rápida (Apenas Itens Seguros / Baixo Risco)
 3. 📁 Detecção Avançada de Pastas Órfãs (Resíduos de Desinstalação)
 4. 🚀 Otimização de Desempenho, Startup e SSD (TRIM)
 5. 👥 Buscar Arquivos Duplicados por Hash
 6. 📦 Gerenciar Quarentena & Desfazer Limpeza (Undo/Restore)
 7. 📊 Exportar Relatório Atual (HTML / JSON)
 8. 📜 Ver Logs de Auditoria do Sistema
 0. 🚪 Sair
```

### 🔍 Funcionalidades Principais:

1. **Varredura Completa (Opção 1):**  
   Analisa arquivos temporários, caches de navegadores (Chrome, Edge, Firefox, Brave, Opera), lixeira, dumps de falhas, caches de desenvolvimento (`npm`, `pip`, `cargo`, `gradle`), thumbnails e pastas órfãs.
   Ao final, exibe uma tabela detalhada e oferece a opção de enviar os itens aprovados para a **Quarentena**.

2. **Varredura de Pastas Órfãs (Opção 3):**  
   Varre `Program Files`, `ProgramData` e `AppData` procurando pastas deixadas por programas que você já desinstalou. Cada pasta é inspecionada internamente para garantir que não haja DLLs compartilhadas antes de classificar o risco.

3. **Otimização de Desempenho & SSD (Opção 4):**  
   - Lista programas que iniciam automaticamente com o Windows (Startup).
   - Detecta entradas órfãs no registro de inicialização.
   - Identifica se suas unidades são SSDs e permite executar o comando nativo **TRIM** (`Optimize-Volume`) para manter a velocidade de gravação das células flash.

4. **Gerenciar Quarentena & Desfazer Limpeza (Opção 6):**  
   Caso você queira reverter uma limpeza feita anteriormente, basta acessar esta opção, digitar o ID do Lote e todos os arquivos serão restaurados instantaneamente para seus locais originais de onde saíram.

5. **Exportar Relatório Visual HTML (Opção 7):**  
   Gera um arquivo `.html` interativo em modo escuro com pesquisa em tempo real, cards de métricas e filtros por nível de risco para você analisar no navegador.

---

## ⚡ Comandos Rápidos via Terminal (Linha de Comando)

Você também pode rodar o CleanPC diretamente sem navegar pelo menu interativo:

```bash
# Executar varredura completa e gerar dashboard HTML
python cleanpc.py --scan --report html

# Executar varredura rápida apenas com itens 100% seguros (Safe)
python cleanpc.py --safe-only

# Executar varredura focada apenas em pastas órfãs
python cleanpc.py --orphans-only

# Listar todos os lotes que estão na quarentena
python cleanpc.py --quarantine-list

# Restaurar um lote da quarentena usando o ID do lote
python cleanpc.py --restore 20260831_113000_a1b2c3
```

---

## 🧪 Como Rodar os Testes Automatizados

O projeto conta com uma suíte de testes unitários com `pytest` testando a Whitelist, classificação de risco, integridade dos modelos e o ciclo de Quarentena + Restauração:

```bash
python -m pytest tests/ -v
```

---

## 🏗️ Estrutura do Código

```text
CleanPC/
├── cleanpc.py                    # Script executável e entrada principal da CLI
├── requirements.txt              # Dependências Python (rich, psutil, pytest)
├── cleanpc_core/                 # Núcleo de segurança e regras de negócio
│   ├── models.py                 # Dataclasses (Finding, RiskLevel, QuarantineRecord)
│   ├── config.py                 # Diretórios padrão de quarentena, logs e relatórios
│   ├── whitelist.py              # Proteção inegociável de arquivos e pastas de sistema
│   ├── quarantine.py             # Gerenciamento de quarentena e manifesto de restauração (Undo)
│   ├── classifier.py             # Heurísticas de risco e justificativas auditáveis
│   └── logger.py                 # Logger estruturado em JSON Lines (cleanpc_activity.jsonl)
├── cleanpc_scanners/             # Módulos de escaneamento modular
│   ├── temp_files.py             # Temporários do Windows e Usuário
│   ├── browser_cache.py          # Caches de navegadores (apenas cache, sem senhas/histórico)
│   ├── recycle_bin.py            # Lixeira em todos os discos
│   ├── error_dumps.py            # Crash dumps, Minidumps e WER
│   ├── dev_caches.py             # Caches de desenvolvimento (npm, pip, yarn, gradle, etc.)
│   ├── thumbnails.py             # Cache de miniaturas do Explorer
│   ├── orphan_folders.py         # Cruzamento Registro x Sistema de Arquivos
│   ├── duplicates.py             # Identificação de duplicados por hash streaming
│   ├── system_optimizations.py   # Análise de Startup, processos e SSD/TRIM
│   └── manager.py                # Coordenador central de execução de varreduras
├── cleanpc_executors/            # Executores de ações
│   ├── cleaner.py                # Envio seguro para quarentena
│   └── optimizer.py              # Gerenciador de inicialização e comando TRIM
├── cleanpc_reports/              # Exportação de relatórios
│   ├── exporter_html.py          # Dashboard interativo HTML/JS
│   └── exporter_json.py          # Exportação em JSON estruturado
├── cleanpc_ui/                   # Camada de apresentação visual no terminal
│   └── cli.py                    # Menu, tabelas e barras de progresso com Rich
└── tests/                        # Testes unitários automatizados
```

---

## 🤝 Feedback e Contribuições

Este projeto foi construído para ser seguro, aberto e auditável. Se encontrar algum comportamento inesperado, sugestão de novo scanner ou falso-positivo, sinta-se à vontade para abrir uma *Issue* ou enviar um *Pull Request* no repositório!
