import pytest
from datetime import date, timedelta

from sistema_rural.controlador import ControladorSistema
from sistema_rural.excepciones import DniInvalidoError, ErrorSistemaRural
from sistema_rural.fabricas import PersonalFactory
from sistema_rural.modelos import Medicamento, Paciente
from sistema_rural.seguridad import hash_dni


def _paciente(nombres="Juan", apellidos="Pérez"):
    return Paciente("00000002", nombres, apellidos, date(1990, 1, 1))

# Verifica que el sistema rechace nombres y apellidos inválidos.
def test_nombres_y_apellidos_rechazan_numeros_y_simbolos():
    for malo in ["Juan3", "123", "J@n", "Ana_Cruz", "<script>", "A", "--", "x" * 60, ""]:
        with pytest.raises(ValueError):
            _paciente(nombres=malo)
        with pytest.raises(ValueError):
            _paciente(apellidos=malo)


def test_nombres_validos_se_aceptan_y_se_limpian():
    assert _paciente(nombres="  María   José ").nombres == "María José"
    for bueno in ["Ñusta", "O'Connor", "Ana-Lucía", "José Luis"]:
        assert _paciente(nombres=bueno).nombres == bueno


def test_dni_rechaza_letras_otros_alfabetos_y_ceros():
    for malo in ["1234567a", "²2345678", "１２３４５６７８", "00000000", "1234567", "123456789", ""]:
        with pytest.raises(DniInvalidoError):
            hash_dni(malo)


def test_fecha_de_nacimiento_real():
    with pytest.raises(ValueError):
        Paciente("00000002", "Ana", "Cruz", date(1800, 1, 1))            # más de 120 años
    with pytest.raises(ValueError):
        Paciente("00000002", "Ana", "Cruz", date.today() + timedelta(days=1))
    with pytest.raises(ValueError):
        Paciente("00000002", "Ana", "Cruz", "01/01/2000")                 # texto, no fecha


def test_colegiatura_diagnostico_y_medicamento_validados():
    with pytest.raises(ValueError):
        PersonalFactory.crear("medico", "00000007", "Rosa", "Vega", "!!!")
    with pytest.raises(ValueError):
        _paciente().agregar_diagnostico("x" * 500)
    with pytest.raises(ValueError):
        _paciente().agregar_diagnostico("   ")
    for nombre, stock in [("###", 5), ("", 5), ("Paracetamol", 3.5), ("Paracetamol", True), ("Paracetamol", -1)]:
        with pytest.raises(ValueError):
            Medicamento(nombre, stock, 10)
    assert Medicamento("Paracetamol 500 mg (tabletas)", 20, 5).nombre == "Paracetamol 500 mg (tabletas)"


def test_formularios_rechazan_fechas_horas_y_motivos_invalidos():
    ctrl = ControladorSistema()
    ctrl.cargar_demo()
    paciente, personal = ctrl.opciones_pacientes()[0][1], ctrl.opciones_personal()[0][1]
    futuro = (date.today() + timedelta(days=10)).strftime("%d/%m/%Y")
    casos = [("01/01/2001", "09:00", "Control"),            # en el pasado
             ((date.today() + timedelta(days=400)).strftime("%d/%m/%Y"), "09:00", "Control"),   # muy lejana
             (futuro, "9:5", "Control"), (futuro, "25:00", "Control"),                 # hora mal escrita
             ("20301231", "09:00", "Control"), ("5/1/2030", "09:00", "Control"), ("2030-01-05", "09:00", "Control"),       # fecha sin formato
             (futuro, "09:00", "###"), (futuro, "09:00", ""), (futuro, "09:00", "x" * 200)]
    for fecha, hora, motivo in casos:
        with pytest.raises(ErrorSistemaRural):
            ctrl.programar_cita(paciente, personal, fecha, hora, motivo)
    with pytest.raises(ErrorSistemaRural):
        ctrl.registrar_paciente("00000009", "Ana3", "Cruz", "05/01/2000")
    with pytest.raises(ErrorSistemaRural):
        ctrl.registrar_paciente("00000009", "Ana", "Cruz", "20000105")


def test_cantidades_solo_enteros_positivos_en_rango():
    ctrl = ControladorSistema()
    ctrl.cargar_demo()
    for mala in ["1_0", "-5", "0", "1.5", "abc", "", " ", "１２", "99999999999", "5 0"]:
        with pytest.raises(ErrorSistemaRural):
            ctrl.reponer("Ibuprofeno 400 mg", mala)
    ctrl.reponer("Ibuprofeno 400 mg", " 25 ")


def test_filtro_del_dni_bloquea_letras_y_mas_de_8_digitos():
    from sistema_rural.validaciones import permitir_dni
    assert permitir_dni("") and permitir_dni("1234567") and permitir_dni("12345678")
    assert not permitir_dni("123456789")          # el noveno dígito ya no se puede escribir
    for malo in ["12a", "abc", "12 3", "²", "１２", "-1"]:
        assert not permitir_dni(malo)


def test_filtros_de_nombre_fecha_hora_y_numeros():
    from sistema_rural.validaciones import permitir_fecha, permitir_hora, permitir_nombre, permitir_numero
    assert permitir_nombre("María José") and not permitir_nombre("Ana3") and not permitir_nombre("x" * 51)
    assert permitir_fecha("26/12/20") and not permitir_fecha("2026-12-01") and not permitir_fecha("26/12/20266")
    assert permitir_hora("09:3") and not permitir_hora("9h30") and not permitir_hora("09:300")
    assert permitir_numero("123456") and not permitir_numero("1234567") and not permitir_numero("1.5")
