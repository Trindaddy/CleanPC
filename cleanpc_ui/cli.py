"""
Interface de Linha de Comando (CLI) Aprimorada, Interativa e Visual com Rich.
Suporta diagnóstico ao vivo de hardware, varreduras completas no PC e limpeza de Smartphones via USB.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.columns import Columns

from cleanpc_core.config import APP_NAME, APP_VERSION
from cleanpc_core.logger import app_logger
from cleanpc_core.models import Finding, RiskLevel, ScanCategory
from cleanpc_core.quarantine import quarantine_manager
from cleanpc_executors.cleaner import SafeCleanerExecutor
from cleanpc_executors.optimizer import OptimizerExecutor
from cleanpc_executors.process_lock import ProcessLockManager
from cleanpc_executors.system_restore import SystemRestoreManager
from cleanpc_mobile.detector import MobileDeviceDetector, ConnectedMobileDevice
from cleanpc_mobile.adb_scanner import AdbDeviceScanner
from cleanpc_mobile.mtp_scanner import MtpDeviceScanner
from cleanpc_mobile.mobile_cleaner import SafeMobileCleaner
from cleanpc_reports.exporter_html import HtmlReportExporter, format_bytes
from cleanpc_reports.exporter_json import JsonReportExporter
from cleanpc_scanners.manager import ScannerManager, ScanSummary


def generate_bar(pct: float, length: int = 15) -> str:
    """Gera uma barra gráfica de progresso ASCII colorida."""
    filled = int((pct / 100.0) * length)
    bar = "█" * filled + "░" * (length - filled)
    if pct > 85:
        return f"[bold red]{bar}[/] {pct:.0f}%"
    elif pct > 65:
        return f"[bold yellow]{bar}[/] {pct:.0f}%"
    return f"[bold green]{bar}[/] {pct:.0f}%"


class CleanPcCLI:
    def __init__(self):
        self.console = Console(highlight=False, soft_wrap=True)
        self.scanner_manager = ScannerManager()
        self.cleaner = SafeCleanerExecutor()
        self.optimizer = OptimizerExecutor()
        self.last_findings: List[Finding] = []
        self.last_summary: Optional[ScanSummary] = None

    def print_banner_and_dashboard(self):
        # 1. Coleta estatísticas em tempo real
        mem = psutil.virtual_memory()
        mem_used_gb = round(mem.used / (1024**3), 1)
        mem_total_gb = round(mem.total / (1024**3), 1)
        mem_bar = generate_bar(mem.percent)

        disk_c = psutil.disk_usage("C:\\")
        disk_used_gb = round(disk_c.used / (1024**3), 1)
        disk_total_gb = round(disk_c.total / (1024**3), 1)
        disk_free_gb = round(disk_c.free / (1024**3), 1)
        disk_bar = generate_bar(disk_c.percent)

        # 2. Detecta celular conectado
        connected_mobiles = MobileDeviceDetector.detect_all_devices()
        mobile_status = f"[bold green]📱 {connected_mobiles[0].name} ({connected_mobiles[0].mode})[/]" if connected_mobiles else "[dim]📱 Nenhum celular USB conectado[/]"

        header_text = f"""[bold cyan]╔══════════════════════════════════════════════════════════════════════════════════╗[/]
[bold cyan]║[/]    [bold white]🛡️  CLEANPC — MEGA LIMPADOR & OTIMIZADOR DE PC E SMARTPHONE[/] [dim]v{APP_VERSION}[/]     [bold cyan]║[/]
[bold cyan]║[/]    [dim]Segurança Inegociável • Quarentena Reversível (Undo) • 100% Local & Seguro[/]    [bold cyan]║[/]
[bold cyan]╚══════════════════════════════════════════════════════════════════════════════════╝[/]"""
        self.console.print(header_text)

        dash_content = f"""[bold white]🖥️ SISTEMA:[/] Windows ({os.environ.get('PROCESSOR_ARCHITECTURE', '64-bit')})  |  [bold white]RAM:[/] {mem_used_gb}/{mem_total_gb} GB {mem_bar}
