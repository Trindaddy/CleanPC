"""
Interface Gráfica Desktop Moderna (GUI) para o CleanPC desenvolvida em CustomTkinter.
Oferece uma experiência visual intuitiva, elegante (Dark/Light mode) e 100% responsiva.
"""

import os
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import customtkinter as ctk
import psutil

from cleanpc_core.config import APP_NAME, APP_VERSION
from cleanpc_core.models import Finding, RiskLevel, ScanCategory
from cleanpc_core.quarantine import quarantine_manager
from cleanpc_executors.cleaner import SafeCleanerExecutor
from cleanpc_executors.process_lock import ProcessLockManager
from cleanpc_executors.system_restore import SystemRestoreManager
from cleanpc_reports.exporter_html import HtmlReportExporter, format_bytes
from cleanpc_scanners.manager import ScannerManager, ScanSummary


class CleanPcGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.title(f"{APP_NAME} — Mega Limpador & Otimizador de PC v{APP_VERSION}")
        self.geometry("1100x720")
        self.minsize(950, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Estado da Aplicação
        self.scanner_manager = ScannerManager()
        self.cleaner = SafeCleanerExecutor()
        self.findings: List[Finding] = []
        self.summary: Optional[ScanSummary] = None
        self.current_filter = "all"
        self.is_scanning = False

        # Configura Layout em Grid (Sidebar + Área Principal)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar_frame.grid_rowconfigure(12, weight=1)

        # Logo / Título
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="🛡️ CleanPC",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Segurança & Reversibilidade Total",
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        # Seletor de Categorias
        self.cat_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="CATEGORIAS DE VARREDURA:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray75"
        )
        self.cat_label.grid(row=2, column=0, padx=20, pady=(5, 5), sticky="w")

        self.category_checkboxes: Dict[ScanCategory, ctk.CTkCheckBox] = {}
        cats_to_display = [
            (ScanCategory.TEMP_FILES, "Arquivos Temporários", True),
            (ScanCategory.BROWSER_CACHE, "Caches de Navegadores", True),
            (ScanCategory.GPU_SHADERS, "Shaders de GPU (NVIDIA/AMD)", True),
            (ScanCategory.APP_CACHES, "Apps (Discord/Spotify/Steam)", True),
            (ScanCategory.WINDOWS_LOGS, "Logs CBS / Windows Update", True),
            (ScanCategory.DEV_CACHES, "Caches Dev (npm/pip/etc)", True),
            (ScanCategory.ORPHAN_FOLDERS, "Pastas Órfãs (Desinstalações)", True),
            (ScanCategory.RECYCLE_BIN, "Lixeira do Windows", True),
            (ScanCategory.ERROR_DUMPS, "Relatórios de Erros (WER)", True)
        ]

        row_idx = 3
        for cat, label, default_checked in cats_to_display:
            cb = ctk.CTkCheckBox(self.sidebar_frame, text=label, font=ctk.CTkFont(size=12))
            if default_checked:
                cb.select()
            cb.grid(row=row_idx, column=0, padx=20, pady=3, sticky="w")
            self.category_checkboxes[cat] = cb
            row_idx += 1

        # Ações do Rodapé da Sidebar
        self.btn_undo = ctk.CTkButton(
            self.sidebar_frame,
            text="📦 Desfazer (Quarentena)",
            fg_color="#334155",
            hover_color="#475569",
            command=self._open_quarantine_window
        )
        self.btn_undo.grid(row=13, column=0, padx=20, pady=5, sticky="ew")

        self.btn_html_report = ctk.CTkButton(
            self.sidebar_frame,
            text="📊 Abrir Relatório HTML",
            fg_color="#1e293b",
            hover_color="#334155",
            command=self._open_html_report
        )
        self.btn_html_report.grid(row=14, column=0, padx=20, pady=(5, 20), sticky="ew")

    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # 1. Cards de Resumo no Topo
        self.cards_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.cards_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_total = self._create_metric_card(self.cards_frame, 0, "Espaço Identificado", "0 B", "0 itens", "#38bdf8")
        self.card_safe = self._create_metric_card(self.cards_frame, 1, "Seguro (Safe)", "0 B", "Caches & Temporários", "#10b981")
        self.card_moderate = self._create_metric_card(self.cards_frame, 2, "Moderado", "0 B", "Lixeira & Resíduos", "#f59e0b")
        self.card_unknown = self._create_metric_card(self.cards_frame, 3, "Requer Análise", "0 B", "Revisão manual", "#a855f7")

        # 2. Barra de Controle e Ações
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="#1e293b", corner_radius=10)
        self.controls_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10), padx=0)
        self.controls_frame.grid_columnconfigure(2, weight=1)

        self.btn_scan = ctk.CTkButton(
            self.controls_frame,
            text="🔍 Iniciar Varredura",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._start_scan_thread
        )
        self.btn_scan.grid(row=0, column=0, padx=(10, 5), pady=8)

        self.btn_clean = ctk.CTkButton(
            self.controls_frame,
            text="🧹 Limpar com Quarentena",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#10b981",
            hover_color="#059669",
            state="disabled",
            command=self._execute_clean_flow
        )
        self.btn_clean.grid(row=0, column=1, padx=5, pady=8)

        self.search_entry = ctk.CTkEntry(
            self.controls_frame,
            placeholder_text="Filtrar por nome, aplicativo ou caminho...",
            height=38
        )
        self.search_entry.grid(row=0, column=2, padx=10, pady=8, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_findings_list())

        # 3. Barra de Progresso e Status
        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Pronto para escanear. Selecione as categorias desejadas à esquerda.",
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        self.status_label.grid(row=0, column=0, sticky="w", pady=(0, 3))

        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.grid(row=1, column=0, sticky="ew")
        self.progress_bar.set(0)

        # 4. Lista Rolável de Achados
        self.list_frame = ctk.CTkScrollableFrame(self.main_frame, corner_radius=10, fg_color="#0f172a")
        self.list_frame.grid(row=3, column=0, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

    def _create_metric_card(self, parent, col, title, value, sub, color_val):
        card = ctk.CTkFrame(parent, fg_color="#1e293b", corner_radius=10)
        card.grid(row=0, column=col, padx=5, sticky="nsew")

        title_lbl = ctk.CTkLabel(card, text=title.upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color="gray60")
        title_lbl.pack(anchor="w", padx=12, pady=(10, 0))

        val_lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=color_val)
        val_lbl.pack(anchor="w", padx=12, pady=(2, 0))

        sub_lbl = ctk.CTkLabel(card, text=sub, font=ctk.CTkFont(size=11), text_color="gray50")
        sub_lbl.pack(anchor="w", padx=12, pady=(0, 10))

        card.val_lbl = val_lbl
        card.sub_lbl = sub_lbl
        return card

    def _start_scan_thread(self):
        if self.is_scanning:
            return

        selected_cats = [cat for cat, cb in self.category_checkboxes.items() if cb.get() == 1]
        if not selected_cats:
            self.status_label.configure(text="⚠️ Selecione pelo menos uma categoria de varredura à esquerda!")
            return

        self.is_scanning = True
        self.btn_scan.configure(state="disabled", text="Varrendo...")
        self.btn_clean.configure(state="disabled")
        self.progress_bar.set(0)

        threading.Thread(target=self._run_scan_worker, args=(selected_cats,), daemon=True).start()

    def _run_scan_worker(self, categories):
        def cb(msg, current, total):
            pct = current / max(total, 1)
            self.after(0, lambda: self._update_progress(msg, pct))

        findings, summary = self.scanner_manager.run_all(categories=categories, progress_callback=cb)

        self.after(0, lambda: self._on_scan_completed(findings, summary))

    def _update_progress(self, msg: str, pct: float):
        self.status_label.configure(text=msg)
        self.progress_bar.set(pct)

    def _on_scan_completed(self, findings: List[Finding], summary: ScanSummary):
        self.findings = findings
        self.summary = summary
        self.is_scanning = False
        self.btn_scan.configure(state="normal", text="🔍 Iniciar Varredura")
        self.progress_bar.set(1.0)

        # Atualiza métricas
        self.card_total.val_lbl.configure(text=format_bytes(summary.total_size_bytes))
        self.card_total.sub_lbl.configure(text=f"{summary.total_findings} itens encontrados")

        self.card_safe.val_lbl.configure(text=format_bytes(summary.safe_size_bytes))
        self.card_moderate.val_lbl.configure(text=format_bytes(summary.moderate_size_bytes))
        self.card_unknown.val_lbl.configure(text=format_bytes(summary.unknown_size_bytes))

        self.status_label.configure(text=f"Varredura finalizada em {summary.duration_seconds}s! {summary.total_findings} itens identificados.")

        if findings:
            self.btn_clean.configure(state="normal")

        self._refresh_findings_list()

    def _refresh_findings_list(self):
        # Limpa widgets da lista
        for w in self.list_frame.winfo_children():
            w.destroy()

        search_txt = self.search_entry.get().lower().strip()

        filtered = []
        for f in self.findings:
            if search_txt:
                match = (
                    search_txt in f.path.lower() or
                    search_txt in f.category.display_name.lower() or
                    (f.related_software and search_txt in f.related_software.lower()) or
                    search_txt in f.reason.lower()
                )
                if not match:
                    continue
            filtered.append(f)

        if not filtered:
            lbl = ctk.CTkLabel(
                self.list_frame,
                text="Nenhum item encontrado nesta busca.",
                font=ctk.CTkFont(size=13),
                text_color="gray50"
            )
            lbl.pack(pady=40)
            return

        # Renderiza os itens filtrados
        for f in filtered[:100]:  # Limite de 100 itens renderizados para suavidade
            self._render_finding_row(f)

    def _render_finding_row(self, finding: Finding):
        row = ctk.CTkFrame(self.list_frame, fg_color="#1e293b", corner_radius=8)
        row.pack(fill="x", padx=5, pady=4)
        row.grid_columnconfigure(1, weight=1)

        # Badge de Risco
        risk_colors = {
            RiskLevel.SAFE: ("#064e3b", "#34d399"),
            RiskLevel.MODERATE: ("#78350f", "#fbbf24"),
            RiskLevel.RISKY: ("#7f1d1d", "#f87171"),
            RiskLevel.UNKNOWN: ("#581c87", "#c084fc")
        }
        bg_col, text_col = risk_colors.get(finding.confidence, ("#1e293b", "white"))

        badge = ctk.CTkLabel(
            row,
            text=finding.confidence.display_name.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=bg_col,
            text_color=text_col,
            corner_radius=6,
            width=80
        )
        badge.grid(row=0, column=0, rowspan=2, padx=10, pady=10)

        # Informações Principais
        title_text = f"{finding.category.display_name} — {finding.related_software or Path(finding.path).name}"
        title_lbl = ctk.CTkLabel(row, text=title_text, font=ctk.CTkFont(size=12, weight="bold"), text_color="white")
        title_lbl.grid(row=0, column=1, sticky="w", padx=5, pady=(8, 0))

        path_lbl = ctk.CTkLabel(row, text=finding.path, font=ctk.CTkFont(size=10), text_color="gray60")
        path_lbl.grid(row=1, column=1, sticky="w", padx=5, pady=(0, 8))

        # Tamanho
        size_lbl = ctk.CTkLabel(row, text=format_bytes(finding.size_bytes), font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8")
        size_lbl.grid(row=0, column=2, rowspan=2, padx=15, pady=10)

    def _execute_clean_flow(self):
        cleanable = [f for f in self.findings if f.confidence in (RiskLevel.SAFE, RiskLevel.MODERATE)]
        if not cleanable:
            return

        # Verifica processos em execução
        blocking_apps = ProcessLockManager.get_running_blocking_apps(cleanable)
        if blocking_apps:
            app_names = [name for name, _ in blocking_apps]
            msg = f"Os seguintes aplicativos estão abertos e podem travar a limpeza:\n\n• {', '.join(app_names)}\n\nDeseja fechá-los suavemente antes de limpar?"
            dialog = ctk.CTkToplevel(self)
            dialog.title("Aplicativos em Execução")
            dialog.geometry("450x220")
            dialog.transient(self)

            lbl = ctk.CTkLabel(dialog, text=msg, justify="left", font=ctk.CTkFont(size=12))
            lbl.pack(padx=20, pady=20)

            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=10)

            def on_close_apps():
                ProcessLockManager.terminate_apps(app_names)
                dialog.destroy()
                self._proceed_with_cleaning(cleanable)

            def on_skip_apps():
                dialog.destroy()
                self._proceed_with_cleaning(cleanable)

            ctk.CTkButton(btn_frame, text="Fechar e Limpar", fg_color="#10b981", command=on_close_apps).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Pular em Uso", fg_color="#64748b", command=on_skip_apps).pack(side="left", padx=5)
            return

        self._proceed_with_cleaning(cleanable)

    def _proceed_with_cleaning(self, cleanable_items):
        self.btn_clean.configure(state="disabled", text="Limpando...")
        self.status_label.configure(text="Movendo arquivos para a Quarentena reversível...")

        def clean_worker():
            report = self.cleaner.execute_cleaning(cleanable_items)
            self.after(0, lambda: self._on_clean_completed(report))

        threading.Thread(target=clean_worker, daemon=True).start()

    def _on_clean_completed(self, report):
        self.btn_clean.configure(state="normal", text="🧹 Limpar com Quarentena")
        self.status_label.configure(
            text=f"✅ Limpeza concluída! {report.successful_items} itens movidos para a Quarentena ({format_bytes(report.total_freed_bytes)} liberados)."
        )
        self.findings = [f for f in self.findings if f.path not in [r.original_path for r in report.quarantine_records]]
        self._refresh_findings_list()

    def _open_quarantine_window(self):
        q_win = ctk.CTkToplevel(self)
        q_win.title("📦 Gerenciador de Quarentena & Desfazer (Undo)")
        q_win.geometry("650x450")
        q_win.transient(self)

        lbl = ctk.CTkLabel(q_win, text="Lotes de Limpeza em Quarentena", font=ctk.CTkFont(size=16, weight="bold"))
        lbl.pack(padx=20, pady=(15, 10), anchor="w")

        batches = quarantine_manager.list_all_batches()
        if not batches:
            ctk.CTkLabel(q_win, text="A Quarentena está vazia. Nenhum item para restaurar.", text_color="gray50").pack(pady=50)
            return

        scroll = ctk.CTkScrollableFrame(q_win, fg_color="#1e293b")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        for b in batches:
            card = ctk.CTkFrame(scroll, fg_color="#0f172a", corner_radius=8)
            card.pack(fill="x", pady=5, padx=5)

            info_text = f"Lote: {b.batch_id}\nData: {b.created_at.strftime('%d/%m/%Y %H:%M')} | {len(b.items)} itens | {format_bytes(b.total_size_bytes)}"
            ctk.CTkLabel(card, text=info_text, justify="left", font=ctk.CTkFont(size=12)).pack(side="left", padx=10, pady=10)

            def make_restore_cb(batch_id):
                return lambda: self._restore_batch_gui(batch_id, q_win)

            ctk.CTkButton(card, text="↩️ Restaurar", width=90, fg_color="#10b981", command=make_restore_cb(b.batch_id)).pack(side="right", padx=10)

    def _restore_batch_gui(self, batch_id: str, window):
        succ, fail, errs = quarantine_manager.restore_batch(batch_id)
        window.destroy()
        self.status_label.configure(text=f"✅ Restauração do lote {batch_id} concluída! {succ} itens restaurados.")

    def _open_html_report(self):
        if not self.findings or not self.summary:
            self.status_label.configure(text="Execute uma varredura primeiro para gerar o relatório.")
            return
        out_file = HtmlReportExporter.export(self.findings, self.summary)
        webbrowser.open(str(out_file))


def launch_gui():
    app = CleanPcGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
