"""Service de veille BOAMP — interroge l'API officielle BOAMP et synchronise les résultats."""
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session  # utilisé par les workers Celery synchrones

from app.models.ao_alert import AoWatchConfig, AoWatchResult

logger = logging.getLogger(__name__)

BOAMP_API_URL = "https://www.boamp.fr/api/explore/v2.1/catalog/datasets/boamp/records"
BOAMP_TIMEOUT_S = 30
BOAMP_PAGE_SIZE = 100  # max par requête


def _build_query_params(config: AoWatchConfig) -> dict[str, Any]:
    """Construit les paramètres de requête BOAMP depuis la config org."""
    params: dict[str, Any] = {
        "limit": BOAMP_PAGE_SIZE,
        "order_by": "dateparution desc",
    }

    where_clauses: list[str] = []

    # Filtre mots-clés (recherche dans objet)
    if config.keywords:
        kw_parts = [f'search(objet, "{kw}")' for kw in config.keywords]
        where_clauses.append(f"({' OR '.join(kw_parts)})")

    # Filtre région (département ou région dans lieu)
    if config.regions:
        region_parts = [f'search(lieu, "{r}")' for r in config.regions]
        where_clauses.append(f"({' OR '.join(region_parts)})")

    # Filtre CPV
    if config.cpv_codes:
        cpv_parts = [f'search(cpv, "{c}")' for c in config.cpv_codes]
        where_clauses.append(f"({' OR '.join(cpv_parts)})")

    if where_clauses:
        params["where"] = " AND ".join(where_clauses)

    return params


def _parse_date(raw: str | None) -> datetime | None:
    """Parse une date ISO ou format BOAMP vers un datetime UTC."""
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(raw[:19] if "T" in raw else raw, fmt.split("%z")[0])
            return dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def _parse_value(raw: Any) -> int | None:
    """Extrait une valeur entière depuis le champ valeur_estimee BOAMP."""
    if raw is None:
        return None
    try:
        return int(float(str(raw).replace(",", ".").replace(" ", "")))
    except (ValueError, TypeError):
        return None


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Transforme un enregistrement BOAMP brut en dict normalisé."""
    fields = record.get("fields", record)  # selon version API

    # Référence unique BOAMP
    boamp_ref = (
        fields.get("idweb")
        or fields.get("reference")
        or fields.get("id_web")
        or str(record.get("record_id", ""))
        or str(uuid.uuid4())
    )

    # CPV : peut être une string ou une liste
    cpv_raw = fields.get("cpv") or fields.get("codeCPV") or []
    if isinstance(cpv_raw, str):
        cpv_codes = [c.strip() for c in cpv_raw.split(",") if c.strip()]
    elif isinstance(cpv_raw, list):
        cpv_codes = [str(c) for c in cpv_raw if c]
    else:
        cpv_codes = []

    # URL vers l'annonce
    annonce_url = (
        fields.get("urlannonce")
        or fields.get("url")
        or (f"https://www.boamp.fr/avis/detail/{boamp_ref}" if boamp_ref else None)
    )

    return {
        "boamp_ref": boamp_ref,
        "title": str(fields.get("objet") or fields.get("intitule") or "Sans titre")[:1000],
        "buyer": str(fields.get("nomacheteur") or fields.get("acheteur") or "")[:500] or None,
        "region": str(fields.get("lieu") or fields.get("region") or "")[:255] or None,
        "publication_date": _parse_date(fields.get("dateparution") or fields.get("date_publication")),
        "deadline_date": _parse_date(
            fields.get("datelimitereponse")
            or fields.get("date_limite_reponse")
            or fields.get("datelimite")
        ),
        "estimated_value_eur": _parse_value(
            fields.get("valeurestimee") or fields.get("valeur_estimee")
        ),
        "procedure": str(fields.get("procedure") or fields.get("typemarche") or "")[:255] or None,
        "cpv_codes": cpv_codes,
        "url": str(annonce_url)[:2000] if annonce_url else None,
    }


def fetch_boamp_results(config: AoWatchConfig) -> list[dict[str, Any]]:
    """Interroge l'API BOAMP et retourne une liste d'AO normalisés.

    Filtre côté serveur via les paramètres BOAMP, puis applique un filtre
    budget côté client si min_budget_eur / max_budget_eur sont configurés.
    """
    params = _build_query_params(config)

    try:
        with httpx.Client(timeout=BOAMP_TIMEOUT_S) as client:
            response = client.get(BOAMP_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        logger.warning("BOAMP API timeout après %ss", BOAMP_TIMEOUT_S)
        return []
    except httpx.HTTPStatusError as exc:
        logger.warning("BOAMP API erreur HTTP %s : %s", exc.response.status_code, exc.response.text[:200])
        return []
    except Exception as exc:
        logger.error("BOAMP API erreur inattendue : %s", exc)
        return []

    # L'API BOAMP v2.1 retourne {"total_count": N, "results": [...]}
    raw_records: list[dict] = data.get("results") or data.get("records") or []

    normalized: list[dict[str, Any]] = []
    for record in raw_records:
        try:
            norm = _normalize_record(record)
        except Exception as exc:
            logger.debug("Erreur normalisation record BOAMP : %s", exc)
            continue

        # Filtre budget côté client
        val = norm.get("estimated_value_eur")
        if config.min_budget_eur is not None and val is not None and val < config.min_budget_eur:
            continue
        if config.max_budget_eur is not None and val is not None and val > config.max_budget_eur:
            continue

        normalized.append(norm)

    logger.info(
        "BOAMP fetch org=%s : %d résultats bruts → %d après filtres",
        config.org_id, len(raw_records), len(normalized),
    )
    return normalized


def sync_watch_results(db: Session, org_id: uuid.UUID) -> int:
    """Synchronise les résultats BOAMP pour une org.

    Récupère la config active, interroge l'API, sauvegarde les nouveaux
    résultats (dédupliqués par boamp_ref) et met à jour last_checked_at.

    Returns:
        Nombre de nouveaux résultats insérés.
    """
    # Récupérer la config org
    config: AoWatchConfig | None = (
        db.query(AoWatchConfig)
        .filter(AoWatchConfig.org_id == org_id, AoWatchConfig.is_active.is_(True))
        .first()
    )
    if not config:
        logger.debug("Aucune config veille active pour org=%s", org_id)
        return 0

    # Interroger l'API BOAMP
    results = fetch_boamp_results(config)
    if not results:
        config.last_checked_at = datetime.now(timezone.utc)
        db.commit()
        return 0

    # Charger les refs déjà connues pour cette org (éviter les doublons)
    existing_refs: set[str] = {
        row[0]
        for row in db.query(AoWatchResult.boamp_ref)
        .filter(AoWatchResult.org_id == org_id)
        .all()
    }

    new_count = 0
    for item in results:
        if item["boamp_ref"] in existing_refs:
            continue  # déjà en base

        watch_result = AoWatchResult(
            org_id=org_id,
            boamp_ref=item["boamp_ref"],
            title=item["title"],
            buyer=item.get("buyer"),
            region=item.get("region"),
            publication_date=item.get("publication_date"),
            deadline_date=item.get("deadline_date"),
            estimated_value_eur=item.get("estimated_value_eur"),
            procedure=item.get("procedure"),
            cpv_codes=item.get("cpv_codes", []),
            url=item.get("url"),
            is_read=False,
        )
        db.add(watch_result)
        existing_refs.add(item["boamp_ref"])
        new_count += 1

    config.last_checked_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "BOAMP sync org=%s : %d nouveaux résultats insérés",
        org_id, new_count,
    )
    return new_count
