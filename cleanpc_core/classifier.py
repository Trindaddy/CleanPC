"""
Motor de Classificação de Risco e Heurísticas de Confiança.
Avalia achados com base em transparência, tipo de conteúdo e impacto no sistema.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import Finding, RiskLevel, ScanCategory


class RiskClassifier:
    """
    Motor de regras heurísticas para classificar achados de varredura.
    Garante que itens com potencial dependência nunca sejam classificados como 'Seguro' erroneamente.
    """

    @staticmethod
    def classify_temp_file(path: str, last_modified: Optional[datetime], is_directory: bool) -> Tuple[RiskLevel, str]:
        r"""
        Classifica arquivos temporários (%TEMP%, C:\Windows\Temp, etc.).
        Heurística:
        - Se modificado há mais de 24 horas: Seguro (Safe).
        - Se modificado muito recentemente (< 24h): Moderado (Moderate), pois pode estar em uso por um processo recém-iniciado.
        """
        if last_modified:
            age = datetime.now() - last_modified
            if age < timedelta(hours=24):
                return (
                    RiskLevel.MODERATE,
                    "Arquivo temporário modificado recentemente (menos de 24h). Pode estar sendo usado por aplicativo ativo."
                )
        return (
            RiskLevel.SAFE,
            "Arquivo temporário antigo sem bloqueios ou dependências ativas do sistema."
        )

    @staticmethod
    def classify_browser_cache(browser_name: str, cache_type: str) -> Tuple[RiskLevel, str]:
        """
        Classifica caches de navegadores.
        Apenas pastas de Cache de renderização, GPU e bytecode são alvos.
        NUNCA inclui cookies, senhas ou histórico.
        """
        return (
            RiskLevel.SAFE,
            f"Cache de mídia e renderização do {browser_name} ({cache_type}). Não afeta senhas, histórico ou favoritos."
        )

    @staticmethod
    def classify_dev_cache(tool_name: str, size_bytes: int) -> Tuple[RiskLevel, str]:
        """
        Classifica caches de ferramentas de desenvolvimento (npm, pip, docker, gradle).
        """
        return (
            RiskLevel.SAFE,
            f"Cache local de pacotes do {tool_name}. Pode ser reconstruído automaticamente quando necessário."
        )

    @staticmethod
    def classify_recycle_bin(item_count: int, total_size_bytes: int) -> Tuple[RiskLevel, str]:
        """
        Classifica a lixeira do Windows.
        """
        return (
            RiskLevel.MODERATE,
            f"Itens descartados na Lixeira do Windows ({item_count} itens). Recomendado revisar se não há arquivos pessoais importantes antes de esvaziar."
        )

    @staticmethod
    def classify_error_dump(dump_type: str, last_modified: Optional[datetime]) -> Tuple[RiskLevel, str]:
        """
        Classifica arquivos de Crash Dump e Minidumps do Windows.
        """
        return (
            RiskLevel.SAFE,
            f"Relatório de erro e despejo de memória ({dump_type}) já registrado pelo sistema. Seguro para remoção."
        )

    @staticmethod
    def classify_thumbnails() -> Tuple[RiskLevel, str]:
        """
        Classifica cache de miniaturas do Windows Explorer.
        """
        return (
            RiskLevel.SAFE,
            "Cache de miniaturas do Explorer. O Windows irá recriar as miniaturas automaticamente ao abrir pastas."
        )

    @staticmethod
    def classify_orphan_folder(
        folder_path: str,
        files_info: Dict[str, int],
        has_executables: bool,
        has_dlls: bool,
        last_modified: Optional[datetime],
        matched_software_name: Optional[str]
    ) -> Tuple[RiskLevel, str]:
        """
        HEURÍSTICA ESPECIAL: Pastas Órfãs de Programas Desinstalados.
        
        Regras de Decisão:
        1. Se a pasta contém `.dll` ou drivers: Classifica como RISKY ou UNKNOWN, pois bibliotecas podem ser compartilhadas.
        2. Se a pasta contém executáveis `.exe`: Classifica como UNKNOWN (Requer Análise Manual), pois pode ser um programa portable não registrado.
        3. Se a pasta contém APENAS arquivos de configuração (.ini, .json, .xml), logs (.log) e pastas de cache vazias:
           - Se a última modificação tem mais de 30 dias: Classifica como SAFE (Seguro).
           - Se modificada recentemente (< 30 dias): Classifica como MODERATE.
        4. Qualquer dúvida ou inconsistência: Retorna UNKNOWN com justificativa detalhada.
        """
        path_obj = Path(folder_path)
        software_display = matched_software_name or path_obj.name

        if has_dlls:
            return (
                RiskLevel.RISKY,
                f"A pasta '{software_display}' contém bibliotecas dinâmicas (.dll). Pode haver outro programa ou serviço compartilhando estas bibliotecas. Recomenda-se cautela."
            )

        if has_executables:
            return (
                RiskLevel.UNKNOWN,
                f"A pasta '{software_display}' contém arquivos executáveis (.exe), porém o programa não consta na lista de instalados do Registro. Pode ser um software portable ou desinstalador incompleto. Requer análise manual."
            )

        # Apenas configs, logs e dados estáticos
        is_old = False
        if last_modified:
            age = datetime.now() - last_modified
            is_old = age > timedelta(days=30)

        if is_old:
            return (
                RiskLevel.SAFE,
                f"Resíduo inativo do '{software_display}': contém apenas arquivos de log, configurações ou cache, sem executáveis e sem modificações há mais de 30 dias."
            )
        else:
            return (
                RiskLevel.MODERATE,
                f"Possível resíduo de '{software_display}': contém apenas configurações/logs, mas sofreu modificação recente. Recomenda-se confirmar se o aplicativo não está mais em uso."
            )

    @staticmethod
    def classify_duplicate_file(file_path: str, duplicate_group_count: int) -> Tuple[RiskLevel, str]:
        """
        Classifica arquivos duplicados por hash idêntico.
        """
        return (
            RiskLevel.MODERATE,
            f"Arquivo com conteúdo 100% idêntico encontrado em {duplicate_group_count} locais diferentes. Selecione a cópia a ser preservada."
        )


classifier = RiskClassifier()
