# 🛡️ CleanPC — Mega Limpador & Otimizador de PC para Windows

> **Utilitário desktop moderno para Windows** com **Interface Gráfica (GUI)** e **CLI**, focado em limpeza profunda, diagnóstico de desempenho, auditoria transparente e detecção inteligente de pastas órfãs — **com segurança absoluta e reversibilidade total (Quarentena + Desfazer/Undo com 1 clique)**.

---

## ⚡ Como Baixar e Usar (Para Usuários & Amigos)

### 🥇 Opção 1: Baixar o Executável Direto (.exe) — **Não precisa de Python!**
Se você quer apenas usar o programa sem instalar nada no computador:
1. Acesse a página de **[Releases no GitHub](https://github.com/Trindaddy/CleanPC/releases)**.
2. Baixe o arquivo **`CleanPC.exe`**.
3. Dê **dois cliques** no `CleanPC.exe` para abrir a Interface Gráfica moderna!

*(Dica: Para permitir limpeza completa de logs do Windows e reotimização de SSD via TRIM, execute como Administrador clicando com o botão direito -> "Executar como Administrador")*.

---

### 🥈 Opção 2: Executar pelo Código-Fonte (Para Desenvolvedores)

Se você clonou o repositório ou quer rodar via código:

#### Método Rápido (1 Clique):
Basta dar dois cliques no arquivo **`iniciar.bat`**. Ele cria o ambiente virtual, instala as dependências e abre o CleanPC automaticamente!

#### Método Manual:
```bash
# 1. Clonar o repositório
git clone https://github.com/Trindaddy/CleanPC.git
cd CleanPC

# 2. Criar e ativar ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Iniciar a Interface Gráfica (GUI)
python cleanpc.py

# 5. Ou iniciar no modo Terminal / CLI interativo
python cleanpc.py --cli
```

---

## 💡 Por que o CleanPC é diferente dos outros limpadores?

A maioria dos utilitários de PC tradicionais funciona como uma "caixa preta": apagam arquivos sem explicar o motivo e muitas vezes quebram o sistema ou apagam logins.

O **CleanPC** foi projetado com premissas inegociáveis de segurança:

- 🛡️ **Whitelist Blindada:** Pastas essenciais do Windows (`C:\Windows`, `System32`, `SysWOW64`, `Boot`, `Program Files\WindowsApps`, etc.) e pastas pessoais (`Documentos`, `Desktop`, `Imagens`) são 100% protegidas e ignoradas por qualquer ação de limpeza.
- 📦 **Quarentena Reversível (1-Click Undo):** Nenhum arquivo é excluído definitivamente direto do disco. Ao limpar, os itens vão para uma pasta de quarentena segura com manifesto criptográfico. Você pode restaurar qualquer arquivo ou lote inteiro de volta para o caminho original a qualquer momento.
- 📁 **Detecção Inteligente de Pastas Órfãs:** Cruza a lista de programas instalados no Registro do Windows (`HKLM`/`HKCU`/`WOW6432Node`) com as pastas em `Program Files`, `ProgramData`, `%AppData%` e `%LocalAppData%`, identificando resíduos deixados para trás por desinstaladores incompletos.
- 🎮 **Recuperação de Espaço em Shaders de GPU (5 GB a 30 GB+):** Limpeza segura de shaders pré-compilados obsoletos de placas de vídeo (NVIDIA `DXCache`/`GLCache`, AMD Radeon `DxCache`, DirectX `D3DSCache` e Intel).
- 💬 **Caches de Aplicativos Pesados:** Caches puros de renderização de Discord, Spotify, Steam, Epic Games Launcher e Telegram (nunca toca em senhas, mensagens ou logins).
- 📄 **Logs CBS de Atualizações do Windows:** Remove arquivos de log persistidos e compactados (`CbsPersist_*.cab`) que ficam presos no disco após atualizações do Windows Update.
- 🔒 **Detecção de Processos Abertos (File Locks):** Identifica se navegadores ou apps estão abertos durante a limpeza e oferece a opção de fechá-los suavemente para liberar 100% do cache.
- 🌐 **Dashboard Visual em HTML:** Exporta relatórios interativos com pesquisa em tempo real, cards de métricas e filtros por nível de risco.
- 🔒 **100% Local & Sem Telemetria:** Não envia dados para a internet nem coleta dados pessoais.

---

## 🎨 Interface Gráfica Moderna (GUI Desktop)

O CleanPC possui uma interface nativa com suporte a **Dark Theme**:

* **Seleção Modular:** Escolha exatamente quais categorias escanear por checkboxes.
* **Cards de Métricas:** Visualize o espaço total recuperável dividido por nível de risco:
  * 🟢 **Seguro (Safe):** Caches de navegadores, shaders de GPU, temporários antigos, caches de desenvolvimento.
  * 🟡 **Moderado (Moderate):** Lixeira do Windows, temporários recentes, pastas órfãs com configurações.
  * 🔴 **Arriscado (Risky):** Pastas que contêm DLLs ou dependências compartilhadas.
  * 🟣 **Requer Análise (Unknown):** Executáveis portáteis não registrados.
* **Barra de Progresso:** Status em tempo real durante a varredura e limpeza.
* **Gerenciador de Quarentena Integrado:** Restaure limpezas anteriores com apenas 1 clique.

---

## 💻 Modos de Linha de Comando (CLI / Terminal)

Você também pode utilizar o CleanPC via terminal ou automatizar em scripts:

```bash
# Abrir menu interativo de terminal
python cleanpc.py --cli

# Varredura completa imediata e exportação de dashboard HTML
python cleanpc.py --scan --report html

# Varredura rápida apenas com itens 100% seguros (Safe)
python cleanpc.py --safe-only

# Varredura focada exclusivamente em pastas órfãs de desinstalação
python cleanpc.py --orphans-only

# Listar lotes em quarentena
python cleanpc.py --quarantine-list

# Restaurar um lote da quarentena usando o ID
python cleanpc.py --restore <ID_DO_LOTE>
```

---

## 🔨 Como Compilar o Executável Standalone (.exe)

Para compilar um novo `CleanPC.exe` portátil localmente:
```bash
python build_exe.py
# Ou execute o arquivo build.bat com 2 cliques
```
O executável standalone será gerado em `dist/CleanPC.exe`.

---

## 🧪 Suíte de Testes Automatizados

O CleanPC inclui 24 testes unitários automatizados cobrindo todos os módulos:
```bash
python -m pytest tests/ -v
```

---

## 🤝 Licença e Contribuições

Desenvolvido para ser uma ferramenta transparente, segura e auditável para a comunidade Windows. Sinta-se à vontade para abrir uma *Issue* ou enviar um *Pull Request* no repositório!
