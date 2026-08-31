"""
Interface de Linha de Comando (CLI) Rica e Interativa com Rich.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm

from cleanpc_core.config import APP_NAME, APP_VERSION
from cleanpc_core.logger import app_logger
from cleanpc_core.models import Finding, RiskLevel, ScanCategory
from cleanpc_core.quarantine import quarantine_manager
from cleanpc_executors.cleaner import SafeCleanerExecutor
from cleanpc_executors.optimizer import OptimizerExecutor
from cleanpc_reports.exporter_html import HtmlReportExporter, format_bytes
from cleanpc_reports.exporter_json import JsonReportExporter
from cleanpc_scanners.manager import ScannerManager, ScanSummary


class CleanPcCLI:
    def __init__(self):
        # Configura Console para saída segura
        self.console = Console(highlight=False, soft_wrap=True)
        self.scanner_manager = ScannerManager()
        self.cleaner = SafeCleanerExecutor()
        self.optimizer = OptimizerExecutor()
        self.last_findings: List[Finding] = []
        self.last_summary: Optional[ScanSummary] = None

    def print_banner(self):
        banner_text = f"""[bold cyan]╔════════════════════════════════════════════════════════════════╗[/]
[bold cyan]║[/]   [bold white]🛡️  MEGA LIMPADOR & OTIMIZADOR DE PC[/]  [dim]v{APP_VERSION}[/]                [bold cyan]║[/]
[bold cyan]║[/]   [dim]Segurança Absoluta • Quarentena Reversível • Sem Telemetria[/]  [bold cyan]║[/]
[bold cyan]╚════════════════════════════════════════════════════════════════╝[/]"""
        self.console.print(banner_text)

    def display_main_menu(self):
        self.console.print("\n[bold yellow]MENU PRINCIPAL:[/]")
        self.console.print(" [bold green]1[/]. 🔍 [bold white]Varredura Completa do Sistema[/] (Temp, Caches, Órfãos, Dumps, Startup)")
        self.console.print(" [bold green]2[/]. ⚡ [bold white]Varredura Rápida (Apenas Itens Seguros / Baixo Risco)[/]")
        self.console.print(" [bold green]3[/]. 📁 [bold white]Detecção Avançada de Pastas Órfãs[/] (Resíduos de Desinstalação)")
        self.console.print(" [bold green]4[/]. 🚀 [bold white]Otimização de Desempenho, Startup e SSD (TRIM)[/]")
        self.console.print(" [bold green]5[/]. 👥 [bold white]Buscar Arquivos Duplicados por Hash[/]")
        self.console.print(" [bold green]6[/]. 📦 [bold white]Gerenciar Quarentena & Desfazer Limpeza (Undo/Restore)[/]")
        self.console.print(" [bold green]7[/]. 📊 [bold white]Exportar Relatório Atual (HTML / JSON)[/]")
        self.console.print(" [bold green]8[/]. 📜 [bold white]Ver Logs de Auditoria do Sistema[/]")
        self.console.print(" [bold red]0[/]. 🚪 [bold dim]Sair[/]")

    def run_interactive(self):
        self.print_banner()
        while True:
            self.display_main_menu()
            choice = Prompt.ask("\n[bold cyan]Escolha uma opção[/]", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"], default="1")

            if choice == "0":
                self.console.print("\n[bold cyan]Encerrando o Mega Limpador. Até logo![/]\n")
                break
            elif choice == "1":
                self.handle_full_scan()
            elif choice == "2":
                self.handle_safe_scan()
            elif choice == "3":
                self.handle_orphan_scan()
            elif choice == "4":
                self.handle_optimizations()
            elif choice == "5":
                self.handle_duplicates_scan()
            elif choice == "6":
                self.handle_quarantine_management()
            elif choice == "7":
                self.handle_export_report()
            elif choice == "8":
                self.handle_view_logs()

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
            task = progress.add_task("[cyan]Iniciando varredura do sistema...", total=100)

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

        # Painel de Resumo
        summary_panel = f"""[bold white]Total de Itens:[/] {summary.total_findings} | [bold white]Espaço Total:[/] [bold cyan]{format_bytes(summary.total_size_bytes)}[/] | [bold white]Tempo:[/] {summary.duration_seconds}s
