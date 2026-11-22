"""Controlador de la interfaz: convierte lo escrito en los formularios en operaciones del dominio.

Separa la lógica del negocio de la ventana (vista): así el código es más fácil de mantener
y se puede probar sin abrir la interfaz gráfica. Aquí también se VALIDAN los datos antes
de registrarlos (fechas, horas, cantidades), mostrando errores claros al usuario.
"""
from datetime import date, datetime, timedelta

from . import reportes
from .excepciones import ErrorSistemaRural
from .fabricas import PersonalFactory
from .modelos import DetalleReceta, Paciente
from .registro import RegistroCentral
from .seguridad import generar_clave
from .validaciones import MAX_CANTIDAD


# Tipos de personal que se pueden elegir en la interfaz -> texto que entiende la fábrica
TIPOS_PERSONAL = {"Médico": "medico", "Enfermero": "enfermero"}


# Eventos que modifican los datos: al ocurrir alguno, hay cambios que aún no están respaldados
EVENTOS_DE_CAMBIO = ("paciente_registrado", "paciente_eliminado", "personal_registrado",
                     "cita_programada", "cita_actualizada", "inventario_actualizado", "receta_emitida")


class ControladorSistema:
    def __init__(self, registro=None):
        self._reg = registro or RegistroCentral()
        self._cambios_sin_guardar = False
        for evento in EVENTOS_DE_CAMBIO:           # listener: marca que hay datos sin respaldar
            self._reg.eventos.suscribir(evento, self._marcar_cambio)

    def _marcar_cambio(self, **_datos):
        self._cambios_sin_guardar = True

    @property
    def hay_cambios_sin_guardar(self) -> bool:
        """True si se registró o modificó algo desde el último respaldo (para avisar al cerrar)."""
        return self._cambios_sin_guardar

    @property
    def registro(self) -> RegistroCentral:
        return self._reg

    # --- pacientes ---------------------------------------------------
    def registrar_paciente(self, dni: str, nombres: str, apellidos: str, fecha_texto: str) -> Paciente:
        nacimiento = self._leer_fecha(fecha_texto)
        try:
            paciente = Paciente(dni.strip(), nombres, apellidos, nacimiento)
        except ValueError as error:
            raise ErrorSistemaRural(str(error))
        self._reg.registrar_paciente(paciente)
        return paciente

    @staticmethod
    def _leer_fecha(texto):
        """Convierte 'DD/MM/AAAA' (con ceros, por ejemplo 05/01/2000) en fecha; si no, lanza error."""
        limpio = texto.strip()
        try:
            if len(limpio) != 10:
                raise ValueError
            return datetime.strptime(limpio, "%d/%m/%Y").date()
        except ValueError:
            raise ErrorSistemaRural("La fecha debe tener el formato DD/MM/AAAA (por ejemplo, 05/01/2000).")

    def filas_pacientes(self, filtro_dni: str = "", con_id: bool = False) -> list:
        """(DNI enmascarado, nombre completo, edad). Con un DNI de 8 dígitos busca solo a ese paciente.

        Con con_id=True devuelve (id_interno, fila) para poder identificar la fila seleccionada.
        """
        filtro = filtro_dni.strip()
        pacientes = [self._reg.buscar_paciente(filtro)] if filtro else self._reg.pacientes
        filas = [(p.dni_hash, (p.dni_enmascarado, p.nombre_completo, p.edad())) for p in pacientes]
        return filas if con_id else [fila for _, fila in filas]

    def eliminar_paciente(self, id_paciente: str) -> int:
        """Elimina al paciente (y su historial de citas). Devuelve cuántas citas se eliminaron."""
        return self._reg.eliminar_paciente(self._reg.paciente_por_id(id_paciente))

    def opciones_pacientes(self) -> list:
        return [(f"{p.dni_enmascarado} - {p.nombre_completo}", p) for p in self._reg.pacientes]

    def opciones_personal(self) -> list:
        return [(f"{p.rol()} - {p.nombre_completo}", p) for p in self._reg.personal]

    # --- personal de salud -------------------------------------------
    def tipos_personal(self):
        return list(TIPOS_PERSONAL)

    def registrar_personal(self, tipo_texto, dni, nombres, apellidos, colegiatura):
        """Registra personal de salud nuevo usando la fábrica según el tipo elegido."""
        tipo = TIPOS_PERSONAL.get(tipo_texto)
        if tipo is None:
            raise ErrorSistemaRural("Seleccione el tipo de personal (Médico o Enfermero).")
        try:
            personal = PersonalFactory.crear(tipo, dni.strip(), nombres, apellidos, colegiatura)
        except ValueError as error:
            raise ErrorSistemaRural(str(error))
        self._reg.registrar_personal(personal)
        return personal

    def filas_personal(self):
        return [(p.dni_enmascarado, p.nombre_completo, p.rol(), p.colegiatura) for p in self._reg.personal]

    # --- citas -------------------------------------------------------
    def programar_cita(self, paciente, personal, fecha_texto: str, hora_texto: str, motivo: str):
        if paciente is None or personal is None:
            raise ErrorSistemaRural("Seleccione un paciente y un profesional.")
        if not motivo.strip():
            raise ErrorSistemaRural("Indique el motivo de la cita.")
        fecha = self._leer_fecha(fecha_texto)
        hora = hora_texto.strip()
        try:
            if len(hora) != 5:
                raise ValueError
            hora_leida = datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            raise ErrorSistemaRural("La hora debe tener el formato HH:MM (por ejemplo, 08:30).")
        fecha_hora = datetime.combine(fecha, hora_leida)
        if fecha_hora < datetime.now():
            raise ErrorSistemaRural("La cita no puede estar en el pasado.")
        if fecha_hora > datetime.now() + timedelta(days=365):
            raise ErrorSistemaRural("La cita no puede programarse con más de un año de anticipación.")
        try:
            return self._reg.programar_cita_para(paciente, personal, fecha_hora, motivo)
        except ValueError as error:          # por ejemplo, motivo con caracteres no permitidos
            raise ErrorSistemaRural(str(error))

    def filas_citas(self) -> list:
        return [(c.id, f"{c.fecha_hora:%d/%m/%Y %H:%M}",
                 f"{c.paciente.dni_enmascarado} {c.paciente.nombre_completo}",
                 f"{c.personal.rol()} {c.personal.nombre_completo}", c.estado.value)
                for c in sorted(self._reg.citas, key=lambda c: c.fecha_hora)]

    def atender_cita(self, id_cita: int) -> None:
        self._reg.atender_cita(id_cita)

    def cancelar_cita(self, id_cita: int) -> None:
        self._reg.cancelar_cita(id_cita)

    def eliminar_cita(self, id_cita: int) -> None:
        self._reg.eliminar_cita(id_cita)

    # --- recetas -----------------------------------------------------
    def preparar_linea_receta(self, nombre, cantidad_texto, indicaciones):
        """Valida una línea de la receta antes de agregarla al borrador: (nombre, cantidad, indicaciones)."""
        if not nombre:
            raise ErrorSistemaRural("Seleccione el medicamento.")
        cantidad = self._entero_positivo(cantidad_texto)
        try:
            detalle = DetalleReceta(nombre, cantidad, indicaciones)
        except ValueError as error:
            raise ErrorSistemaRural(str(error))
        return detalle.medicamento, detalle.cantidad, detalle.indicaciones

    def emitir_receta(self, paciente, medico, lineas):
        """Emite la receta (lineas = [(medicamento, cantidad, indicaciones)]) y descuenta el stock."""
        if paciente is None or medico is None:
            raise ErrorSistemaRural("Seleccione el paciente y el médico que receta.")
        if not lineas:
            raise ErrorSistemaRural("Agregue al menos un medicamento a la receta.")
        return self._reg.emitir_receta(paciente, medico, lineas)

    def nombres_medicamentos(self) -> list:
        return [m.nombre for m in self._reg.inventario.listar()]

    def filas_recetas(self) -> list:
        """(N.°, fecha y hora, paciente, médico, resumen) de cada receta, de la más reciente a la más antigua."""
        return [(r.id, f"{r.fecha_hora:%d/%m/%Y %H:%M}",
                 f"{r.paciente.dni_enmascarado} {r.paciente.nombre_completo}",
                 f"{r.medico.rol()} {r.medico.nombre_completo}", f"{len(r.detalles)} medicamento(s)")
                for r in sorted(self._reg.recetas, key=lambda r: r.id, reverse=True)]

    def filas_detalle_receta(self, id_receta: int) -> list:
        """(medicamento, cantidad, indicaciones) de la receta indicada."""
        for r in self._reg.recetas:
            if r.id == id_receta:
                return [(d.medicamento, d.cantidad, d.indicaciones) for d in r.detalles]
        raise ErrorSistemaRural(f"No existe la receta {id_receta}.")

    # --- inventario --------------------------------------------------
    @staticmethod
    def _leer_entero(texto, campo, minimo):
        """Convierte un texto en entero validando que sean solo dígitos y esté en rango."""
        limpio = texto.strip()
        # isascii + isdecimal: solo dígitos del 0 al 9 (sin signos, puntos, guiones bajos ni otros alfabetos)
        if not limpio or not limpio.isascii() or not limpio.isdecimal():
            raise ErrorSistemaRural(f"{campo} debe ser un número entero (solo dígitos).")
        valor = int(limpio)
        if valor < minimo or valor > MAX_CANTIDAD:
            raise ErrorSistemaRural(f"{campo} debe estar entre {minimo} y {MAX_CANTIDAD}.")
        return valor

    @staticmethod
    def _entero_positivo(texto):
        return ControladorSistema._leer_entero(texto, "La cantidad", 1)

    def agregar_medicamento(self, nombre, stock_texto, minimo_texto):
        """Registra un medicamento nuevo validando nombre y cantidades."""
        stock = self._leer_entero(stock_texto, "El stock inicial", 0)
        minimo = self._leer_entero(minimo_texto, "El stock mínimo", 0)
        try:
            return self._reg.agregar_medicamento(nombre, stock, minimo)
        except ValueError as error:
            raise ErrorSistemaRural(str(error))

    def filas_inventario(self) -> list:
        return [(m.nombre, m.stock, m.stock_minimo, "CRÍTICO" if m.en_stock_critico else "Normal")
                for m in self._reg.inventario.listar()]

    def dispensar(self, nombre, cantidad_texto, personal=None):
        """Dispensa un medicamento; si se indica el profesional, solo el médico tiene permiso (RF5)."""
        self._reg.dispensar_medicamento(nombre, self._entero_positivo(cantidad_texto), personal)

    def reponer(self, nombre, cantidad_texto):
        self._reg.reponer_medicamento(nombre, self._entero_positivo(cantidad_texto))

    # --- reportes y respaldo -----------------------------------------
    def texto_reporte(self) -> str:
        citas, reg = self._reg.citas, self._reg
        criticos = reportes.medicamentos_criticos(reg.inventario)
        lineas = ["RESUMEN DE CITAS (DNI enmascarado)"]
        lineas += reportes.resumen_citas(citas) or ["  (sin citas registradas)"]
        por_estado = reportes.citas_por_estado(citas)
        lineas += ["", "CITAS POR ESTADO",
                   ", ".join(f"{k}: {v}" for k, v in por_estado.items()) or "  (sin datos)",
                   "", f"EDAD PROMEDIO DE PACIENTES: {reportes.edad_promedio(reg.pacientes)} años",
                   "", f"RECETAS EMITIDAS: {len(reg.recetas)}"]
        lineas += reportes.resumen_recetas(reg.recetas)
        unidades = reportes.unidades_recetadas(reg.recetas)
        lineas += [f"  Total recetado de {n}: {u} u." for n, u in unidades.items()]
        lineas += ["", "MEDICAMENTOS EN STOCK CRÍTICO"]
        lineas += [f"  {m.nombre}: {m.stock} u. (mínimo {m.stock_minimo})" for m in criticos] or ["  (ninguno)"]
        return "\n".join(lineas)

    def exportar_respaldo(self, ruta: str) -> str:
        """Exporta cifrado y devuelve la clave (texto) que el usuario debe guardar aparte."""
        clave = generar_clave()
        self._reg.exportar_cifrado(ruta, clave)
        self._cambios_sin_guardar = False          # los datos ya quedaron respaldados
        return clave.decode()

    # --- datos de demostración (ficticios) -----------------------------
    def cargar_demo(self) -> None:
        if self._reg.pacientes:
            raise ErrorSistemaRural("Ya hay datos cargados; la demostración solo se carga con el registro vacío.")
        medico = PersonalFactory.crear("medico", "00000001", "Rosa", "Salazar Vega", "CMP-00001")
        enfermero = PersonalFactory.crear("enfermero", "00000009", "Luis", "Rojas Cruz", "CEP-00001")
        self._reg.registrar_personal(medico)
        self._reg.registrar_personal(enfermero)
        datos = [("00000002", "Juan", "Pérez Díaz", date(1985, 3, 14)),
                 ("00000003", "María", "Tello Cruz", date(2001, 7, 2)),
                 ("00000004", "Pedro", "Quispe Vega", date(1960, 11, 20))]
        pacientes = [Paciente(*d) for d in datos]
        for p in pacientes:
            self._reg.registrar_paciente(p)
        self._reg.inventario.agregar("Paracetamol 500 mg", stock=14, stock_minimo=10)
        self._reg.inventario.agregar("Ibuprofeno 400 mg", stock=40, stock_minimo=15)
        self._reg.inventario.agregar("Amoxicilina 500 mg", stock=9, stock_minimo=10)
        base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        self._reg.programar_cita_para(pacientes[0], medico, base, "Control")
        self._reg.programar_cita_para(pacientes[1], medico, base.replace(minute=30), "Fiebre")
        self._reg.programar_cita_para(pacientes[2], enfermero, base.replace(hour=10), "Curación")
        self._reg.emitir_receta(pacientes[0], medico, [
            ("Ibuprofeno 400 mg", 6, "1 tableta cada 8 horas por 2 días"),
            ("Paracetamol 500 mg", 3, "1 tableta si hay fiebre")])