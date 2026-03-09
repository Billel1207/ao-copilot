"""TED (Tenders Electronic Daily) — API publique EU sans clé d'authentification.

Interroge le portail officiel européen des marchés publics pour compléter
la veille BOAMP avec des appels d'offres européens (France + Belgique,
Wallonie, Luxembourg si l'option est activée).
"""
import httpx
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)

TED_API_BASE = "https://ted.europa.eu/api/v3.0"
TED_TIMEOUT_S = 15.0
TED_PAGE_SIZE = 50


async def search_ted_notices(
    keywords: list[str],
    cpv_codes: list[str] | None = None,
    countries: list[str] | None = None,
    days_back: int = 7,
) -> list[dict]:
    """Cherche des avis de marchés publics sur TED.

    Args:
        keywords: Mots-clés de recherche (opérateur OR entre eux).
        cpv_codes: Codes CPV à filtrer (opérateur OR entre eux).
        countries: Codes pays ISO 2 lettres (ex: ["FR", "BE", "LU"]).
                   Si None, recherche sur tous les pays.
        days_back: Nombre de jours en arrière pour la date de publication.

    Returns:
        Liste de dicts normalisés représentant les avis TED.
    """
    query_parts: list[str] = []

    if keywords:
        query_parts.append(f"({' OR '.join(keywords)})")
    if cpv_codes:
        query_parts.append(f"cpv:({' OR '.join(cpv_codes)})")
    if countries:
        query_parts.append(f"CY:({' OR '.join(countries)})")

    date_from = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y%m%d")
    query_parts.append(f"DD:[{date_from} TO *]")

    params = {
        "query": " AND ".join(query_parts) if query_parts else "*",
        "fields": "ND,TI,CY,DD,DT,OC,PR,PC",
        "limit": TED_PAGE_SIZE,
        "page": 1,
        "scope": "0",  # avis actifs uniquement
    }

    try:
        async with httpx.AsyncClient(timeout=TED_TIMEOUT_S) as client:
            resp = await client.get(
                f"{TED_API_BASE}/notices/search",
                params=params,
                headers={"Accept": "application/json"},
            )
            if resp.status_code != 200:
                logger.warning(
                    "ted_api_error",
                    status=resp.status_code,
                    body=resp.text[:200],
                )
                return []
            data = resp.json()
            notices = data.get("notices") or data.get("results") or []
            parsed = _parse_ted(notices)
            logger.info("ted_search_ok", count=len(parsed), query=params["query"][:100])
            return parsed
    except httpx.TimeoutException:
        logger.warning("ted_api_timeout", timeout=TED_TIMEOUT_S)
        return []
    except Exception as e:
        logger.error("ted_search_error", error=str(e))
        return []


def _parse_ted(notices: list) -> list[dict]:
    """Transforme les avis TED bruts en dicts normalisés compatibles AoWatchResult."""
    results = []
    for n in notices:
        # Titre multilingue — préférer FR, puis EN, puis premier dispo
        title_obj = n.get("TI", {})
        if isinstance(title_obj, dict):
            title = (
                title_obj.get("FR")
                or title_obj.get("EN")
                or next(iter(title_obj.values()), "Sans titre")
            )
        else:
            title = str(title_obj) if title_obj else "Sans titre"

        # Acheteur
        oc = n.get("OC", {})
        buyer = oc.get("OfficialName", "") if isinstance(oc, dict) else ""

        # Codes CPV
        pc = n.get("PC", {})
        if isinstance(pc, dict):
            cpv_codes = [pc.get("Code", "")] if pc.get("Code") else []
        elif isinstance(pc, list):
            cpv_codes = [str(c.get("Code", "")) for c in pc if isinstance(c, dict) and c.get("Code")]
        else:
            cpv_codes = []

        ted_ref = str(n.get("ND", ""))

        results.append(
            {
                "source": "TED",
                "ted_ref": ted_ref,
                # On stocke la ref TED dans boamp_ref pour rester compatible avec le modèle
                "boamp_ref": f"TED-{ted_ref}" if ted_ref else "",
                "title": str(title)[:1000],
                "buyer": str(buyer)[:500] or None,
                "country": str(n.get("CY", "")).upper()[:10] or None,
                "region": str(n.get("CY", "")).upper()[:255] or None,
                "publication_date": _parse_ted_date(n.get("DD")),
                "deadline_date": _parse_ted_date(n.get("DT")),
                "url": f"https://ted.europa.eu/fr/notice/{ted_ref}" if ted_ref else None,
                "cpv_codes": cpv_codes,
                "estimated_value_eur": None,
                "procedure": str(n.get("PR", ""))[:255] or None,
            }
        )
    return results


def _parse_ted_date(raw: str | None) -> datetime | None:
    """Parse une date TED (YYYYMMDD, YYYY-MM-DD ou ISO) en datetime UTC."""
    if not raw:
        return None
    from datetime import timezone

    raw_str = str(raw).strip()
    candidates = [
        (8,  "%Y%m%d"),
        (10, "%Y-%m-%d"),
        (19, "%Y-%m-%dT%H:%M:%S"),
    ]
    for length, fmt in candidates:
        try:
            dt = datetime.strptime(raw_str[:length], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None