[bold white]💽 DISCO C:[/] {disk_free_gb} GB Livres de {disk_total_gb} GB {disk_bar}
[bold white]USB STATUS:[/] {mobile_status}"""
        
        self.console.print(Panel(dash_content, title="[bold cyan]Painel de Diagnóstico do Sistema[/]", border_style="cyan"))

    def display_main_menu(self):
        self.console.print("\n[bold yellow]MENU PRINCIPAL DE AÇÕES:[/]")
        self.console.print(" [bold green]1[/]. 🔍 [bold white]Varredura Completa do PC[/] (Temp, Caches, Shaders GPU, Apps, Órfãos, Dumps)")
        self.console.print(" [bold green]2[/]. 📱 [bold cyan]Varredura & Limpeza de Smartphone Conectado (USB / MTP / ADB)[/]")
        self.console.print(" [bold green]3[/]. ⚡ [bold white]Varredura Rápida do PC[/] (Apenas Baixo Risco / 100% Safe)")
        self.console.print(" [bold green]4[/]. 📁 [bold white]Pastas Órfãs de Softwares Desinstalados (PC)[/]")
        self.console.print(" [bold green]5[/]. 🎮 [bold white]Caches Pesados (Shaders GPU, Discord, Spotify, Steam, Logs CBS)[/]")
        self.console.print(" [bold green]6[/]. 🚀 [bold white]Otimizações de Desempenho, Startup e SSD (TRIM)[/]")
        self.console.print(" [bold green]7[/]. 👥 [bold white]Buscar Arquivos Duplicados por Hash[/]")
        self.console.print(" [bold green]8[/]. 📦 [bold white]Gerenciar Quarentena & Desfazer Limpeza (Undo/Restore)[/]")
        self.console.print(" [bold green]9[/]. 📊 [bold white]Exportar Relatório Visual (HTML / JSON)[/]")
        self.console.print(" [bold red]0[/]. 🚪 [bold dim]Sair[/]")

    def run_interactive(self):
        while True:
            self.console.clear()
            self.print_banner_and_dashboard()
            self.display_main_menu()
            
            choice = Prompt.ask("\n[bold cyan]Escolha uma opção[/]", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], default="1")

            if choice == "0":
                self.console.print("\n[bold cyan]Encerrando o CleanPC. Até logo![/]\n")
                break
            elif choice == "1":
                self.handle_full_scan()
            elif choice == "2":
                self.handle_mobile_cleaning()
            elif choice == "3":
                self.handle_safe_scan()
            elif choice == "4":
                self.handle_orphan_scan()
            elif choice == "5":
                self.handle_heavy_caches_scan()
            elif choice == "6":
                self.handle_optimizations()
            elif choice == "7":
                self.handle_duplicates_scan()
            elif choice == "8":
                self.handle_quarantine_management()
            elif choice == "9":
                self.handle_export_report()

            self.console.print("\n[dim]Pressione ENTER para voltar ao menu principal...[/]")
            input()

    def _execute_scan_with_progress(self, categories: Optional[List[ScanCategory]] = None):
        findings: List[Finding] = []
        summary: Optional[ScanSummary] = None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Iniciando varredura...", total=100)

            def update_cb(msg: str, current: int, total: int):
                pct = int((current / max(total, 1)) * 100)
                progress.update(task, description=f"[cyan]{msg}", completed=pct)

            findings, summary = self.scanner_manager.run_all(
                categories=categories,
                progress_callback=update_cb
            )
            progress.update(task, description="[bold green]Varredura concluída!", completed=100)

        self.last_findings = findings
        self.last_summary = summary
        self.display_findings_table(findings, summary)

    def display_findings_table(self, findings: List[Finding], summary: ScanSummary):
        if not findings:
            self.console.print("\n[bold green]✨ Nenhum item desnecessário ou resíduo encontrado![/]")
            return

        summary_panel = f"""[bold white]Total de Itens:[/] {summary.total_findings} | [bold white]Espaço Recuperável:[/] [bold cyan]{format_bytes(summary.total_size_bytes)}[/] | [bold white]Duração:[/] {summary.duration_seconds}s
