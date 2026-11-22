"""Protección de datos personales (Ley N.° 29733)."""
import hashlib
import hmac
import os

from .excepciones import CifradoNoDisponibleError, DniInvalidoError

# Dependencia externa se instala con requirements.txt
try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover
    Fernet = None

# La sal se lee del entorno; el valor por defecto es solo para demostración.
_SAL = os.environ.get("SISTEMA_RURAL_SAL", "sal-demo-cambiar-en-produccion").encode()


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
