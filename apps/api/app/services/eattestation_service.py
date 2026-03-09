"""Service d'intégration e-Attestations.com

Vérifie automatiquement la validité des attestations réglementaires :
- Attestation fiscale (DGFiP)
- Attestation de vigilance URSSAF
- Assurance décennale RC Pro
- Extrait Kbis

API e-Attestations.com : https://www.e-attestations.com/api
"""
import httpx
from datetime import datetime, timezone
from typing import Optional
import structlog

from app.config import settings

logger = structlog.get_logger()


class AttestationStatus:
    VALID = "valid"
    EXPIRED = "expired"
    MISSING = "missing"
    UNKNOWN = "unknown"
    MOCK = "mock"  # Données simulées (pas de clé API)


class AttestationResult:
    def __init__(
        self,
        attestation_type: str,
        status: str,
        expires_at: Optional[datetime] = None,
        document_url: Optional[str] = None,
        details: Optional[str] = None,
        is_mock: bool = False,
    ):
        self.attestation_type = attestation_type
        self.status = status
        self.expires_at = expires_at
        self.document_url = document_url
        self.details = details
        self.is_mock = is_mock

    def to_dict(self) -> dict:
        return {
            "type": self.attestation_type,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "document_url": self.document_url,
            "details": self.details,
            "is_mock": self.is_mock,
        }


async def verify_company_attestations(siret: str) -> list[dict]:
    """
    Vérifie les attestations d'une entreprise via son SIRET.

    Retourne une liste de résultats d'attestation.
    Si EATTESTATION_API_KEY est vide, retourne des données simulées.
    """
    if not siret or len(siret.replace(" ", "")) < 9:
        raise ValueError("SIRET invalide (minimum 9 chiffres)")

    siret_clean = siret.replace(" ", "")

    if not settings.EATTESTATION_API_KEY:
        logger.warning("eattestation_api_key_missing", siret=siret_clean[:9] + "***")
        return _generate_mock_results(siret_clean)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{settings.EATTESTATION_BASE_URL}/company/{siret_clean}/attestations",
                headers={
                    "Authorization": f"Bearer {settings.EATTESTATION_API_KEY}",
                    "Accept": "application/json",
                    "User-Agent": "AO-Copilot/1.0",
                },
            )
            response.raise_for_status()
            data = response.json()
            return _parse_api_response(data)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info("eattestation_company_not_found", siret=siret_clean[:9] + "***")
            return [
                AttestationResult(
                    attestation_type="company",
                    status=AttestationStatus.MISSING,
                    details="Entreprise non trouvée dans e-Attestations",
                ).to_dict()
            ]
        logger.error("eattestation_api_error", status=e.response.status_code, siret=siret_clean[:9] + "***")
        raise RuntimeError(f"Erreur API e-Attestations : {e.response.status_code}")

    except httpx.TimeoutException:
        logger.error("eattestation_timeout", siret=siret_clean[:9] + "***")
        raise RuntimeError("Délai d'attente dépassé pour e-Attestations")

    except Exception as e:
        logger.error("eattestation_unexpected_error", error=str(e))
        raise RuntimeError(f"Erreur inattendue : {str(e)}")


def _parse_api_response(data: dict) -> list[dict]:
    """Parse la réponse de l'API e-Attestations en liste de résultats."""
    results = []

    # Structure typique de l'API e-Attestations
    attestations = data.get("attestations", [])
    for att in attestations:
        att_type = att.get("type", "unknown")
        status_raw = att.get("status", "unknown").lower()

        # Normaliser le status
        if status_raw in ("valid", "valide", "active"):
            status = AttestationStatus.VALID
        elif status_raw in ("expired", "expire", "invalide"):
            status = AttestationStatus.EXPIRED
        else:
            status = AttestationStatus.UNKNOWN

        # Parser la date d'expiration
        expires_at = None
        if att.get("expiry_date"):
            try:
                expires_at = datetime.fromisoformat(att["expiry_date"])
            except (ValueError, TypeError):
                pass

        results.append(
            AttestationResult(
                attestation_type=att_type,
                status=status,
                expires_at=expires_at,
                document_url=att.get("document_url"),
                details=att.get("description"),
            ).to_dict()
        )

    return results


def _generate_mock_results(siret: str) -> list[dict]:
    """
    Génère des données simulées pour les tests (quand API key absente).
    Les données sont déterministes basées sur le SIRET pour la cohérence.
    """
    from datetime import timedelta

    # Utiliser les derniers chiffres du SIRET pour varier les statuts
    last_digit = int(siret[-1]) if siret[-1].isdigit() else 0

    attestation_types = [
        {
            "type": "attestation_fiscale",
            "label": "Attestation fiscale (DGFiP)",
            "status": AttestationStatus.VALID if last_digit < 8 else AttestationStatus.EXPIRED,
        },
        {
            "type": "attestation_urssaf",
            "label": "Attestation de vigilance URSSAF",
            "status": AttestationStatus.VALID if last_digit < 7 else AttestationStatus.EXPIRED,
        },
        {
            "type": "assurance_decennale",
            "label": "Assurance décennale RC Pro",
            "status": AttestationStatus.VALID if last_digit < 9 else AttestationStatus.MISSING,
        },
        {
            "type": "kbis",
            "label": "Extrait Kbis",
            "status": AttestationStatus.VALID,
        },
    ]

    results = []
    base_date = datetime.now(timezone.utc)

    for i, att in enumerate(attestation_types):
        from datetime import timedelta
        expires = base_date + timedelta(days=90 + i * 30) if att["status"] == AttestationStatus.VALID else None
        results.append(
            AttestationResult(
                attestation_type=att["type"],
                status=att["status"],
                expires_at=expires,
                details=att["label"] + " (données simulées — configurez EATTESTATION_API_KEY)",
                is_mock=True,
            ).to_dict()
        )

    return results
