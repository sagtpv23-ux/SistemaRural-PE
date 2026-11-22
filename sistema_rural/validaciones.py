"""Validación de datos de entrada."""
from datetime import date, datetime

LARGO_NOMBRE = (2, 50)
LARGO_MOTIVO = (3, 100)
LARGO_DIAGNOSTICO = (3, 200)
MAX_CANTIDAD = 100000
MAX_EDAD_ANIOS = 120


def limpiar_espacios(texto):
    """Quita espacios al inicio y al final y deja un solo espacio entre palabras."""
    return " ".join(texto.split())


def _exigir_texto(valor, campo):
    if not isinstance(valor, str):
        raise ValueError(f"{campo} debe ser un texto.")


def _revisar_largo(limpio, campo, minimo, maximo):
    if len(limpio) < minimo or len(limpio) > maximo:
        raise ValueError(f"{campo} debe tener entre {minimo} y {maximo} caracteres.")


def validar_nombre_persona(valor, campo):
    """Nombres o apellidos: solo letras, espacios, guion o apóstrofe."""
    _exigir_texto(valor, campo)
    limpio = limpiar_espacios(valor)
    _revisar_largo(limpio, campo, *LARGO_NOMBRE)
    for caracter in limpio:
        if not (caracter.isalpha() or caracter in " -'’"):
            raise ValueError(f"{campo} solo admite letras, espacios, guion o apóstrofe "
                             "(sin números ni símbolos).")
    if sum(1 for c in limpio if c.isalpha()) < 2:
        raise ValueError(f"{campo} debe tener al menos 2 letras.")
    return limpio


def validar_texto_libre(valor, campo, minimo, maximo):
    """Texto libre: sin caracteres de control y con al menos una letra o número."""
    _exigir_texto(valor, campo)
    limpio = limpiar_espacios(valor)
    _revisar_largo(limpio, campo, minimo, maximo)
    if not all(c.isprintable() for c in limpio):
        raise ValueError(f"{campo} contiene caracteres no permitidos.")
    if not any(c.isalnum() for c in limpio):
        raise ValueError(f"{campo} debe incluir letras o números.")
    return limpio


def validar_colegiatura(valor):
    """Código de colegiatura: letras, números y guion."""
    _exigir_texto(valor, "La colegiatura")
    limpio = valor.strip().upper()
    _revisar_largo(limpio, "La colegiatura", 3, 20)
    if not limpio.isascii() or not all(c.isalnum() or c == "-" for c in limpio):
        raise ValueError("La colegiatura solo puede tener letras, números y guion.")
    if not any(c.isdigit() for c in limpio):
        raise ValueError("La colegiatura debe incluir al menos un número.")
    return limpio


def validar_nombre_medicamento(valor):
    """Medicamento: letras, números, espacios y los signos."""
    _exigir_texto(valor, "El nombre del medicamento")
    limpio = limpiar_espacios(valor)
    _revisar_largo(limpio, "El nombre del medicamento", 2, 60)
    if not all(c.isalnum() or c in " -.,/()%" for c in limpio):
        raise ValueError("El nombre del medicamento tiene caracteres no permitidos.")
    if not any(c.isalpha() for c in limpio):
        raise ValueError("El nombre del medicamento debe incluir letras.")
    return limpio


def validar_indicaciones(valor):
    """Indicaciones de un medicamento recetado."""
    return validar_texto_libre(valor, "Las indicaciones", 3, 100)


def validar_entero(valor, campo, minimo, maximo=MAX_CANTIDAD):
    """Número entero dentro de un rango."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"{campo} debe ser un número entero.")
    if valor < minimo or valor > maximo:
        raise ValueError(f"{campo} debe estar entre {minimo} y {maximo}.")
    return valor


def validar_fecha_nacimiento(valor, hoy=None):
    """Fecha de nacimiento real: no futura y con una edad máxima de 120 años."""
    if not isinstance(valor, date) or isinstance(valor, datetime):
        raise ValueError("La fecha de nacimiento no es válida.")
    hoy = hoy or date.today()
    if valor > hoy:
        raise ValueError("La fecha de nacimiento no puede ser futura.")
    if hoy.year - valor.year > MAX_EDAD_ANIOS:
        raise ValueError(f"La fecha de nacimiento supera los {MAX_EDAD_ANIOS} años de edad.")
    return valor


def permitir_dni(texto):
    """Solo dígitos del 0 al 9 y máximo 8: al completar 8 dígitos ya no deja escribir más."""
    return texto == "" or (texto.isascii() and texto.isdigit() and len(texto) <= 8)


def permitir_nombre(texto):
    """Nombres y apellidos: solo letras, espacios, guion o apóstrofe (no deja escribir números)."""
    return len(texto) <= LARGO_NOMBRE[1] and all(c.isalpha() or c in " -'’" for c in texto)


def permitir_numero(texto, max_digitos=6):
    """Cantidades: solo dígitos del 0 al 9, con un máximo de dígitos."""
    return texto == "" or (texto.isascii() and texto.isdigit() and len(texto) <= max_digitos)


def permitir_fecha(texto):
    """Fecha DD/MM/AAAA: solo dígitos y barra, máximo 10 caracteres."""
    return len(texto) <= 10 and all(c in "0123456789/" for c in texto)


def permitir_hora(texto):
    """Hora HH:MM: solo dígitos y dos puntos, máximo 5 caracteres."""
    return len(texto) <= 5 and all(c in "0123456789:" for c in texto)


def permitir_largo(texto, maximo):
    """Texto libre con un máximo de caracteres."""
    return len(texto) <= maximo


def permitir_nombre_medicamento(texto):
    """Medicamento: letras, números, espacios y - . , / ( ) %; máximo 60 caracteres."""
    return len(texto) <= 60 and all(c.isalnum() or c in " -.,/()%" for c in texto)
