# PROMPT MESTRE — Mini Projeto: Mega Limpador & Otimizador de PC

> Use este documento como prompt de entrada para uma IA de codificação (Claude Code, Cursor, etc.) ou como especificação de projeto para você mesmo desenvolver. Ele foi escrito para ser auto-suficiente: contém contexto, regras de segurança, arquitetura, requisitos funcionais e não funcionais, e critérios de aceite.

---

## 1. CONTEXTO E PAPEL

Você é um(a) engenheiro(a) de software sênior especializado(a) em ferramentas de sistema (system utilities) para Windows, com foco em segurança, reversibilidade e transparência. Vai projetar e implementar um **mini projeto desktop** chamado **"Mega Limpador & Otimizador"**, cujo objetivo é escanear um computador Windows, identificar itens desnecessários ou obsoletos, e permitir a limpeza/otimização de forma **segura, auditável e nunca destrutiva por padrão**.

**Premissa inegociável:** a ferramenta prioriza NUNCA apagar nada que possa ser importante. Na dúvida, ela reporta e pergunta — não decide sozinha.

---

## 2. OBJETIVO GERAL

Criar uma aplicação que:
1. Faça uma **varredura completa** de armazenamento e memória/desempenho da máquina.
2. Classifique cada item encontrado em níveis de confiança (**Seguro / Moderado / Arriscado**).
3. Gere um **relatório claro** antes de qualquer ação (o que foi encontrado, tamanho, motivo, nível de risco).
4. Só execute limpeza **mediante confirmação explícita** do usuário, item por item ou por categoria.
5. Identifique **pastas órfãs** (resíduos) de softwares que já foram desinstalados, cruzando com o Registro do Windows / lista de programas instalados.
6. Otimize desempenho (inicialização, processos, serviços) sem "achismo" — sem prometer ganhos mágicos de RAM (nada de "boosters" enganosos).
7. Seja **100% reversível** sempre que possível (lixeira/quarentena em vez de exclusão definitiva; backup de metadados; log completo de tudo).

---

## 3. ESCOPO — O QUE A FERRAMENTA FAZ

### 3.1. Varredura de Armazenamento
- Arquivos temporários do sistema (`%TEMP%`, `C:\Windows\Temp`, `Prefetch` antigo).
- Cache de navegadores (Chrome, Edge, Firefox) — apenas cache, nunca senhas/histórico/favoritos.
- Lixeira (itens antigos, com opção de esvaziar).
- Arquivos de dump de erro e logs do Windows (Windows Error Reporting, Minidumps antigos).
- Pontos de restauração do sistema muito antigos (com aviso claro do trade-off).
- Cache de gerenciadores de pacote de desenvolvimento: `npm`/`yarn` cache, `pip` cache, `.gradle`, cache do Docker (imagens/containers *parados* e não usados — sempre listando antes), `node_modules` órfãos (pastas de projetos que não existem mais).
- Miniaturas (thumbnail cache) do Explorer.
- Versões antigas de drivers (Driver Store) não mais usadas pelo hardware atual.
- Arquivo de hibernação (`hiberfil.sys`) — **apenas como sugestão opcional e explicada**, nunca automático.
- Arquivos duplicados (por hash, não só por nome) em pastas indicadas pelo usuário — nunca em `System32` ou pastas de sistema.
- **Pastas órfãs de programas desinstalados** (ver seção 3.3 — tratamento especial).
- Downloads muito antigos e instaladores (`.exe`, `.msi`) já usados, parados há muito tempo na pasta Downloads.

### 3.2. Varredura de Memória / Desempenho
- Itens de inicialização (Startup) com impacto no boot — lista com nome, editor, impacto medido.
- Processos em segundo plano consumindo CPU/RAM de forma anômala (sem matar processos do sistema).
- Serviços do Windows desnecessários/desabilitáveis com segurança (baseado em base de conhecimento, não em "achismo").
- Aplicativos na bandeja do sistema que sobem sozinhos.
- Verificação simples de bloatware (programas pré-instalados de fabricante que raramente são usados) — **apenas relatar, nunca desinstalar sozinho**.
- Análise de fragmentação de disco (se HDD) e sugestão de TRIM (se SSD) — nunca desfragmentar SSD.

### 3.3. Tratamento especial: Pastas órfãs de software desinstalado
Esse é o recurso mais delicado e mais valioso pedido. Regras específicas:

1. Ler a lista de programas **atualmente instalados** via:
   - Registro do Windows: `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall` e a versão `WOW6432Node` (32 bits).
   - `HKCU` equivalente para instalações por usuário.
   - Windows Apps (pacotes UWP/Store), se relevante.
2. Escanear diretórios típicos onde softwares deixam resíduos:
   - `C:\Program Files` e `C:\Program Files (x86)`
   - `C:\ProgramData`
   - `%APPDATA%` e `%LOCALAPPDATA%`
   - Chaves de registro órfãs (sub-chaves de programas que não constam mais na lista de instalados).
