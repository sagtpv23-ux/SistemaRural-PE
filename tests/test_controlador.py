"""Pruebas del ControladorSistema (RF7).

Verifican que el controlador valide los datos de los formularios, proteja el DNI y
conecte la interfaz con el dominio sin necesidad de abrir la ventana.
"""
import pytest
from datetime import date, timedelta

from sistema_rural.controlador import ControladorSistema
from sistema_rural.excepciones import ErrorSistemaRural


def _controlador():
    ctrl = ControladorSistema()
    ctrl.cargar_demo()
    return ctrl


def test_registrar_paciente_rechaza_fecha_invalida_o_futura():
    ctrl = ControladorSistema()
    with pytest.raises(ErrorSistemaRural):
        ctrl.registrar_paciente("00000005", "Ana", "Cruz", "14/03/1990")
    with pytest.raises(ErrorSistemaRural):
        ctrl.registrar_paciente("00000005", "Ana", "Cruz", "2999-01-01")


def test_filas_pacientes_no_exponen_el_dni_completo():
    ctrl = _controlador()
    filas = ctrl.filas_pacientes()
    assert len(filas) == 3 and all(f[0].startswith("****") for f in filas)
    assert ctrl.filas_pacientes("00000002")[0][1] == "Juan Pérez Díaz"


def test_programar_cita_desde_formulario_y_validar_hora():
    ctrl = _controlador()
    (_, paciente), (_, personal) = ctrl.opciones_pacientes()[0], ctrl.opciones_personal()[0]
    fecha = (date.today() + timedelta(days=30)).isoformat()      # siempre una fecha futura
    ctrl.programar_cita(paciente, personal, fecha, "08:00", "Control")
    assert any(f[1] == f"{fecha} 08:00" and f[4] == "programada" for f in ctrl.filas_citas())
    with pytest.raises(ErrorSistemaRural):
        ctrl.programar_cita(paciente, personal, fecha, "8am", "Control")


def test_dispensar_valida_cantidad_y_dispara_alerta():
    ctrl = _controlador()
    alertas = []
    ctrl.registro.eventos.suscribir("stock_bajo", lambda medicamento, stock: alertas.append(medicamento))
    with pytest.raises(ErrorSistemaRural):
        ctrl.dispensar("Ibuprofeno 400 mg", "abc")
    ctrl.dispensar("Ibuprofeno 400 mg", "30")        # 40 -> 10 (<= mínimo 15)
    assert alertas == ["Ibuprofeno 400 mg"]
    ctrl.reponer("Ibuprofeno 400 mg", "50")
    assert dict((f[0], f[3]) for f in ctrl.filas_inventario())["Ibuprofeno 400 mg"] == "Normal"


def test_cargar_demo_solo_con_registro_vacio():
    ctrl = _controlador()
    with pytest.raises(ErrorSistemaRural):
        ctrl.cargar_demo()


def test_reporte_en_texto_no_contiene_dni_completo():
    texto = _controlador().texto_reporte()
    assert "****0002" in texto
    assert "00000002" not in texto and "Amoxicilina" in texto


def test_exportar_respaldo_cifrado(tmp_path):
    pytest.importorskip("cryptography")
    ctrl = _controlador()
    ruta = tmp_path / "respaldo.bin"
    clave = ctrl.exportar_respaldo(str(ruta))
    assert clave and b"Juan" not in ruta.read_bytes()


def test_eliminar_paciente_sin_citas_programadas():
    ctrl = _controlador()
    id_juan = ctrl.filas_pacientes("00000002", con_id=True)[0][0]
    ctrl.cancelar_cita(1)                       # cita 1 es de Juan
    eliminadas = ctrl.eliminar_paciente(id_juan)
    assert eliminadas == 1
    assert all(f[1] != "Juan Pérez Díaz" for f in ctrl.filas_pacientes())
    assert all("Juan" not in f[2] for f in ctrl.filas_citas())


