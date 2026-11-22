import pytest
from datetime import date

from sistema_rural.excepciones import StockInsuficienteError
from sistema_rural.fabricas import PersonalFactory
from sistema_rural.modelos import Medicamento, Paciente


def test_polimorfismo_y_factory():
    medico = PersonalFactory.crear("medico", "00000001", "Rosa", "Vega", "CMP-1")
    enfermero = PersonalFactory.crear("enfermero", "00000009", "Luis", "Rojas", "CEP-1")
    assert [medico.rol(), enfermero.rol()] == ["Médico", "Enfermero"]
    assert medico.puede_prescribir() and not enfermero.puede_prescribir()


def test_encapsulamiento_valida_nombres_y_protege_diagnosticos():
    p = Paciente("00000002", "Juan", "Pérez", date(1990, 1, 1))
    with pytest.raises(ValueError):
        p.nombres = "   "
    p.agregar_diagnostico("Control")
    assert isinstance(p.diagnosticos, tuple)


def test_stock_insuficiente():
    m = Medicamento("Ibuprofeno", stock=5)
    with pytest.raises(StockInsuficienteError):
        m.retirar(6)


def test_factory_rechaza_tipo_desconocido_y_admite_tipos_nuevos():
    import pytest
    from sistema_rural.excepciones import TipoPersonalInvalidoError
    from sistema_rural.fabricas import PersonalFactory
    from sistema_rural.modelos import Medico
    with pytest.raises(TipoPersonalInvalidoError):
        PersonalFactory.crear("brujo", "00000001", "A", "B", "X")
    PersonalFactory.registrar_tipo("obstetra", Medico)
    assert PersonalFactory.crear("obstetra", "00000005", "Eva", "Ríos", "COP-1").rol() == "Médico"


def test_paciente_valida_fecha_y_diagnostico():
    import pytest
    from datetime import date, timedelta
    from sistema_rural.modelos import Paciente
    with pytest.raises(ValueError):
        Paciente("00000002", "Ana", "Torres", date.today() + timedelta(days=1))
    p = Paciente("00000002", "Ana", "Torres", date(1990, 1, 1))
    with pytest.raises(ValueError):
        p.agregar_diagnostico("  ")