[bold green]● Seguro (Safe):[/] {format_bytes(summary.safe_size_bytes)} ({len(summary.findings_by_risk.get('safe', []))} itens)
[bold yellow]● Moderado:[/] {format_bytes(summary.moderate_size_bytes)} ({len(summary.findings_by_risk.get('moderate', []))} itens)
[bold red]● Arriscado:[/] {format_bytes(summary.risky_size_bytes)} ({len(summary.findings_by_risk.get('risky', []))} itens)
[bold magenta]● Requer Análise:[/] {format_bytes(summary.unknown_size_bytes)} ({len(summary.findings_by_risk.get('unknown', []))} itens)"""
        
        self.console.print(Panel(summary_panel, title="[bold cyan]Sumário da Varredura[/]", border_style="cyan"))

        table = Table(title="Itens Identificados na Varredura", expand=True, show_lines=True)
        table.add_column("Risco", style="bold", width=14)
        table.add_column("Categoria", width=24)
        table.add_column("Caminho / Item", style="dim", ratio=3)
        table.add_column("Tamanho", justify="right", width=12)
        table.add_column("Justificativa", ratio=3)

        displayed_items = findings[:30]
        for f in displayed_items:
            risk_badge = f"[{f.confidence.color}]{f.confidence.display_name}[/]"
            table.add_row(
                risk_badge,
                f.category.display_name,
                f.path,
                format_bytes(f.size_bytes),
                f.reason
            )

        self.console.print(table)

        if len(findings) > 30:
            self.console.print(f"[dim]... e mais {len(findings) - 30} itens. Use a opção 9 para exportar o relatório HTML interativo completo.[/]")

        self.prompt_cleaning_action(findings)

    def prompt_cleaning_action(self, findings: List[Finding]):
        cleanable = [f for f in findings if f.category not in (ScanCategory.STARTUP_ITEMS, ScanCategory.SYSTEM_OPTIMIZATIONS)]
        if not cleanable:
            return

        self.console.print("\n[bold yellow]Ações de Limpeza Segura (com Quarentena Reversível):[/]")
        self.console.print(" [bold green]1[/]. 🛡️  [bold green]Mover apenas itens SEGUROS para Quarentena (Recomendado)[/]")
        self.console.print(" [bold yellow]2[/]. ⚙️  [bold yellow]Mover itens SEGUROS e MODERADOS para Quarentena[/]")
        self.console.print(" [bold red]3[/]. ⚠️  [bold red]Mover TODOS os itens para Quarentena (Requer Confirmação)[/]")
        self.console.print(" [bold dim]0[/]. 🔙 [bold dim]Não limpar nada / Voltar[/]")

        act = Prompt.ask("\n[bold cyan]Deseja executar a limpeza?[/]", choices=["0", "1", "2", "3"], default="0")

        to_clean: List[Finding] = []
        if act == "1":
            to_clean = [f for f in cleanable if f.confidence == RiskLevel.SAFE]
        elif act == "2":
            to_clean = [f for f in cleanable if f.confidence in (RiskLevel.SAFE, RiskLevel.MODERATE)]
        elif act == "3":
            if Confirm.ask("[bold red]ATENÇÃO: Você optou por incluir itens marcados para Análise Manual. Deseja prosseguir?[/]", default=False):
                to_clean = cleanable
            else:
                self.console.print("[yellow]Operação cancelada.[/]")
                return
        else:
            return

        if not to_clean:
            self.console.print("[yellow]Nenhum item selecionado para limpeza.[/]")
            return

        # 1. Verifica se há processos abertos travando arquivos
        blocking_apps = ProcessLockManager.get_running_blocking_apps(to_clean)
        if blocking_apps:
            app_names = [name for name, _ in blocking_apps]
            self.console.print(f"\n[bold yellow]⚠️  Os seguintes aplicativos estão abertos e podem travar a limpeza:[/] [bold white]{', '.join(app_names)}[/]")
            if Confirm.ask("[bold cyan]Deseja que o CleanPC solicite o encerramento suave desses apps para liberar 100% do cache?[/]", default=True):
                ProcessLockManager.terminate_apps(app_names)

        # 2. Pergunta sobre Ponto de Restauração
        if Confirm.ask("\n[bold cyan]Deseja criar um Ponto de Restauração do Windows antes de prosseguir?[/]", default=False):
            ok, msg = SystemRestoreManager.create_restore_point()
            if ok:
                self.console.print(f"[bold green]✅ {msg}[/]")
            else:
                self.console.print(f"[yellow]{msg}[/]")

        total_bytes = sum(f.size_bytes for f in to_clean)
        self.console.print(f"\n[bold green]Movendo {len(to_clean)} itens ({format_bytes(total_bytes)}) para a Quarentena reversível...[/]")

        with Progress(console=self.console) as progress:
            task = progress.add_task("[green]Enviando para quarentena...", total=len(to_clean))
            def cb(msg, curr, tot):
                progress.update(task, description=f"[green]{msg}", completed=curr)
            report = self.cleaner.execute_cleaning(to_clean, progress_callback=cb)
            progress.update(task, completed=len(to_clean))

        self.console.print(Panel(
            f"""[bold green]✅ Limpeza Concluída com Sucesso![/]