3. Para cada pasta/chave encontrada que **não corresponde a nenhum programa instalado atualmente**, gerar uma entrada no relatório com:
   - Nome da pasta/software provável (inferido pelo nome da pasta + metadados de arquivos internos, ex.: `.exe`, ícones, `version info`).
   - Caminho completo.
   - Tamanho total.
   - Data da última modificação (indício de há quanto tempo está "morta").
   - **Nível de confiança de que pode ser apagada**, com justificativa textual (ex.: "Nenhum executável encontrado nesta pasta, apenas arquivos de configuração e logs — provável resíduo seguro" vs. "Contém arquivos `.dll` referenciados por outro programa ainda instalado — risco moderado, não recomendado remover automaticamente").
4. **Nunca apagar automaticamente.** Sempre exibir a lista completa para revisão humana antes de qualquer remoção, mesmo as classificadas como "seguras".
5. Regra de ouro: se a ferramenta não conseguir determinar com razoável certeza que uma pasta é resíduo órfão, ela deve classificar como "Não determinado / requer análise manual" em vez de arriscar um "Seguro" errado.

### 3.4. O que a ferramenta NUNCA faz
- Nunca apaga arquivos pessoais (Documentos, Imagens, Vídeos, Área de Trabalho, Downloads recentes) sem que o usuário aponte explicitamente a pasta.
- Nunca mexe em pastas de sistema críticas (`Windows`, `System32`, `SysWOW64`, `Boot`, `Program Files` de softwares **ativos**).
- Nunca desinstala programas sozinho.
- Nunca altera o Registro sem backup automático prévio (exportação `.reg`) do ramo que será tocado.
- Nunca promete "ganho de X GB de RAM" com números inflados — otimização de memória real é sobre reduzir processos/serviços desnecessários, não "liberar RAM magicamente".
- Nunca executa limpeza em modo silencioso/automático por padrão — sempre exige confirmação (pode ter um modo "avançado" opt-in para usuários experientes, mas nunca como padrão).

---

## 4. FLUXO DE FUNCIONAMENTO (ARQUITETURA)

```
┌─────────────┐     ┌───────────────┐     ┌──────────────┐     ┌───────────────┐
│  Scanner     │ --> │  Classifier   │ --> │  Relatório    │ --> │  Executor      │
│  Modules     │     │  (Safe/       │     │  (dashboard/  │     │  (com          │
│  (storage,   │     │  Moderate/    │     │  CLI/relatório│     │  confirmação   │
│  memory,     │     │  Risky/       │     │  exportável)  │     │  + quarentena) │
│  orphans)    │     │  Unknown)     │     │               │     │                │
└─────────────┘     └───────────────┘     └──────────────┘     └───────────────┘
                                                                        │
                                                                        v
                                                              ┌───────────────────┐
                                                              │  Log + Undo/       │
                                                              │  Restore (quarentena)│
                                                              └───────────────────┘
```

### Módulos sugeridos
1. **`scanner/`** — um submódulo por categoria (`temp_files.py`, `browser_cache.py`, `orphan_folders.py`, `startup_items.py`, `dev_caches.py`, `duplicates.py`, etc.). Cada um retorna uma lista padronizada de "achados" (`Finding`).
2. **`classifier/`** — aplica regras/heurísticas para atribuir nível de confiança e justificativa a cada `Finding`.
3. **`report/`** — gera relatório em tela (CLI/GUI) e exportável (JSON/HTML/PDF) com totais por categoria e por nível de risco.
4. **`executor/`** — recebe a lista de itens aprovados pelo usuário e executa a ação escolhida (mover para quarentena local, esvaziar cache, desabilitar item de startup, etc.), sempre logando.
5. **`quarantine/`** — em vez de apagar direto, move para uma pasta de quarentena com prazo (ex.: 15 dias) antes da exclusão definitiva, permitindo desfazer.
6. **`logger/`** — log estruturado (JSON lines) de tudo: o que foi escaneado, o que foi decidido, o que foi executado, timestamp, hash dos arquivos removidos (para eventual restauração/auditoria).

---

## 5. MODELO DE DADOS (SUGESTÃO)

```python
class Finding:
    id: str                 # UUID
    category: str           # "temp", "browser_cache", "orphan_folder", "startup", "duplicate", ...
    path: str
    size_bytes: int
    last_modified: datetime
    confidence: str          # "safe" | "moderate" | "risky" | "unknown"
    reason: str              # justificativa legível
    related_software: str | None   # inferido, no caso de pastas órfãs
    action_available: list[str]    # ex.: ["quarantine", "delete_permanent", "ignore"]
```

---

## 6. REQUISITOS NÃO FUNCIONAIS

