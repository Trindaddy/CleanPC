#!/usr/bin/env python3
"""
Mega Limpador & Otimizador de PC — Ponto de Entrada Principal.
"""

import argparse
import sys
from pathlib import Path

# Garante suporte adequado a UTF-8 no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Adiciona o diretório atual ao sys.path para importações locais
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from cleanpc_core.models import ScanCategory
from cleanpc_core.quarantine import quarantine_manager
from cleanpc_reports.exporter_html import HtmlReportExporter, format_bytes
from cleanpc_reports.exporter_json import JsonReportExporter
from cleanpc_scanners.manager import ScannerManager
from cleanpc_ui.cli import CleanPcCLI


def main():
    parser = argparse.ArgumentParser(
        description="CleanPC — Mega Limpador & Otimizador de PC e Smartphones (Seguro & Reversível)"
    )
    parser.add_argument("--gui", action="store_true", help="Inicia a interface gráfica desktop (Janela CustomTkinter)")
    parser.add_argument("--cli", action="store_true", help="Inicia o menu interativo de terminal (Padrão)")
    parser.add_argument("--scan", action="store_true", help="Executa varredura completa imediatamente")
    parser.add_argument("--safe-only", action="store_true", help="Executa apenas varredura de baixo risco (Safe)")
    parser.add_argument("--orphans-only", action="store_true", help="Executa apenas busca por pastas órfãs de programas")
    parser.add_argument("--mobile", action="store_true", help="Executa varredura de celular conectado via USB imediatamente")
    parser.add_argument("--report", choices=["html", "json", "none"], default="none", help="Exporta relatório no formato escolhido")
    parser.add_argument("--quarantine-list", action="store_true", help="Lista lotes atualmente em quarentena")
    parser.add_argument("--restore", type=str, metavar="BATCH_ID", help="Restaura um lote de quarentena pelo ID")

    args = parser.parse_args()

    cli = CleanPcCLI()

    # Se o usuário pediu explicitamente a interface gráfica
    if args.gui:
        try:
            from cleanpc_ui.gui_window import launch_gui
            launch_gui()
            return
        except Exception as e:
            print(f"Não foi possível iniciar a GUI desktop ({e}). Iniciando modo Terminal...\n")
            cli.run_interactive()
            return

    # Modo padrão: Terminal Interativo Rico
    if len(sys.argv) == 1 or args.cli:
        cli.run_interactive()
        return

    # Trata argumentos CLI diretos
    if args.mobile:
        cli.handle_mobile_cleaning()
        return

    if args.quarantine_list:
        cli.handle_quarantine_management()
        return

    if args.restore:
        batch_id = args.restore
        print(f"Iniciando restauração do lote {batch_id}...")
        succ, fail, errs = quarantine_manager.restore_batch(batch_id)
        print(f"Restauração finalizada. Sucessos: {succ}, Falhas: {fail}")
        if errs:
            for e in errs:
                print(f"Erro: {e}")
        return

    if args.scan or args.safe_only or args.orphans_only or args.report != "none":
        cli.print_banner()
        categories = None
        if args.safe_only:
            categories = [
                ScanCategory.TEMP_FILES,
                ScanCategory.BROWSER_CACHE,
                ScanCategory.GPU_SHADERS,
                ScanCategory.APP_CACHES,
                ScanCategory.WINDOWS_LOGS,
                ScanCategory.ERROR_DUMPS,
                ScanCategory.DEV_CACHES,
                ScanCategory.THUMBNAILS
            ]
        elif args.orphans_only:
            categories = [ScanCategory.ORPHAN_FOLDERS]

        print("\nExecutando varredura...")
        scanner_manager = ScannerManager()
        findings, summary = scanner_manager.run_all(categories=categories)
        cli.display_findings_table(findings, summary)

        if args.report == "html":
            out_file = HtmlReportExporter.export(findings, summary)
            print(f"\nRelatório HTML gerado em: {out_file}")
        elif args.report == "json":
            out_file = JsonReportExporter.export(findings, summary)
            print(f"\nRelatório JSON gerado em: {out_file}")


if __name__ == "__main__":
    main()