def test_no_elimina_paciente_con_cita_programada():
    ctrl = _controlador()
    id_juan = ctrl.filas_pacientes("00000002", con_id=True)[0][0]
    with pytest.raises(ErrorSistemaRural):
        ctrl.eliminar_paciente(id_juan)
    assert len(ctrl.filas_pacientes()) == 3


def test_eliminar_cita():
    ctrl = _controlador()
    antes = len(ctrl.filas_citas())
    ctrl.eliminar_cita(1)
    assert len(ctrl.filas_citas()) == antes - 1


def test_registrar_personal_desde_el_formulario():
    ctrl = ControladorSistema()                      # sin datos de demostración
    ctrl.registrar_personal("Médico", "00000011", "Rosa", "Salazar Vega", "CMP-00011")
    assert ctrl.filas_personal() == [("****0011", "Rosa Salazar Vega", "Médico", "CMP-00011")]
    assert len(ctrl.opciones_personal()) == 1
    casos = [("Médico", "00000011", "Rosa", "Salazar", "CMP-00011"),      # DNI repetido
             ("", "00000012", "Rosa", "Salazar", "CMP-00012"),            # sin tipo
             ("Enfermero", "00000013", "Luis3", "Rojas", "CEP-00013"),    # número en el nombre
             ("Enfermero", "00000013", "Luis", "Rojas", "!!!"),           # colegiatura inválida
             ("Enfermero", "1234", "Luis", "Rojas", "CEP-00013")]         # DNI incompleto
    for caso in casos:
        with pytest.raises(ErrorSistemaRural):
            ctrl.registrar_personal(*caso)
    assert len(ctrl.filas_personal()) == 1


def test_agregar_medicamento_desde_el_formulario():
    ctrl = ControladorSistema()
    ctrl.agregar_medicamento("Paracetamol 500 mg", "20", "5")
    ctrl.agregar_medicamento("Suero oral", "0", "0")                 # stock cero es válido
    assert [f[0] for f in ctrl.filas_inventario()] == ["Paracetamol 500 mg", "Suero oral"]
    for caso in [("paracetamol 500 MG", "10", "5"), ("###", "10", "5"), ("Ibuprofeno", "3.5", "5"),
                 ("Ibuprofeno", "10", "-1"), ("Ibuprofeno", "", "5")]:
        with pytest.raises(ErrorSistemaRural):
            ctrl.agregar_medicamento(*caso)
    assert len(ctrl.filas_inventario()) == 2


def test_flujo_completo_sin_datos_de_demostracion():
    ctrl = ControladorSistema()
    ctrl.registrar_personal("Médico", "00000011", "Rosa", "Salazar Vega", "CMP-00011")
    ctrl.registrar_paciente("00000020", "Carlos", "Mendoza Ruiz", "1992-05-14")
    ctrl.agregar_medicamento("Amoxicilina 500 mg", "30", "10")
    paciente, personal = ctrl.opciones_pacientes()[0][1], ctrl.opciones_personal()[0][1]
    fecha = (date.today() + timedelta(days=5)).isoformat()
    ctrl.programar_cita(paciente, personal, fecha, "10:00", "Control general")
    ctrl.dispensar("Amoxicilina 500 mg", "5", personal)
    assert ctrl.filas_inventario()[0][1] == 25
    assert ctrl.filas_citas()[0][4] == "programada"


def test_aviso_de_cambios_sin_guardar_hasta_exportar_respaldo(tmp_path):
    ctrl = ControladorSistema()
    assert not ctrl.hay_cambios_sin_guardar            # recién abierto: nada por guardar
    ctrl.registrar_paciente("00000005", "Ana", "Cruz", "1990-03-14")
    assert ctrl.hay_cambios_sin_guardar                # hay un paciente sin respaldar
    ctrl.exportar_respaldo(str(tmp_path / "respaldo.bin"))
    assert not ctrl.hay_cambios_sin_guardar            # tras guardar, se puede cerrar sin aviso
    ctrl.registrar_paciente("00000006", "Luis", "Rojas", "1985-01-20")
    assert ctrl.hay_cambios_sin_guardar                # cualquier cambio nuevo vuelve a avisar
