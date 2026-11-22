import pytest
from datetime import date, datetime

from sistema_rural.excepciones import CitaConflictoError, PacienteDuplicadoError
from sistema_rural.fabricas import PersonalFactory
from sistema_rural.modelos import Paciente
from sistema_rural.registro import RegistroCentral


def _paciente(dni="00000002"):
    return Paciente(dni, "Juan", "Pérez", date(1990, 1, 1))


def test_singleton_devuelve_siempre_la_misma_instancia():
    assert RegistroCentral() is RegistroCentral()


def test_no_permite_paciente_duplicado():
    reg = RegistroCentral()
    reg.registrar_paciente(_paciente())
    with pytest.raises(PacienteDuplicadoError):
        reg.registrar_paciente(_paciente())


def test_conflicto_de_citas_del_mismo_personal():
    reg = RegistroCentral()
    medico = PersonalFactory.crear("medico", "00000001", "Rosa", "Vega", "CMP-1")
    reg.registrar_paciente(_paciente())
    hora = datetime(2026, 11, 3, 9, 0)
    reg.programar_cita("00000002", medico, hora, "Control")
    with pytest.raises(CitaConflictoError):
        reg.programar_cita("00000002", medico, hora, "Otra")


def test_evento_stock_bajo_notifica_al_oyente():
    reg = RegistroCentral()
    alertas = []
    reg.eventos.suscribir("stock_bajo", lambda medicamento, stock: alertas.append(medicamento))
    reg.inventario.agregar("Paracetamol", stock=12, stock_minimo=10)
    reg.dispensar_medicamento("Paracetamol", 5)
    assert alertas == ["Paracetamol"]


def test_exportacion_cifrada_no_contiene_datos_legibles(tmp_path):
    pytest.importorskip("cryptography")
    from sistema_rural.seguridad import descifrar_texto, generar_clave
    reg = RegistroCentral()
    reg.registrar_paciente(_paciente())
    clave = generar_clave()
    ruta = tmp_path / "datos.bin"
    reg.exportar_cifrado(str(ruta), clave)
    crudo = ruta.read_bytes()
    assert b"Juan" not in crudo and b"00000002" not in crudo
    assert "****0002" in descifrar_texto(crudo, clave)


def test_enfermero_no_puede_dispensar_pero_medico_si():
    import pytest
    from sistema_rural.excepciones import PermisoDenegadoError
    from sistema_rural.fabricas import PersonalFactory
    from sistema_rural.registro import RegistroCentral
    reg = RegistroCentral()
    reg.inventario.agregar("Paracetamol", stock=20, stock_minimo=5)
    enfermero = PersonalFactory.crear("enfermero", "00000009", "Luis", "Rojas", "CEP-1")
    medico = PersonalFactory.crear("medico", "00000001", "Rosa", "Salazar", "CMP-1")
    with pytest.raises(PermisoDenegadoError):
        reg.dispensar_medicamento("Paracetamol", 1, enfermero)
    reg.dispensar_medicamento("Paracetamol", 1, medico)
    assert reg.inventario.obtener("Paracetamol").stock == 19


def test_manejador_defectuoso_no_interrumpe_a_los_demas():
    from sistema_rural.eventos import BusEventos
    recibidos = []
    bus = BusEventos()
    bus.suscribir("e", lambda **d: 1 / 0)
    bus.suscribir("e", lambda **d: recibidos.append(d))
    assert bus.publicar("e", x=1) == 1 and recibidos == [{"x": 1}]
