from datetime import date, datetime

from sistema_rural import reportes
from sistema_rural.fabricas import PersonalFactory
from sistema_rural.modelos import Paciente
from sistema_rural.registro import RegistroCentral


def _escenario():
    reg = RegistroCentral()
    medico = PersonalFactory.crear("medico", "00000001", "Rosa", "Vega", "CMP-1")
    reg.registrar_paciente(Paciente("00000002", "Juan", "Pérez", date(1980, 1, 1)))
    reg.registrar_paciente(Paciente("00000003", "Ana", "Cruz", date(2000, 1, 1)))
    reg.programar_cita("00000002", medico, datetime(2026, 11, 3, 9, 0), "Control")
    reg.programar_cita("00000003", medico, datetime(2026, 11, 4, 9, 0), "Fiebre")
    reg.atender_cita(1)
    return reg


def test_citas_por_estado_con_reduce():
    reg = _escenario()
    assert reportes.citas_por_estado(reg.citas) == {"atendida": 1, "programada": 1}


def test_filtrar_citas_del_dia_y_resumen_sin_dni_completo():
    reg = _escenario()
    dia = reportes.citas_del_dia(reg.citas, date(2026, 11, 3))
    assert len(dia) == 1
    linea = reportes.resumen_citas(dia)[0]
    assert "****0002" in linea and "00000002" not in linea


def test_edad_promedio():
    reg = _escenario()
    assert reportes.edad_promedio(reg.pacientes, date(2026, 1, 1)) == 36.0
