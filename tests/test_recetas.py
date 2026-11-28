"""Pruebas de recetas y detalle de receta (RF7)."""
from datetime import date

import pytest

from sistema_rural import reportes
from sistema_rural.controlador import ControladorSistema
from sistema_rural.excepciones import (ErrorSistemaRural, MedicamentoNoEncontradoError, PermisoDenegadoError,
                                       RecetaInvalidaError, StockInsuficienteError)
from sistema_rural.fabricas import PersonalFactory
from sistema_rural.modelos import DetalleReceta, Paciente, Receta
from sistema_rural.registro import RegistroCentral
from sistema_rural.seguridad import descifrar_texto, generar_clave


def _escenario():
    reg = RegistroCentral()
    medico = PersonalFactory.crear("medico", "00000001", "Rosa", "Salazar Vega", "CMP-00001")
    paciente = Paciente("00000002", "Juan", "Pérez Díaz", date(1985, 3, 14))
    reg.registrar_personal(medico)
    reg.registrar_paciente(paciente)
    reg.agregar_medicamento("Paracetamol 500 mg", 30, 10)
    reg.agregar_medicamento("Ibuprofeno 400 mg", 20, 5)
    return reg, medico, paciente


def test_emitir_receta_descuenta_stock_y_publica_evento():
    reg, medico, paciente = _escenario()
    avisos = []
    reg.eventos.suscribir("receta_emitida", lambda receta: avisos.append(receta.id))
    receta = reg.emitir_receta(paciente, medico, [("Paracetamol 500 mg", 4, "1 tableta cada 8 horas"),
                                                  ("ibuprofeno 400 mg", 6, "1 tableta cada 12 horas")])
    assert receta.total_unidades() == 10 and len(receta.detalles) == 2
    assert reg.inventario.obtener("Paracetamol 500 mg").stock == 26
    assert reg.inventario.obtener("Ibuprofeno 400 mg").stock == 14
    assert reg.recetas == (receta,) and avisos == [1]


def test_enfermero_no_puede_emitir_recetas():
    reg, _, paciente = _escenario()
    enfermero = PersonalFactory.crear("enfermero", "00000009", "Luis", "Rojas Cruz", "CEP-00001")
    with pytest.raises(PermisoDenegadoError):
        reg.emitir_receta(paciente, enfermero, [("Paracetamol 500 mg", 1, "1 tableta")])
    assert reg.recetas == ()


def test_receta_es_todo_o_nada_si_falta_stock():
    reg, medico, paciente = _escenario()
    with pytest.raises(StockInsuficienteError):
        reg.emitir_receta(paciente, medico, [("Paracetamol 500 mg", 5, "1 tableta"),
                                             ("Ibuprofeno 400 mg", 99, "1 tableta")])
    assert reg.inventario.obtener("Paracetamol 500 mg").stock == 30     # no se descontó nada
    assert reg.recetas == ()


def test_receta_invalida_sin_detalles_repetidos_o_inexistentes():
    reg, medico, paciente = _escenario()
    with pytest.raises(RecetaInvalidaError):
        Receta(1, paciente, medico, None, [])
    repetido = DetalleReceta("Paracetamol 500 mg", 1, "1 tableta")
    with pytest.raises(RecetaInvalidaError):
        Receta(1, paciente, medico, None, [repetido, repetido])
    with pytest.raises(MedicamentoNoEncontradoError):
        reg.emitir_receta(paciente, medico, [("Aspirina", 1, "1 tableta")])
    with pytest.raises(ValueError):
        DetalleReceta("Paracetamol 500 mg", 0, "1 tableta")            # cantidad inválida
    with pytest.raises(ValueError):
        DetalleReceta("Paracetamol 500 mg", 2, "##")                   # indicaciones inválidas


def test_reportes_de_recetas_funcionales_y_sin_dni_completo():
    reg, medico, paciente = _escenario()
    reg.emitir_receta(paciente, medico, [("Paracetamol 500 mg", 4, "1 tableta")])
    reg.emitir_receta(paciente, medico, [("Paracetamol 500 mg", 2, "1 tableta"), ("Ibuprofeno 400 mg", 3, "1 tableta")])
    assert reportes.unidades_recetadas(reg.recetas) == {"Paracetamol 500 mg": 6, "Ibuprofeno 400 mg": 3}
    texto = " ".join(reportes.resumen_recetas(reg.recetas))
    assert "****0002" in texto and "00000002" not in texto and "Paracetamol 500 mg x4" in texto


def test_eliminar_paciente_elimina_sus_recetas():
    reg, medico, paciente = _escenario()
    reg.emitir_receta(paciente, medico, [("Paracetamol 500 mg", 4, "1 tableta")])
    reg.eliminar_paciente(paciente)
    assert reg.recetas == ()


def test_exportacion_cifrada_incluye_recetas_sin_dni_completo(tmp_path):
    reg, medico, paciente = _escenario()
    reg.emitir_receta(paciente, medico, [("Ibuprofeno 400 mg", 3, "1 tableta cada 8 horas")])
    clave, ruta = generar_clave(), tmp_path / "respaldo.bin"
    reg.exportar_cifrado(str(ruta), clave)
    assert b"Ibuprofeno" not in ruta.read_bytes()                       # en disco no se lee nada
    texto = descifrar_texto(ruta.read_bytes(), clave)
    assert "Ibuprofeno 400 mg" in texto and "00000002" not in texto


def test_controlador_prepara_lineas_emite_y_muestra_el_detalle():
    ctrl = ControladorSistema()
    ctrl.cargar_demo()                                                  # trae una receta de ejemplo
    assert len(ctrl.filas_recetas()) == 1
    assert [f[0] for f in ctrl.filas_detalle_receta(1)] == ["Ibuprofeno 400 mg", "Paracetamol 500 mg"]
    paciente, medico = ctrl.opciones_pacientes()[1][1], ctrl.opciones_personal()[0][1]
    for mala in [("", "2", "1 tableta"), ("Ibuprofeno 400 mg", "abc", "1 tableta"), ("Ibuprofeno 400 mg", "2", "")]:
        with pytest.raises(ErrorSistemaRural):
            ctrl.preparar_linea_receta(*mala)
    linea = ctrl.preparar_linea_receta("Ibuprofeno 400 mg", " 2 ", "1 tableta cada 12 horas")
    receta = ctrl.emitir_receta(paciente, medico, [linea])
    assert receta.id == 2 and ctrl.filas_recetas()[0][0] == 2           # la más reciente primero
    with pytest.raises(ErrorSistemaRural):
        ctrl.emitir_receta(paciente, medico, [])
    with pytest.raises(ErrorSistemaRural):
        ctrl.filas_detalle_receta(99)
    assert "RECETAS EMITIDAS: 2" in ctrl.texto_reporte()