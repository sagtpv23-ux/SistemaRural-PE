"""Patrón Factory: es una fábrica que crea el objeto correcto según el tipo pedido.
De esa manera el resto del programa no necesita saber qué clase concreta crear (Medico o Enfermero).
"""
from .excepciones import TipoPersonalInvalidoError
from .modelos import Enfermero, Medico


class PersonalFactory:
   
    _TIPOS = {"medico": Medico, "enfermero": Enfermero}

    @classmethod   
    def registrar_tipo(cls, tipo, clase):
        """Agrega un tipo nuevo (p. ej. 'obstetra') sin modificar a los clientes (abierto/cerrado)."""
        cls._TIPOS[tipo.strip().lower()] = clase

    @classmethod
    def crear(cls, tipo, dni, nombres, apellidos, colegiatura):
        clase = cls._TIPOS.get(str(tipo).strip().lower())
        if clase is None:
            raise TipoPersonalInvalidoError(f"Tipo de personal desconocido: {tipo}")
        return clase(dni, nombres, apellidos, colegiatura)
