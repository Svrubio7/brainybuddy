import json
import logging
from typing import Any

import httpx
from jose import JWTError, jwk, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache the JWKS keys in-process
_jwks_cache: dict[str, Any] | None = None


def _get_jwks_url() -> str:
    return f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"


def _load_jwks() -> dict[str, list[dict[str, Any]]]:
    """Fetch JWKS from Supabase discovery endpoint (cached in-process)."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    resp = httpx.get(_get_jwks_url(), timeout=10)
    resp.raise_for_status()
    _jwks_cache = resp.json()
    return _jwks_cache


def clear_jwks_cache() -> None:
    global _jwks_cache
    _jwks_cache = None


def verify_supabase_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a Supabase-issued JWT using ES256 JWKS."""
    try:
        # Get the signing key id from the token header
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        jwks = _load_jwks()
        signing_key = None
        for key_data in jwks.get("keys", []):
            if key_data.get("kid") == kid:
                signing_key = key_data
                break

        if signing_key is None:
            # Key not found — clear cache and retry once
            clear_jwks_cache()
            jwks = _load_jwks()
            for key_data in jwks.get("keys", []):
                if key_data.get("kid") == kid:
                    signing_key = key_data
                    break

        if signing_key is None:
            logger.warning("No matching JWK found for kid=%s", kid)
            return None

        alg = signing_key.get("alg", "ES256")
        key = jwk.construct(signing_key, algorithm=alg)

        payload = jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience="authenticated",
        )
        return payload
    except (JWTError, httpx.HTTPError, KeyError) as exc:
        logger.debug("JWT verification failed: %s", exc)
        return None
