"""Protección de datos personales (Ley N.° 29733)."""
import hashlib
import hmac
import logging
import os
import secrets

from .excepciones import CifradoNoDisponibleError, DniInvalidoError

# Dependencia externa se instala con requirements.txt
try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover
    Fernet = None

registro_log = logging.getLogger(__name__)


def leer_sal(entorno=None) -> bytes:
    """Obtiene la sal secreta del HMAC desde la variable de entorno SISTEMA_RURAL_SAL.

    Si no está configurada se genera una sal aleatoria para esta ejecución: así el código no
    contiene ningún secreto fijo (con una sal conocida, un DNI de 8 dígitos se podría recuperar
    probando los 100 millones de combinaciones). Como los datos viven solo en memoria, una sal
    distinta en cada ejecución no rompe nada; si algún día se persistieran los hashes, la sal
    tendría que fijarse con la variable de entorno.
    """
    entorno = os.environ if entorno is None else entorno
    valor = entorno.get("SISTEMA_RURAL_SAL")
    if valor:
        return valor.encode("utf-8")
    registro_log.warning("SISTEMA_RURAL_SAL no está configurada: se usa una sal aleatoria temporal.")
    return secrets.token_bytes(32)


_SAL = leer_sal()


def validar_dni(dni: str) -> str:
    """Devuelve el DNI si tiene 8 dígitos; si no, lanza DniInvalidoError."""
    if not isinstance(dni, str) or len(dni) != 8 or not dni.isascii() or not dni.isdigit():
        raise DniInvalidoError("El DNI debe tener exactamente 8 dígitos (solo números).")
    if dni == "00000000":
        raise DniInvalidoError("El DNI ingresado no es válido.")
    return dni


def hash_dni(dni: str) -> str:
    """HMAC-SHA256 del DNI: sirve para buscar sin almacenar el dato real."""
    return hmac.new(_SAL, validar_dni(dni).encode(), hashlib.sha256).hexdigest()


def enmascarar_dni(dni: str) -> str:
    """Muestra solo los 4 últimos dígitos"""
    return "****" + validar_dni(dni)[-4:]


def generar_clave() -> bytes:
    """Genera una clave Fernet nueva."""
    _requerir_cifrado()
    return Fernet.generate_key()


def cifrar_texto(texto: str, clave: bytes) -> bytes:
    _requerir_cifrado()
    return Fernet(clave).encrypt(texto.encode("utf-8"))


def descifrar_texto(datos: bytes, clave: bytes) -> str:
    _requerir_cifrado()
    return Fernet(clave).decrypt(datos).decode("utf-8")


def _requerir_cifrado() -> None:
    if Fernet is None:
        raise CifradoNoDisponibleError("Instale 'cryptography' (pip install cryptography).")
