"""Pruebas de la ventana Tkinter."""
from datetime import date, timedelta
from unittest import mock

import pytest

tk = pytest.importorskip("tkinter")


@pytest.fixture
def ventana():
    from sistema_rural.ui_tkinter import VentanaPrincipal
    try:
        v = VentanaPrincipal()
    except tk.TclError:
        pytest.skip("No hay pantalla disponible para abrir la ventana")
    v.withdraw()                                 
    yield v
    v.destroy()


def _escribir(entrada, texto):
    entrada.delete(0, "end")
    entrada.insert(0, texto)


@pytest.fixture
def avisos():
    """Reemplaza los cuadros de diálogo (que bloquearían la prueba) y registra lo que mostrarían."""
    with mock.patch("tkinter.messagebox.showinfo") as info, mock.patch("tkinter.messagebox.showerror") as error, \
            mock.patch("tkinter.messagebox.showwarning") as aviso, mock.patch("tkinter.messagebox.askyesno", return_value=True):
        yield info, error, aviso


def test_registrar_paciente_muestra_alerta_de_exito(ventana, avisos):
    info, error, _ = avisos
    for etiqueta, texto in (("DNI (8 dígitos)", "00000010"), ("Nombres", "Ana"), ("Apellidos", "Cruz Rojas"),
                            ("Nacimiento (DD/MM/AAAA)", "14/03/1990")):
        _escribir(ventana._pac[etiqueta], texto)
    ventana._al_registrar_paciente()
    info.assert_called_once()
    assert "Ana Cruz Rojas se registró correctamente" in info.call_args[0][1]
    assert ventana._arbol_pac.get_children() and not error.called


def test_fecha_con_formato_antiguo_muestra_error(ventana, avisos):
    info, error, _ = avisos
    for etiqueta, texto in (("DNI (8 dígitos)", "00000011"), ("Nombres", "Luis"), ("Apellidos", "Rojas"),
                            ("Nacimiento (DD/MM/AAAA)", "1990-03-1")):
        _escribir(ventana._pac[etiqueta], texto)
    ventana._al_registrar_paciente()
    assert "DD/MM/AAAA" in error.call_args[0][1] and not info.called


def test_flujo_de_cita_y_receta_con_alertas(ventana, avisos):
    info, error, _ = avisos
    ventana._al_cargar_demo()                       # carga datos ficticios y avisa
    assert "Datos de demostración" in info.call_args[0][1]
    # cita
    ventana._cb_pac.current(1)
    ventana._cb_per.current(0)
    _escribir(ventana._cita_fecha, (date.today() + timedelta(days=3)).strftime("%d/%m/%Y"))
    _escribir(ventana._cita_hora, "11:00")
    _escribir(ventana._cita_motivo, "Control general")
    ventana._al_programar_cita()
    assert "se programó correctamente" in info.call_args[0][1]
    # receta con dos medicamentos
    ventana._cb_rec_pac.current(1)
    ventana._cb_rec_med.current(0)
    for medicamento, cantidad in (("Ibuprofeno 400 mg", "4"), ("Paracetamol 500 mg", "2")):
        ventana._cb_rec_medic.set(medicamento)
        _escribir(ventana._rec_cantidad, cantidad)
        _escribir(ventana._rec_indic, "1 tableta cada 8 horas")
        ventana._al_agregar_linea()
    assert len(ventana._arbol_borrador.get_children()) == 2
    ventana._al_emitir_receta()
    assert "La receta N.° 2 se emitió correctamente" in info.call_args[0][1]
    assert not ventana._borrador and len(ventana._arbol_recetas.get_children()) == 2
    # detalle al seleccionar
    primera = ventana._arbol_recetas.get_children()[0]
    ventana._arbol_recetas.selection_set(primera)
    ventana.update()
    assert len(ventana._arbol_detalle.get_children()) == 2
    assert not error.called


def test_receta_por_enfermero_muestra_error_y_no_emite(ventana, avisos):
    _, error, _ = avisos
    ventana._al_cargar_demo()
    ventana._cb_rec_pac.current(0)
    ventana._cb_rec_med.current(1)                  # el enfermero
    ventana._cb_rec_medic.set("Ibuprofeno 400 mg")
    _escribir(ventana._rec_cantidad, "1")
    _escribir(ventana._rec_indic, "1 tableta")
    ventana._al_agregar_linea()
    ventana._al_emitir_receta()
    assert "no puede emitir recetas" in error.call_args[0][1]
    assert len(ventana._arbol_recetas.get_children()) == 1       # solo la receta de la demo
