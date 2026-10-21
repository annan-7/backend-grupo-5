from datetime import UTC, datetime

from app.core.exceptions import BusinessRuleError


def validate_text(value: str, field_name: str) -> str:
    """Valida que un texto no sea vacío y lo devuelve limpio (strip)."""
    if value is None or not str(value).strip():
        raise BusinessRuleError(f"The {field_name} is required")
    return str(value).strip()


def utc_now() -> datetime:
    """Timestamp actual con zona horaria UTC.

    Se usa en todo el dominio en lugar de ``datetime.now()`` naive: mezclar
    datetimes naive y aware en comparaciones lanza ``TypeError`` (bug 1.1
    de la revisión).
    """
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Normaliza un datetime a UTC.

    - Naive: se interpreta como UTC (se adjunta ``timezone.utc``).
    - Aware: se convierte a UTC.

    Garantiza que TODOS los datetimes del sistema sean comparables entre sí.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def validate_rut(rut: str) -> str:
    """Valida formato y dígito verificador (módulo 11) de un RUT chileno.

    Formato esperado: ``12345678-5`` (7-8 dígitos, guión, DV 0-9 o K).
    """
    cleaned = (rut or "").strip().upper()
    if "-" not in cleaned:
        raise BusinessRuleError("RUT must contain a hyphen (-), e.g. 12345678-5")
    body, _, dv = cleaned.partition("-")
    if not body.isdigit() or not 7 <= len(body) <= 8:
        raise BusinessRuleError("RUT body must have 7 or 8 digits")
    if len(dv) != 1 or dv not in "0123456789K":
        raise BusinessRuleError("Invalid RUT verification digit")
    if dv != compute_rut_dv(body):
        raise BusinessRuleError(f"Invalid RUT: verification digit should be {compute_rut_dv(body)}")
    return cleaned


def compute_rut_dv(body: str) -> str:
    """Calcula el dígito verificador de un RUT (algoritmo módulo 11, factores 2..7)."""
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    remainder = 11 - (total % 11)
    if remainder == 11:
        return "0"
    if remainder == 10:
        return "K"
    return str(remainder)


def validate_email(email: str) -> str:
    """Validación básica de email (la validación fuerte la hace ``EmailStr`` en el schema)."""
    cleaned = (email or "").strip().lower()
    if cleaned.count("@") != 1:
        raise BusinessRuleError("Email must have only one @")
    local_part, _, domain = cleaned.partition("@")
    if not local_part or not domain or "." not in domain:
        raise BusinessRuleError("Invalid email format")
    if domain.startswith(".") or domain.endswith("."):
        raise BusinessRuleError("Invalid email domain")
    return cleaned