• Itens em Quarentena: [bold white]{report.successful_items}[/]
• Espaço Total Liberado: [bold cyan]{format_bytes(report.total_freed_bytes)}[/]
• ID do Lote de Quarentena: [bold white]{report.batch_id}[/]
• Itens Bloqueados/Ignorados: {report.failed_items + report.skipped_items}

[dim]Você pode restaurar esses arquivos a qualquer momento na opção 'Gerenciar Quarentena'.[/]""",
            title="[bold green]Resultado da Limpeza[/]",
            border_style="green"
        ))

    def handle_mobile_cleaning(self):
        self.console.print("\n[bold cyan]📱 MÓDULO DE VARREDURA E LIMPEZA DE SMARTPHONE / CELULAR[/]")
        self.console.print("[dim]Conecte seu celular no computador via cabo USB.[/]\n")

        with Progress(console=self.console) as progress:
            task = progress.add_task("[cyan]Detectando smartphones conectados via USB...", total=100)
            devices = MobileDeviceDetector.detect_all_devices()
            progress.update(task, completed=100)

        if not devices:
            self.console.print("[yellow]⚠️  Nenhum smartphone detectado via USB no momento.[/]")
            self.console.print("\n[bold white]Como conectar seu celular com sucesso:[/]")
            self.console.print(" 1. Conecte o cabo USB no PC e no celular.")
            self.console.print(" 2. Na tela do celular, selecione a opção [bold cyan]'Transferência de Arquivos / MTP'[/].")
            self.console.print(" 3. [bold dim](Opcional para limpeza avançada)[/] Ative a 'Depuração USB' nas Opções do Desenvolvedor do Android.")
            return

        self.console.print("\n[bold green]Smartphones Detectados:[/]")
        for idx, dev in enumerate(devices):
            self.console.print(f" [bold white][{idx + 1}][/] 📱 [bold cyan]{dev.name}[/] — [dim]{dev.description} (Modo: {dev.mode})[/]")

        choice_idx = 0
        if len(devices) > 1:
            dev_choice = Prompt.ask("\nSelecione o aparelho", choices=[str(i + 1) for i in range(len(devices))], default="1")
            choice_idx = int(dev_choice) - 1

        target_device = devices[choice_idx]
        self.console.print(f"\n[bold green]Iniciando varredura no aparelho:[/] [bold white]{target_device.name}[/]")

        # Executa scanner apropriado
        findings: List[Finding] = []
        if target_device.mode == "ADB":
            scanner = AdbDeviceScanner(target_device)
            with Progress(console=self.console) as progress:
                task = progress.add_task("[cyan]Varrendo armazenamento do Android via ADB...", total=100)
                def cb(msg, curr, tot):
                    pct = int((curr / max(tot, 1)) * 100)
                    progress.update(task, description=f"[cyan]{msg}", completed=pct)
                findings = scanner.scan(progress_callback=cb)
                progress.update(task, completed=100)
        else:
            scanner = MtpDeviceScanner(target_device)
            findings = scanner.scan()

        if not findings:
            self.console.print("\n[bold green]✨ Seu smartphone está limpo! Nenhuma miniatura órfã ou lixo temporário detectado.[/]")
            return

        total_mobile_bytes = sum(f.size_bytes for f in findings)
        self.console.print(f"\n[bold cyan]Foram identificados {len(findings)} itens ocupando {format_bytes(total_mobile_bytes)} no smartphone:[/\n")

        table = Table(title=f"Achados no Celular — {target_device.name}", expand=True)
        table.add_column("Categoria", style="bold cyan", width=26)
        table.add_column("Caminho no Aparelho", style="dim", ratio=3)
        table.add_column("Tamanho", justify="right", width=12)
        table.add_column("Motivo", ratio=3)

        for f in findings:
            table.add_row(f.category.display_name, f.path, format_bytes(f.size_bytes), f.reason)

        self.console.print(table)

        if Confirm.ask(f"\n[bold cyan]Deseja limpar esses itens do celular com backup prévio na Quarentena do PC?[/]", default=True):
            cleaner = SafeMobileCleaner(target_device)
            with Progress(console=self.console) as progress:
                task = progress.add_task("[green]Fazendo backup e limpando celular...", total=len(findings))
                def cb(msg, curr, tot):
                    progress.update(task, description=f"[green]{msg}", completed=curr)
                report = cleaner.execute_mobile_cleaning(findings, progress_callback=cb)
                progress.update(task, completed=len(findings))

            self.console.print(Panel(
                f"""[bold green]✅ Limpeza do Smartphone Concluída![/]
