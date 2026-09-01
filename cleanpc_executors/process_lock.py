"""
Detector e Gerenciador de Processos em Execução (Prevenção de Arquivos Bloqueados).
Permite identificar e solicitar encerramento suave de aplicativos que possam travar arquivos de cache.
"""

from typing import Dict, List, Set, Tuple
import psutil

from cleanpc_core.logger import app_logger
from cleanpc_core.models import Finding, ScanCategory

# Mapeamento entre categorias/softwares e executáveis de processos
APP_PROCESS_MAP: Dict[str, List[str]] = {
    "google chrome": ["chrome.exe"],
    "microsoft edge": ["msedge.exe"],
    "mozilla firefox": ["firefox.exe"],
    "brave browser": ["brave.exe"],
    "opera stable": ["opera.exe"],
    "opera gx": ["opera.exe"],
    "discord": ["discord.exe", "discordcanary.exe", "discordptb.exe"],
    "spotify": ["spotify.exe"],
    "steam": ["steam.exe"],
    "epic games": ["epicgameslauncher.exe"],
    "telegram": ["telegram.exe"]
}


class ProcessLockManager:
    @staticmethod
    def get_running_blocking_apps(findings: List[Finding]) -> List[Tuple[str, List[int]]]:
        """
        Retorna uma lista de (NomeDoApp, [PIDs_em_execucao]) para os aplicativos
        cujos caches foram marcados para limpeza.
        """
        # Identifica quais apps estão nos achados
        target_apps: Set[str] = set()
        for f in findings:
            if f.category in (ScanCategory.BROWSER_CACHE, ScanCategory.APP_CACHES):
                sw = (f.related_software or "").lower()
                for app_key in APP_PROCESS_MAP:
                    if app_key in sw or sw in app_key:
                        target_apps.add(app_key)

        if not target_apps:
            return []

        # Mapeia processos atualmente ativos no sistema
        running_map: Dict[str, List[int]] = {}
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                p_name = (proc.info['name'] or "").lower()
                for app_key in target_apps:
                    target_exes = [e.lower() for e in APP_PROCESS_MAP[app_key]]
                    if p_name in target_exes:
                        if app_key not in running_map:
                            running_map[app_key] = []
                        running_map[app_key].append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        result = [(app.title(), pids) for app, pids in running_map.items()]
        return result

    @staticmethod
    def terminate_apps(app_display_names: List[str], timeout: float = 3.0) -> Tuple[int, List[str]]:
        """
        Encerra suavemente os aplicativos solicitados pelo usuário.
        Retorna (total_encerrados, lista_de_erros).
        """
        terminated_count = 0
        errors: List[str] = []

        exes_to_kill: Set[str] = set()
        for app_name in app_display_names:
            key = app_name.lower()
            for k, exes in APP_PROCESS_MAP.items():
                if k in key or key in k:
                    for e in exes:
                        exes_to_kill.add(e.lower())

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                p_name = (proc.info['name'] or "").lower()
                if p_name in exes_to_kill:
                    proc.terminate()
                    terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                errors.append(f"Não foi possível encerrar PID {proc.pid}: {e}")

        # Aguarda encerramento suave
        gone, alive = psutil.wait_procs(
            [p for p in psutil.process_iter() if (p.name() or "").lower() in exes_to_kill],
            timeout=timeout
        )
        for p in alive:
            try:
                p.kill()  # Força encerramento se travou
            except Exception:
                pass

        app_logger.info(f"Processos encerrados para limpeza: {terminated_count} processos.")
        return terminated_count, errors
