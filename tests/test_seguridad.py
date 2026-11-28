import pytest
from datetime import date

from sistema_rural.excepciones import DniInvalidoError
from sistema_rural.modelos import Paciente
from sistema_rural.seguridad import enmascarar_dni, hash_dni


def test_dni_invalido_lanza_excepcion():
    with pytest.raises(DniInvalidoError):
        hash_dni("123")


def test_dni_no_queda_en_texto_plano():
    p = Paciente("00000002", "Juan", "Pérez", date(1990, 1, 1))
    assert "00000002" not in repr(p)
    assert "00000002" not in p.dni_hash
    assert p.dni_enmascarado == "****0002"
    assert enmascarar_dni("00000002") == "****0002"


def test_cifrado_de_ida_y_vuelta_y_clave_incorrecta():
    import pytest
    from cryptography.fernet import InvalidToken
    from sistema_rural.seguridad import cifrar_texto, descifrar_texto, generar_clave
    clave = generar_clave()
    token = cifrar_texto("dato sensible", clave)
    assert b"dato sensible" not in token
    assert descifrar_texto(token, clave) == "dato sensible"
    with pytest.raises(InvalidToken):
        descifrar_texto(token, generar_clave())


def test_la_sal_viene_del_entorno_o_es_aleatoria():
    """Sin variable de entorno no hay secreto fijo en el código: cada ejecución usa una sal distinta."""
    from sistema_rural.seguridad import leer_sal
    assert leer_sal({"SISTEMA_RURAL_SAL": "mi-sal-secreta"}) == b"mi-sal-secreta"
    primera, segunda = leer_sal({}), leer_sal({})
    assert len(primera) == 32 and primera != segunda
    assert b"sal-demo" not in primera


def test_hash_del_dni_depende_de_la_sal(monkeypatch):
    """El mismo DNI con otra sal produce otro hash: sin la sal no se puede reconstruir el DNI."""
    from sistema_rural import seguridad
    monkeypatch.setattr(seguridad, "_SAL", b"sal-uno")
    uno = seguridad.hash_dni("00000002")
    monkeypatch.setattr(seguridad, "_SAL", b"sal-dos")
    assert uno != seguridad.hash_dni("00000002") and len(uno) == 64
