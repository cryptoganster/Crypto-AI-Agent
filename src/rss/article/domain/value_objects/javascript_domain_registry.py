"""
Value Object para registro de dominios que requieren JavaScript.
Encapsula conocimiento de sitios SPA/JavaScript-heavy.
"""

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class JavaScriptDomainRegistry:
    """
    Value Object para registro de dominios JS-heavy.

    Provee:
    - Lista inmutable de dominios conocidos que requieren JS
    - Métodos de consulta y validación
    - Categorización por tipo de sitio
    """

    domains: FrozenSet[str]

    def __post_init__(self):
        """Validación post-inicialización."""
        if not isinstance(self.domains, (frozenset, set)):
            raise TypeError(
                f"domains debe ser set/frozenset, recibido: {type(self.domains)}"
            )

        # Normalizar todos los dominios a lowercase
        normalized = frozenset(d.lower().replace("www.", "") for d in self.domains)
        object.__setattr__(self, "domains", normalized)

    @classmethod
    def default(cls) -> "JavaScriptDomainRegistry":
        """
        Crea registry con dominios conocidos por defecto.

        Incluye:
        - Redes sociales (Medium, Twitter, Facebook, LinkedIn, Reddit, Instagram)
        - Plataformas de video (YouTube)
        - Sitios financieros (Bloomberg, WSJ, Financial Times)
        """
        default_domains = {
            # Redes sociales y plataformas de contenido
            "medium.com",
            "twitter.com",
            "x.com",
            "facebook.com",
            "linkedin.com",
            "reddit.com",
            "instagram.com",
            # Plataformas de video
            "youtube.com",
            # Sitios de noticias financieras y crypto JS-heavy
            "bloomberg.com",
            "wsj.com",  # Wall Street Journal
            "ft.com",  # Financial Times
            "cointelegraph.com",  # Crypto news (SPA)
            # Plataformas de desarrollo
            "github.com",
            "gitlab.com",
            # Plataformas de streaming
            "twitch.tv",
            "netflix.com",
            # Sitios de e-commerce conocidos
            "amazon.com",
            "ebay.com",
        }
        return cls(frozenset(default_domains))

    @classmethod
    def create(cls, domains: set) -> "JavaScriptDomainRegistry":
        """Factory method para crear registry personalizado."""
        return cls(frozenset(domains))

    @classmethod
    def empty(cls) -> "JavaScriptDomainRegistry":
        """Crea registry vacío."""
        return cls(frozenset())

    def contains(self, domain: str) -> bool:
        """
        Verifica si un dominio está en el registry.

        Args:
            domain: Dominio a verificar (se normaliza automáticamente)

        Returns:
            True si el dominio requiere JavaScript
        """
        if not domain:
            return False

        normalized = domain.lower().replace("www.", "")
        return normalized in self.domains

    def add(self, domain: str) -> "JavaScriptDomainRegistry":
        """
        Crea nuevo registry agregando un dominio.

        Args:
            domain: Dominio a agregar

        Returns:
            Nuevo JavaScriptDomainRegistry con dominio agregado
        """
        normalized = domain.lower().replace("www.", "")
        new_domains = self.domains | {normalized}
        return JavaScriptDomainRegistry(new_domains)

    def remove(self, domain: str) -> "JavaScriptDomainRegistry":
        """
        Crea nuevo registry removiendo un dominio.

        Args:
            domain: Dominio a remover

        Returns:
            Nuevo JavaScriptDomainRegistry sin el dominio
        """
        normalized = domain.lower().replace("www.", "")
        new_domains = self.domains - {normalized}
        return JavaScriptDomainRegistry(new_domains)

    def merge(self, other: "JavaScriptDomainRegistry") -> "JavaScriptDomainRegistry":
        """
        Combina dos registries.

        Args:
            other: Otro registry a combinar

        Returns:
            Nuevo registry con dominios combinados
        """
        merged_domains = self.domains | other.domains
        return JavaScriptDomainRegistry(merged_domains)

    def get_social_media_domains(self) -> FrozenSet[str]:
        """Retorna solo dominios de redes sociales."""
        social = {
            "medium.com",
            "twitter.com",
            "x.com",
            "facebook.com",
            "linkedin.com",
            "reddit.com",
            "instagram.com",
        }
        return self.domains & social

    def get_news_domains(self) -> FrozenSet[str]:
        """Retorna solo dominios de noticias."""
        news = {"bloomberg.com", "wsj.com", "ft.com"}
        return self.domains & news

    def count(self) -> int:
        """Retorna cantidad de dominios en el registry."""
        return len(self.domains)

    def is_empty(self) -> bool:
        """Verifica si el registry está vacío."""
        return len(self.domains) == 0

    def __len__(self) -> int:
        return len(self.domains)

    def __contains__(self, domain: str) -> bool:
        """Permite usar 'in' operator."""
        return self.contains(domain)

    def __str__(self) -> str:
        return f"JavaScriptDomainRegistry({len(self.domains)} domains)"

    def __repr__(self) -> str:
        domains_preview = list(self.domains)[:3]
        preview = ", ".join(domains_preview)
        suffix = "..." if len(self.domains) > 3 else ""
        return f"JavaScriptDomainRegistry(domains={{{preview}{suffix}}})"
