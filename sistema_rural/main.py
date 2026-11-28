"""Demostración por consola del módulo (datos ficticios)."""
from datetime import date, datetime

from .excepciones import ErrorSistemaRural
from .seguridad import descifrar_texto, generar_clave
from .fabricas import PersonalFactory
from .modelos import Paciente
from .registro import RegistroCentral
from . import reportes


def alerta_stock(medicamento: str, stock: int) -> None:
    print(f"  ALERTA: stock crítico de {medicamento} ({stock} u.)")


def aviso_receta(receta) -> None:
    print(f"  AVISO: la receta N.° {receta.id} se emitió correctamente ({receta.total_unidades()} unidades).")


def main() -> None:
    reg = RegistroCentral()
    reg.eventos.suscribir("stock_bajo", alerta_stock)
    reg.eventos.suscribir("receta_emitida", aviso_receta)

    medico = PersonalFactory.crear("medico", "00000001", "Rosa", "Salazar Vega", "CMP-00001")
    reg.registrar_paciente(Paciente("00000002", "Juan", "Pérez Díaz", date(1985, 3, 14)))
    reg.registrar_paciente(Paciente("00000003", "María", "Tello Cruz", date(2001, 7, 2)))
    reg.inventario.agregar("Paracetamol 500 mg", stock=14, stock_minimo=10)
    reg.inventario.agregar("Ibuprofeno 400 mg", stock=40, stock_minimo=15)

    reg.programar_cita("00000002", medico, datetime(2026, 11, 3, 9, 0), "Control")
    reg.programar_cita("00000003", medico, datetime(2026, 11, 3, 9, 30), "Fiebre")
    try:  # error esperado: mismo médico y misma hora
        reg.programar_cita("00000003", medico, datetime(2026, 11, 3, 9, 0), "Duplicada")
    except ErrorSistemaRural as error:
        print("Error controlado:", error)

    reg.atender_cita(1)
    enfermero = PersonalFactory.crear("enfermero", "00000009", "Luis", "Rojas Cruz", "CEP-00001")
    try:  # error esperado: el enfermero no puede dispensar
        reg.dispensar_medicamento("Paracetamol 500 mg", 1, enfermero)
    except ErrorSistemaRural as error:
        print("Error controlado:", error)
    reg.dispensar_medicamento("Paracetamol 500 mg", 6, medico)

    print("\nReceta con detalle:")
    receta = reg.emitir_receta(reg.buscar_paciente("00000002"), medico, [
        ("Ibuprofeno 400 mg", 6, "1 tableta cada 8 horas por 2 días"),
        ("Paracetamol 500 mg", 1, "1 tableta si hay fiebre")], datetime(2026, 11, 3, 9, 20))
    for d in receta.detalles:
        print(f"  - {d.medicamento} x{d.cantidad}: {d.indicaciones}")

    print("\nResumen de citas (DNI enmascarado):")
    print(*reportes.resumen_citas(reg.citas), sep="\n")
    print("\nRecetas (DNI enmascarado):")
    print(*reportes.resumen_recetas(reg.recetas), sep="\n")
    print("\nPor estado:", reportes.citas_por_estado(reg.citas))
    print("Edad promedio:", reportes.edad_promedio(reg.pacientes, date(2026, 11, 3)))
    print("Medicamentos críticos:", [m.nombre for m in reportes.medicamentos_criticos(reg.inventario)])
    clave = generar_clave()
    reg.exportar_cifrado("respaldo_demo.bin", clave)
    print("Respaldo cifrado generado: respaldo_demo.bin")
    print("Clave de la demostración (en el sistema real se guarda aparte):", clave.decode())
    with open("respaldo_demo.bin", "rb") as archivo:      # comprobación: la clave sí abre el respaldo
        contenido = descifrar_texto(archivo.read(), clave)
    print("Verificación: el respaldo se descifró bien y no contiene el DNI completo:",
          "00000002" not in contenido)


if __name__ == "__main__":
    main()