import json
import logging
from typing import Any, Dict, Iterable

from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now

from bomberos.models import ApiLog

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {"password", "pass", "pwd", "token", "access", "refresh"}


def _mask_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    masked = {}
    for key, value in data.items():
        if isinstance(value, dict):
            masked[key] = _mask_dict(value)
        elif isinstance(value, list):
            masked[key] = [_mask_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            masked[key] = "***" if key.lower() in SENSITIVE_KEYS else value
    return masked


class ApiLogMiddleware(MiddlewareMixin):
    """
    Registra cada request/response en ApiLog. Limita el tamaño de body
    y enmascara campos sensibles básicos.
    """

    MAX_BODY_LEN = 2000

    def process_response(self, request, response):
        try:
            user = getattr(request, "user", None)
            body_text = ""
            if request.method in ("POST", "PUT", "PATCH"):
                try:
                    payload = request.body.decode("utf-8")
                    # si es JSON, enmascara campos sensibles
                    try:
                        parsed = json.loads(payload)
                        masked = _mask_dict(parsed) if isinstance(parsed, dict) else parsed
                        body_text = json.dumps(masked, ensure_ascii=False)
                    except Exception:
                        body_text = payload
                except Exception:
                    body_text = ""

            ApiLog.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                ip=self._get_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:400],
                body=body_text[: self.MAX_BODY_LEN],
                created_at=now(),
            )
        except Exception:
            logger.exception("No se pudo registrar ApiLog")
        return response

    def _get_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