- **Segurança em primeiro lugar:** toda ação destrutiva passa por quarentena reversível por padrão.
- **Transparência:** todo item listado tem explicação do motivo (nunca uma caixa preta "isso é lixo, confie").
- **Performance:** varredura completa de um disco de 500GB deve rodar em tempo razoável (streaming/paralelismo com `concurrent.futures`, evitar carregar tudo em memória).
- **Idempotência:** rodar o scanner duas vezes seguidas não deve gerar resultados inconsistentes.
- **Logs auditáveis:** formato estruturado, com timestamp, fácil de revisar depois.
- **Testabilidade:** lógica de classificação deve ser testável isoladamente (sem precisar mexer no disco real — usar fixtures/mocks de sistema de arquivos).
- **Sem telemetria/rede:** ferramenta 100% local, não envia nada para fora (importante para confiança do usuário).

---

## 7. STACK TECNOLÓGICA SUGERIDA

Dado o perfil do projeto (ferramenta de sistema Windows + já tenho familiaridade com Python/CLI):

- **Linguagem:** Python 3.11+
- **Acesso ao sistema:** `os`, `pathlib`, `shutil`, `psutil` (processos/memória/discos), `winreg` (Registro do Windows), `pywin32` (serviços, itens de startup, WMI se necessário).
- **Hash de duplicados:** `hashlib` (xxhash ou blake3 para performance, se disponível).
- **Interface:**
  - Fase 1 (MVP): **CLI interativa** (ex.: `rich` ou `textual` para uma UI de terminal bonita, com tabelas e barra de progresso).
  - Fase 2 (opcional): **GUI desktop** com `PySide6`/`customtkinter`, ou migrar para uma stack Electron+Node se preferir reaproveitar seu conhecimento full-stack JS.
- **Relatórios:** exportação em JSON (dados brutos) + HTML (relatório visual, pode usar Jinja2) e, opcionalmente, PDF (ReportLab, que você já usou).
- **Testes:** `pytest` + `pyfakefs` (para simular sistema de arquivos sem tocar no disco real nos testes).
- **Empacotamento final:** `PyInstaller` para gerar um `.exe` standalone.

> Observação: como a maior parte das features (Registro, startup, serviços, driver store) é específica de Windows, o projeto deve ser tratado como **Windows-only** — não vale a pena forçar portabilidade cross-platform num mini projeto assim.

---

## 8. ROADMAP DE DESENVOLVIMENTO (FASES)

**Fase 0 — Fundação**
- Estrutura do projeto, modelo `Finding`, logger, sistema de configuração (whitelist de pastas protegidas).

**Fase 1 — Scanners de armazenamento "óbvios" (baixo risco)**
- Temp files, cache de navegador, lixeira, thumbnails, caches de dev (npm/pip/etc).

**Fase 2 — Relatório + Executor com quarentena**
- Dashboard/CLI mostrando achados, confirmação por item/categoria, mover para quarentena, restaurar.

**Fase 3 — Detecção de pastas órfãs (feature-chave)**
- Cruzamento Registro x sistema de arquivos, heurísticas de confiança, geração de relatório detalhado por pasta órfã.

**Fase 4 — Otimização de memória/desempenho**
- Startup items, serviços, processos, sugestões de TRIM/desfragmentação.

**Fase 5 — Duplicados + polimento**
- Busca de duplicados por hash, relatório final consolidado, exportação HTML/PDF, empacotamento `.exe`.

**Fase 6 (opcional) — GUI**
- Migrar a CLI para uma interface gráfica, mantendo toda a lógica de negócio intacta (separação clara entre core e UI).

---

## 9. CRITÉRIOS DE ACEITE

- [ ] Nenhuma ação de exclusão definitiva acontece sem passar antes pela quarentena (exceto se o usuário optar explicitamente por "excluir definitivo" em um item específico).
- [ ] Toda pasta órfã listada tem justificativa textual clara de por que foi classificada como está.
- [ ] Existe uma whitelist codificada de pastas que a ferramenta **nunca** toca, independentemente do que o scanner encontre.
- [ ] O relatório mostra, por categoria: quantidade de itens, espaço total recuperável, e nível de risco predominante.
- [ ] Há um comando/opção de "desfazer última limpeza" que restaura itens da quarentena.
- [ ] Testes cobrem a lógica de classificação (safe/moderate/risky/unknown) com casos de borda.
- [ ] Log completo de cada execução é salvo e pode ser reaberto/auditado depois.

---

## 10. INSTRUÇÃO FINAL PARA A IA DE CODIFICAÇÃO

Ao implementar este projeto:
1. Comece pela **Fase 0 e 1**, entregando um scanner funcional (mesmo que só leia e reporte, sem apagar nada ainda).
2. Sempre que tiver dúvida entre "classificar como seguro" ou "classificar como precisa revisão manual", **opte pela revisão manual**.
3. Escreva o código de forma modular, para que cada scanner possa ser testado isoladamente.
4. Documente, para cada heurística de classificação usada (ex.: "pasta sem `.exe` e sem entradas de registro associadas = provável resíduo seguro"), a lógica exata em comentários/docstrings, para que o usuário possa auditar o critério.
5. Priorize sempre segurança e reversibilidade sobre "agressividade" de limpeza — o objetivo é confiança, não o maior número de GB liberados.
