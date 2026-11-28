"""Prueba de viabilidad: ¿cooperan POO, eventos y funcional en un mismo flujo? (datos ficticios)."""
import logging
import os
import sys
import tempfile
from datetime import date, datetime

from sistema_rural import reportes
from sistema_rural.fabricas import PersonalFactory
from sistema_rural.modelos import Paciente
from sistema_rural.registro import RegistroCentral
from sistema_rural.seguridad import descifrar_texto, generar_clave

logging.basicConfig(stream=sys.stdout, format="  [log] %(message)s", level=logging.WARNING)
reg, avisos = RegistroCentral(), []
reg.eventos.suscribir("receta_emitida", lambda receta: 1 / 0)                       # oyente defectuoso
reg.eventos.suscribir("receta_emitida", lambda receta: avisos.append("receta_emitida"))
reg.eventos.suscribir("stock_bajo", lambda medicamento, stock: avisos.append("stock_bajo"))

medico = PersonalFactory.crear("medico", "00000001", "Rosa", "Salazar Vega", "CMP-00001")
reg.registrar_paciente(Paciente("00000002", "Juan", "Pérez Díaz", date(1985, 3, 14)))
reg.inventario.agregar("Paracetamol 500 mg", stock=14, stock_minimo=10)
reg.programar_cita("00000002", medico, datetime(2026, 11, 3, 9, 0), "Control")
reg.emitir_receta(reg.buscar_paciente("00000002"), medico, [("Paracetamol 500 mg", 6, "1 cada 8 horas")])   # POO + eventos

unidades = dict(reportes.unidades_recetadas(reg.recetas))                            # funcional (reduce)
estados = reportes.citas_por_estado(reg.citas)                                       # funcional (reduce)
ruta, clave = os.path.join(tempfile.mkdtemp(), "respaldo.bin"), generar_clave()
reg.exportar_cifrado(ruta, clave)                                                    # seguridad
with open(ruta, "rb") as archivo:
    texto = descifrar_texto(archivo.read(), clave)

pruebas = {
    "POO: receta emitida y stock descontado": reg.inventario.obtener("Paracetamol 500 mg").stock == 8,
    "Eventos: oyentes sanos avisados pese al oyente defectuoso": sorted(avisos) == ["receta_emitida", "stock_bajo"],
    "Funcional: reportes calculados sobre los objetos": unidades == {"Paracetamol 500 mg": 6} and estados == {"programada": 1},
    "Seguridad: respaldo cifrado se descifra sin el DNI completo": "00000002" not in texto and "Juan" in texto,
}
for nombre, ok in pruebas.items():
    print(("OK   " if ok else "FALLA"), nombre)
print("VEREDICTO:", "VIABLE" if all(pruebas.values()) else "REQUIERE AJUSTE")