• Aparelho: [bold white]{target_device.name}[/]
• Itens Limpos: [bold white]{report.successful_items}[/]
• Espaço Liberado no Celular: [bold cyan]{format_bytes(report.total_freed_bytes)}[/]
• Backup de Segurança salvo no PC em: [dim]%LOCALAPPDATA%\\MegaLimpador\\quarantine_mobile\\{report.batch_id}[/]""",
                title="[bold green]Resultado da Limpeza Mobile[/]",
                border_style="green"
            ))

    def handle_full_scan(self):
        self._execute_scan_with_progress()

    def handle_safe_scan(self):
        safe_cats = [
            ScanCategory.TEMP_FILES,
            ScanCategory.BROWSER_CACHE,
            ScanCategory.GPU_SHADERS,
            ScanCategory.APP_CACHES,
            ScanCategory.WINDOWS_LOGS,
            ScanCategory.ERROR_DUMPS,
            ScanCategory.DEV_CACHES,
            ScanCategory.THUMBNAILS
        ]
        self._execute_scan_with_progress(categories=safe_cats)

    def handle_orphan_scan(self):
        self._execute_scan_with_progress(categories=[ScanCategory.ORPHAN_FOLDERS])

    def handle_heavy_caches_scan(self):
        heavy_cats = [
            ScanCategory.GPU_SHADERS,
            ScanCategory.APP_CACHES,
            ScanCategory.WINDOWS_LOGS,
            ScanCategory.BROWSER_CACHE
        ]
        self._execute_scan_with_progress(categories=heavy_cats)

    def handle_duplicates_scan(self):
        from cleanpc_scanners.duplicates import DuplicateFilesScanner
        self.console.print("\n[bold cyan]Buscando arquivos duplicados por hash nas pastas do usuário...[/]")
        scanner = DuplicateFilesScanner()
        findings = []
        with Progress(console=self.console) as progress:
            task = progress.add_task("[cyan]Comparando hashes...", total=100)
            def cb(msg, curr, tot):
                pct = int((curr / max(tot, 1)) * 100)
                progress.update(task, description=f"[cyan]{msg}", completed=pct)
            findings = scanner.scan(progress_callback=cb)
            progress.update(task, completed=100)

        summary = self.scanner_manager._build_summary(findings, 0.0)
        self.last_findings = findings
        self.last_summary = summary
        self.display_findings_table(findings, summary)

    def handle_optimizations(self):
        self.console.print("\n[bold cyan]Analisando Otimizações de Inicialização e Hardware...[/]")
        from cleanpc_scanners.system_optimizations import SystemOptimizationsScanner
        scanner = SystemOptimizationsScanner()
        findings = scanner.scan()

        table = Table(title="Otimizações e Itens de Inicialização (Startup)", expand=True)
        table.add_column("Tipo / Item", style="bold cyan")
        table.add_column("Status / Recomendação")
        table.add_column("Ação Disponível")

        for f in findings:
            table.add_row(f.path, f.reason, ", ".join(f.action_available))

        self.console.print(table)

        trim_items = [f for f in findings if f.metadata.get("optimization_type") == "TRIM"]
        if trim_items:
            if Confirm.ask("\n[bold cyan]Deseja executar o comando TRIM para reotimizar as unidades SSD?[/]", default=False):
                ok, msg = self.optimizer.execute_trim_optimization("C")
                if ok:
                    self.console.print(f"[bold green]✅ {msg}[/]")
                else:
                    self.console.print(f"[bold red]❌ {msg}[/]")

    def handle_quarantine_management(self):
        self.console.print("\n[bold cyan]📦 Gerenciamento de Quarentena e Restauração (Undo)[/]")
        batches = quarantine_manager.list_all_batches()

        if not batches:
            self.console.print("[dim]A quarentena do PC está vazia. Nenhum item para restaurar.[/]")
            return

        table = Table(title="Lotes em Quarentena no PC", expand=True)
        table.add_column("ID do Lote", style="bold white")
        table.add_column("Data da Limpeza")
        table.add_column("Itens", justify="right")
        table.add_column("Tamanho Total", justify="right")
        table.add_column("Observação")

        for b in batches:
            table.add_row(
                b.batch_id,
                b.created_at.strftime("%d/%m/%Y %H:%M:%S"),
                str(len(b.items)),
                format_bytes(b.total_size_bytes),
                b.note
            )

        self.console.print(table)

        self.console.print("\n[bold yellow]Opções de Quarentena:[/]")
        self.console.print(" [bold green]1[/]. ↩️  [bold green]Restaurar um Lote Completo (Desfazer Limpeza)[/]")
        self.console.print(" [bold red]2[/]. 🗑️  [bold red]Excluir Permanentemente um Lote da Quarentena[/]")
        self.console.print(" [bold dim]0[/]. 🔙 Voltar")

        opt = Prompt.ask("\n[bold cyan]Escolha uma opção[/]", choices=["0", "1", "2"], default="0")
        if opt == "1":
            batch_id = Prompt.ask("Digite o ID do Lote para restaurar")
            succ, fail, errs = quarantine_manager.restore_batch(batch_id)
            self.console.print(f"[bold green]✅ Restauração concluída! Sucessos: {succ}, Falhas: {fail}[/]")
            if errs:
                for e in errs:
                    self.console.print(f"[red]• {e}[/]")
        elif opt == "2":
            batch_id = Prompt.ask("Digite o ID do Lote para excluir permanentemente")
            if Confirm.ask(f"[bold red]Tem certeza que deseja apagar DEFINITIVAMENTE o lote {batch_id}?[/]", default=False):
                ok, err = quarantine_manager.purge_batch(batch_id)
                if ok:
                    self.console.print("[bold green]✅ Lote excluído permanentemente.[/]")
                else:
                    self.console.print(f"[bold red]❌ Erro: {err}[/]")

    def handle_export_report(self):
        if not self.last_findings or not self.last_summary:
            self.console.print("[yellow]Execute uma varredura primeiro antes de exportar o relatório.[/]")
            return

        self.console.print("\n[bold cyan]Escolha o formato de exportação:[/]")
        self.console.print(" [bold green]1[/]. 🌐 Dashboard HTML Interativo (Recomendado)")
        self.console.print(" [bold green]2[/]. 📄 Arquivo JSON Estruturado")

        opt = Prompt.ask("Opção", choices=["1", "2"], default="1")
        if opt == "1":
            out_file = HtmlReportExporter.export(self.last_findings, self.last_summary)
            self.console.print(f"[bold green]✅ Relatório HTML gerado em:[/] [bold white]{out_file}[/]")
            if Confirm.ask("Deseja abrir o relatório no navegador agora?", default=True):
                import webbrowser
                webbrowser.open(str(out_file))
        elif opt == "2":
            out_file = JsonReportExporter.export(self.last_findings, self.last_summary)
            self.console.print(f"[bold green]✅ Relatório JSON gerado em:[/] [bold white]{out_file}[/]")