[bold green]● Seguro:[/] {format_bytes(summary.safe_size_bytes)} ({len(summary.findings_by_risk.get('safe', []))} itens)
[bold yellow]● Moderado:[/] {format_bytes(summary.moderate_size_bytes)} ({len(summary.findings_by_risk.get('moderate', []))} itens)
[bold red]● Arriscado:[/] {format_bytes(summary.risky_size_bytes)} ({len(summary.findings_by_risk.get('risky', []))} itens)
[bold magenta]● Requer Análise:[/] {format_bytes(summary.unknown_size_bytes)} ({len(summary.findings_by_risk.get('unknown', []))} itens)"""
        
        self.console.print(Panel(summary_panel, title="[bold cyan]Sumário da Varredura[/]", border_style="cyan"))

        table = Table(title="Itens Identificados na Varredura", expand=True, show_lines=True)
        table.add_column("Risco", style="bold", width=14)
        table.add_column("Categoria", width=22)
        table.add_column("Caminho / Item", style="dim", ratio=3)
        table.add_column("Tamanho", justify="right", width=12)
        table.add_column("Justificativa", ratio=3)

        # Mostra até 35 itens na tabela do terminal para não sobrecarregar
        displayed_items = findings[:35]
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

        if len(findings) > 35:
            self.console.print(f"[dim]... e mais {len(findings) - 35} itens. Use a opção 7 para exportar o relatório HTML completo.[/]")

        # Pergunta de ação
        self.prompt_cleaning_action(findings)

    def prompt_cleaning_action(self, findings: List[Finding]):
        cleanable = [f for f in findings if f.category not in (ScanCategory.STARTUP_ITEMS, ScanCategory.SYSTEM_OPTIMIZATIONS)]
        if not cleanable:
            return

        self.console.print("\n[bold yellow]Ações de Limpeza Disponíveis:[/]")
        self.console.print(" [bold green]1[/]. 🛡️  [bold green]Mover apenas itens SEGUROS para Quarentena (Recomendado)[/]")
        self.console.print(" [bold yellow]2[/]. ⚙️  [bold yellow]Mover itens SEGUROS e MODERADOS para Quarentena[/]")
        self.console.print(" [bold red]3[/]. ⚠️  [bold red]Mover TODOS os itens para Quarentena (Requer Confirmação Extra)[/]")
        self.console.print(" [bold dim]0[/]. 🔙 [bold dim]Não limpar nada / Voltar ao Menu Principal[/]")

        act = Prompt.ask("\n[bold cyan]Deseja executar alguma ação?[/]", choices=["0", "1", "2", "3"], default="0")

        to_clean: List[Finding] = []
        if act == "1":
            to_clean = [f for f in cleanable if f.confidence == RiskLevel.SAFE]
        elif act == "2":
            to_clean = [f for f in cleanable if f.confidence in (RiskLevel.SAFE, RiskLevel.MODERATE)]
        elif act == "3":
            if Confirm.ask("[bold red]ATENÇÃO: Você optou por mover até mesmo itens marcados para Análise Manual. Deseja prosseguir?[/]", default=False):
                to_clean = cleanable
            else:
                self.console.print("[yellow]Operação cancelada.[/]")
                return
        else:
            return

        if not to_clean:
            self.console.print("[yellow]Nenhum item selecionado para limpeza.[/]")
            return

        total_bytes = sum(f.size_bytes for f in to_clean)
        self.console.print(f"\n[bold green]Preparando para mover {len(to_clean)} itens ({format_bytes(total_bytes)}) para a Quarentena...[/]")
        
        if Confirm.ask("[bold cyan]Confirmar envio para quarentena reversível?[/]", default=True):
            with Progress(console=self.console) as progress:
                task = progress.add_task("[green]Enviando para quarentena...", total=len(to_clean))
                
                def cb(msg, curr, tot):
                    progress.update(task, description=f"[green]{msg}", completed=curr)

                report = self.cleaner.execute_cleaning(to_clean, progress_callback=cb)
                progress.update(task, completed=len(to_clean))

            self.console.print(Panel(
                f"""[bold green]✅ Limpeza Concluída com Sucesso![/]
• Itens em Quarentena: [bold white]{report.successful_items}[/]
• Espaço Liberado: [bold cyan]{format_bytes(report.total_freed_bytes)}[/]
• ID do Lote de Quarentena: [bold white]{report.batch_id}[/]
• Falhas/Bloqueios: {report.failed_items + report.skipped_items}

[dim]Você pode restaurar esses arquivos a qualquer momento na opção 'Gerenciar Quarentena'.[/]""",
                title="[bold green]Resultado da Limpeza[/]",
                border_style="green"
            ))

    def handle_full_scan(self):
        self._execute_scan_with_progress()

    def handle_safe_scan(self):
        safe_cats = [
            ScanCategory.TEMP_FILES,
            ScanCategory.BROWSER_CACHE,
            ScanCategory.ERROR_DUMPS,
            ScanCategory.DEV_CACHES,
            ScanCategory.THUMBNAILS
        ]
        self._execute_scan_with_progress(categories=safe_cats)

    def handle_orphan_scan(self):
        self.console.print("\n[bold cyan]Iniciando detecção especializada de resíduos e pastas órfãs...[/]")
        self._execute_scan_with_progress(categories=[ScanCategory.ORPHAN_FOLDERS])

    def handle_duplicates_scan(self):
        from cleanpc_scanners.duplicates import DuplicateFilesScanner
        self.console.print("\n[bold cyan]Varredura de Arquivos Duplicados por Hash...[/]")
        scanner = DuplicateFilesScanner()
        findings: List[Finding] = []

        with Progress(console=self.console) as progress:
            task = progress.add_task("[cyan]Buscando duplicados...", total=100)
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

        # Ações de TRIM
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
            self.console.print("[dim]A quarentena está vazia. Nenhum item aguardando restauração.[/]")
            return

        table = Table(title="Lotes em Quarentena", expand=True)
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
        self.console.print(" [bold dim]0[/]. 🔙 Voltar ao Menu")

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
                    self.console.print("[bold green]✅ Lote excluído permanentemente da quarentena.[/]")
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

    def handle_view_logs(self):
        self.console.print("\n[bold cyan]📜 Logs Recentes de Auditoria:[/]")
        events = app_logger.read_recent_events(limit=15)
        if not events:
            self.console.print("[dim]Nenhum evento registrado ainda.[/]")
            return

        table = Table(title="Auditoria de Ações (cleanpc_activity.jsonl)", expand=True)
        table.add_column("Data/Hora", width=20)
        table.add_column("Ação", width=22)
        table.add_column("Status", width=12)
        table.add_column("Detalhes", ratio=3)

        for ev in events:
            st = ev.get("status", "info")
            st_color = "green" if st == "success" else ("yellow" if st == "blocked" else "red")
            table.add_row(
                ev.get("timestamp", "")[:19].replace("T", " "),
                ev.get("action", ""),
                f"[{st_color}]{st}[/]",
                str(ev.get("details", ""))[:100]
            )

        self.console.print(table)
