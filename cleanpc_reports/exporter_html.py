"""
Exportador de Relatório Visual em HTML Dashboard Interativo.
Gera uma página única auto-contida, moderna e responsiva com filtros dinâmicos em JavaScript.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from cleanpc_core.config import REPORTS_DIR, ensure_directories
from cleanpc_core.models import Finding, RiskLevel
from cleanpc_scanners.manager import ScanSummary


def format_bytes(bytes_num: int) -> str:
    if bytes_num <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_num) < 1024.0:
            return f"{bytes_num:3.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"


class HtmlReportExporter:
    @staticmethod
    def export(findings: List[Finding], summary: ScanSummary, output_path: Path | None = None) -> Path:
        ensure_directories()
        if output_path is None:
            filename = f"cleanpc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            output_path = REPORTS_DIR / filename

        total_size_str = format_bytes(summary.total_size_bytes)
        safe_size_str = format_bytes(summary.safe_size_bytes)
        moderate_size_str = format_bytes(summary.moderate_size_bytes)
        risky_size_str = format_bytes(summary.risky_size_bytes)
        unknown_size_str = format_bytes(summary.unknown_size_bytes)

        findings_json = json.dumps([f.to_dict() for f in findings], ensure_ascii=False)

        html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mega Limpador & Otimizador — Relatório de Varredura</title>
    <style>
        :root {{
            --bg-main: #0f172a;
            --bg-card: #1e293b;
            --bg-card-hover: #334155;
            --border-color: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --safe-color: #10b981;
            --moderate-color: #f59e0b;
            --risky-color: #ef4444;
            --unknown-color: #a855f7;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        body {{
            background-color: var(--bg-main);
            color: var(--text-main);
            padding: 2rem;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 2rem;
        }}
        .logo-title h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            color: #60a5fa;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .logo-title p {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        .meta-tag {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }}
        .card-title {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }}
        .card-value {{
            font-size: 1.8rem;
            font-weight: 700;
        }}
        .card-sub {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.25rem;
        }}
        .card-safe .card-value {{ color: var(--safe-color); }}
        .card-moderate .card-value {{ color: var(--moderate-color); }}
        .card-risky .card-value {{ color: var(--risky-color); }}
        .card-unknown .card-value {{ color: var(--unknown-color); }}
        .card-total .card-value {{ color: #38bdf8; }}

        .controls-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            background-color: var(--bg-card);
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid var(--border-color);
        }}
        .search-box {{
            flex: 1;
            min-width: 250px;
        }}
        .search-box input {{
            width: 100%;
            padding: 0.6rem 1rem;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            background-color: var(--bg-main);
            color: var(--text-main);
            font-size: 0.95rem;
        }}
        .filter-group {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}
        .filter-btn {{
            background-color: var(--bg-main);
            color: var(--text-muted);
            border: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background-color: var(--primary);
            color: #ffffff;
            border-color: var(--primary);
        }}

        .table-wrapper {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }}
        th {{
            background-color: #1e293b;
            padding: 1rem;
            font-weight: 600;
            border-bottom: 2px solid var(--border-color);
            color: var(--text-muted);
        }}
        td {{
            padding: 1rem;
            border-bottom: 1px solid var(--border-color);
            vertical-align: top;
        }}
        tr:hover td {{
            background-color: var(--bg-card-hover);
        }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }}
        .badge-safe {{ background-color: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }}
        .badge-moderate {{ background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }}
        .badge-risky {{ background-color: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }}
        .badge-unknown {{ background-color: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #a855f7; }}

        .path-text {{
            font-family: monospace;
            font-size: 0.85rem;
            color: #cbd5e1;
            word-break: break-all;
        }}
        .reason-text {{
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }}
        footer {{
            margin-top: 3rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-title">
                <h1>🛡️ Mega Limpador & Otimizador de PC</h1>
                <p>Relatório de Auditoria e Diagnóstico de Armazenamento</p>
            </div>
            <div class="meta-tag">
                Gerado em: <strong>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</strong> | Duração: {summary.duration_seconds}s
            </div>
        </header>

        <div class="summary-grid">
            <div class="card card-total">
                <div class="card-title">Espaço Total Identificado</div>
                <div class="card-value">{total_size_str}</div>
                <div class="card-sub">{summary.total_findings} itens encontrados</div>
            </div>
            <div class="card card-safe">
                <div class="card-title">Baixo Risco (Seguro)</div>
                <div class="card-value">{safe_size_str}</div>
                <div class="card-sub">Caches e temporários puros</div>
            </div>
            <div class="card card-moderate">
                <div class="card-title">Risco Moderado</div>
                <div class="card-value">{moderate_size_str}</div>
                <div class="card-sub">Lixeira e resíduos parciais</div>
            </div>
            <div class="card card-risky">
                <div class="card-title">Arriscado</div>
                <div class="card-value">{risky_size_str}</div>
                <div class="card-sub">Possui DLLs ou dependências</div>
            </div>
            <div class="card card-unknown">
                <div class="card-title">Requer Análise Manual</div>
                <div class="card-value">{unknown_size_str}</div>
                <div class="card-sub">Executáveis órfãos / Não registrados</div>
            </div>
        </div>

        <div class="controls-bar">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Filtrar por nome, caminho ou aplicativo..." onkeyup="filterTable()">
            </div>
            <div class="filter-group">
                <button class="filter-btn active" onclick="setRiskFilter('all', this)">Todos</button>
                <button class="filter-btn" onclick="setRiskFilter('safe', this)">Seguros ({len(summary.findings_by_risk.get('safe', []))})</button>
                <button class="filter-btn" onclick="setRiskFilter('moderate', this)">Moderados ({len(summary.findings_by_risk.get('moderate', []))})</button>
                <button class="filter-btn" onclick="setRiskFilter('risky', this)">Arriscados ({len(summary.findings_by_risk.get('risky', []))})</button>
                <button class="filter-btn" onclick="setRiskFilter('unknown', this)">Análise Manual ({len(summary.findings_by_risk.get('unknown', []))})</button>
            </div>
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th style="width: 140px;">Confiança</th>
                        <th style="width: 200px;">Categoria</th>
                        <th>Caminho / Item</th>
                        <th style="width: 120px;">Tamanho</th>
                        <th style="width: 150px;">Software / Origem</th>
                        <th>Justificativa / Motivo</th>
                    </tr>
                </thead>
                <tbody id="findingsTableBody">
                </tbody>
            </table>
        </div>

        <footer>
            Mega Limpador & Otimizador de PC — Operação 100% local, transparente e reversível com quarentena prévia.
        </footer>
    </div>

    <script>
        const findingsData = {findings_json};
        let currentRiskFilter = 'all';

        function formatBytesJs(bytes) {{
            if (!bytes || bytes <= 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }}

        function renderTable(items) {{
            const tbody = document.getElementById('findingsTableBody');
            tbody.innerHTML = '';

            if (items.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 2rem;">Nenhum item corresponde aos filtros selecionados.</td></tr>';
                return;
            }}

            items.forEach(f => {{
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><span class="badge badge-${{f.confidence}}">${{f.confidence_display}}</span></td>
                    <td><strong>${{f.category_name}}</strong></td>
                    <td>
                        <div class="path-text">${{f.path}}</div>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">${{f.file_count}} arquivo(s) ${{f.is_directory ? '(Diretório)' : ''}}</div>
                    </td>
                    <td><strong>${{formatBytesJs(f.size_bytes)}}</strong></td>
                    <td>${{f.related_software || '<span style="color: #64748b;">Sistema / Geral</span>'}}</td>
                    <td><div class="reason-text">${{f.reason}}</div></td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function setRiskFilter(risk, btn) {{
            currentRiskFilter = risk;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterTable();
        }}

        function filterTable() {{
            const search = document.getElementById('searchInput').value.toLowerCase();
            const filtered = findingsData.filter(f => {{
                const matchRisk = (currentRiskFilter === 'all' || f.confidence === currentRiskFilter);
                const matchSearch = !search ||
                    f.path.toLowerCase().includes(search) ||
                    f.category_name.toLowerCase().includes(search) ||
                    (f.related_software && f.related_software.toLowerCase().includes(search)) ||
                    f.reason.toLowerCase().includes(search);
                return matchRisk && matchSearch;
            }});
            renderTable(filtered);
        }}

        // Render inicial
        renderTable(findingsData);
    </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        return output_path
