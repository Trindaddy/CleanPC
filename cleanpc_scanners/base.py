"""
Classe base abstrata para todos os scanners do CleanPc.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from cleanpc_core.models import Finding, ScanCategory


class BaseScanner(ABC):
    """Classe base que todo módulo de escaneamento deve implementar."""

    @property
    @abstractmethod
    def category(self) -> ScanCategory:
        """Categoria de varredura correspondente."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome amigável do scanner."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição resumida do que o scanner avalia."""
        pass

    @abstractmethod
    def scan(self, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Finding]:
        """
        Executa a varredura e retorna a lista de achados (Finding).
        progress_callback: Função opcional (status_msg, current, total) para atualização visual na UI.
        """
        pass
