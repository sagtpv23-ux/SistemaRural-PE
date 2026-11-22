"""Paradigma funcional : funciones que reciben datos y devuelven resultados.
Se usan map, filter, reduce y lambda sin modificar las colecciones originales."""

from functools import reduce

def _sumar_estado(acumulado, cita):
    """Función auxiliar para reduce: devuelve un diccionario NUEVO con el conteo actualizado."""
    estado = cita.estado.value
    nuevo = dict(acumulado)                 
    nuevo[estado] = nuevo.get(estado, 0) + 1
    return nuevo


def citas_por_estado(citas):
    """Cuenta citas por estado con reduce. Ejemplo: {'atendida': 1, 'programada': 2}."""
    return reduce(_sumar_estado, citas, {})


def citas_del_dia(citas, dia):
    """Filtra las citas de un día (filter + lambda)."""
    return list(filter(lambda c: c.fecha_hora.date() == dia, citas))


def resumen_citas(citas):
    """Líneas de reporte SIN datos sensibles (map + lambda)."""
    ordenadas = sorted(citas, key=lambda c: c.fecha_hora)
    return list(map(
        lambda c: (f"{c.fecha_hora:%d/%m/%Y %H:%M} | {c.paciente.dni_enmascarado} | "
                   f"{c.personal.rol()} | {c.estado.value}"),
        ordenadas))


def medicamentos_criticos(inventario):
    """Medicamentos con stock igual o menor al mínimo (filter + lambda)."""
    return list(filter(lambda m: m.en_stock_critico, inventario.listar()))


def edad_promedio(pacientes, referencia=None):
    """Edad promedio de los pacientes, sumando con reduce."""
    if not pacientes:
        return 0.0
    total = reduce(lambda suma, p: suma + p.edad(referencia), pacientes, 0)
    return round(total / len(pacientes), 1)


def _sumar_unidades(acumulado, detalle):
    """Auxiliar para reduce: devuelve un diccionario NUEVO con las unidades recetadas por medicamento."""
    nuevo = dict(acumulado)
    nuevo[detalle.medicamento] = nuevo.get(detalle.medicamento, 0) + detalle.cantidad
    return nuevo


def unidades_recetadas(recetas):
    """Total de unidades recetadas por medicamento (comprensión + reduce)."""
    detalles = [d for receta in recetas for d in receta.detalles]
    return reduce(_sumar_unidades, detalles, {})


def resumen_recetas(recetas):
    """Líneas de reporte de recetas SIN datos sensibles (map + lambda)."""
    ordenadas = sorted(recetas, key=lambda r: r.fecha_hora)
    return list(map(
        lambda r: (f"N.° {r.id} | {r.fecha_hora:%d/%m/%Y %H:%M} | {r.paciente.dni_enmascarado} | "
                   + ", ".join(f"{d.medicamento} x{d.cantidad}" for d in r.detalles)),
        ordenadas))
