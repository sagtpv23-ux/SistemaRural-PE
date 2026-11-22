"""Registro central del establecimiento (patrón Singleton, sílabo 3.4).

Singleton: solo puede existir UN registro en todo el programa. Así todos los módulos
(consola, interfaz, pruebas) trabajan sobre los mismos datos y no se duplican registros.
"""
import json
from datetime import datetime

from .eventos import BusEventos
from .excepciones import (CitaConflictoError, CitaNoEncontradaError, ErrorSistemaRural,
                          PacienteDuplicadoError, PacienteNoEncontradoError,
                          PermisoDenegadoError, StockInsuficienteError)
from .modelos import (Cita, DetalleReceta, EstadoCita, Inventario, Paciente, PersonalSalud,
                      Receta)
from .seguridad import cifrar_texto, hash_dni


class RegistroCentral:
    """Única fuente de verdad del establecimiento (una sola instancia)."""

    _instancia = None   # aquí se guarda la única instancia

    def __new__(cls):
        # __new__ se ejecuta antes de crear el objeto: si ya existe uno, se devuelve ese mismo
        if cls._instancia is None:
            instancia = super().__new__(cls)
            instancia._inicializar()
            cls._instancia = instancia
        return cls._instancia

    def _inicializar(self) -> None:
        self._pacientes = {}   # diccionario: hash del DNI -> Paciente
        self._personal = {}    # diccionario: hash del DNI -> PersonalSalud
        self._citas = []       # lista de Cita
        self._recetas = []     # lista de Receta
        self._siguiente_id = 1
        self._siguiente_receta = 1
        self.inventario = Inventario()
        self.eventos = BusEventos()

    @classmethod
    def reiniciar(cls):
        """Descarta la instancia actual y crea una nueva vacía (se usa en las pruebas)."""
        cls._instancia = None
        return cls()

    # --- pacientes ---------------------------------------------------
    def registrar_paciente(self, paciente):
        if paciente.dni_hash in self._pacientes:
            raise PacienteDuplicadoError("Ya existe un paciente con ese DNI.")
        self._pacientes[paciente.dni_hash] = paciente
        self.eventos.publicar("paciente_registrado", paciente=paciente)

    def buscar_paciente(self, dni: str) -> Paciente:
        try:
            return self._pacientes[hash_dni(dni)]
        except KeyError:
            raise PacienteNoEncontradoError("Paciente no registrado.")

    def paciente_por_id(self, id_hash: str) -> Paciente:
        try:
            return self._pacientes[id_hash]
        except KeyError:
            raise PacienteNoEncontradoError("Paciente no registrado.")

    def eliminar_paciente(self, paciente: Paciente) -> int:
        """Elimina al paciente y su historial de citas (derecho de cancelación, Ley N.° 29733).

        No permite eliminarlo si tiene citas programadas: primero deben atenderse o cancelarse.
        Devuelve la cantidad de citas eliminadas junto con él.
        """
        propias = [c for c in self._citas if c.paciente.dni_hash == paciente.dni_hash]
        if any(c.estado is EstadoCita.PROGRAMADA for c in propias):
            raise ErrorSistemaRural("El paciente tiene citas programadas; atiéndalas o cancélelas primero.")
        self.paciente_por_id(paciente.dni_hash)
        self._citas = [c for c in self._citas if c not in propias]
        self._recetas = [r for r in self._recetas if r.paciente.dni_hash != paciente.dni_hash]
        del self._pacientes[paciente.dni_hash]
        self.eventos.publicar("paciente_eliminado", paciente=paciente)
        return len(propias)

    @property
    def pacientes(self) -> tuple:
        return tuple(self._pacientes.values())

    # --- personal de salud -------------------------------------------
    def registrar_personal(self, personal: PersonalSalud) -> None:
        if personal.dni_hash in self._personal:
            raise PacienteDuplicadoError("Ya existe personal con ese DNI.")
        self._personal[personal.dni_hash] = personal
        self.eventos.publicar("personal_registrado", personal=personal)

    @property
    def personal(self) -> tuple:
        return tuple(self._personal.values())

    # --- citas -------------------------------------------------------
    def programar_cita(self, dni: str, personal: PersonalSalud,
                       fecha_hora: datetime, motivo: str) -> Cita:
        return self.programar_cita_para(self.buscar_paciente(dni), personal, fecha_hora, motivo)

    def programar_cita_para(self, paciente: Paciente, personal: PersonalSalud,
                            fecha_hora: datetime, motivo: str) -> Cita:
        ocupado = any(c.personal.dni_hash == personal.dni_hash
                      and c.fecha_hora == fecha_hora
                      and c.estado is EstadoCita.PROGRAMADA
                      for c in self._citas)
        if ocupado:
            raise CitaConflictoError("El personal ya tiene una cita a esa hora.")
        cita = Cita(self._siguiente_id, paciente, personal, fecha_hora, motivo)
        self._siguiente_id += 1
        self._citas.append(cita)
        self.eventos.publicar("cita_programada", cita=cita)
        return cita

    def _cita(self, id_cita: int) -> Cita:
        for c in self._citas:
            if c.id == id_cita:
                return c
        raise CitaNoEncontradaError(f"No existe la cita {id_cita}.")

    def atender_cita(self, id_cita: int) -> None:
        cita = self._cita(id_cita)
        cita.atender()
        self.eventos.publicar("cita_actualizada", cita=cita)

    def cancelar_cita(self, id_cita: int) -> None:
        cita = self._cita(id_cita)
        cita.cancelar()
        self.eventos.publicar("cita_actualizada", cita=cita)

    def eliminar_cita(self, id_cita: int) -> None:
        cita = self._cita(id_cita)
        self._citas.remove(cita)
        self.eventos.publicar("cita_actualizada", cita=cita)

    @property
    def citas(self) -> tuple:
        return tuple(self._citas)

    # --- recetas -----------------------------------------------------
    def emitir_receta(self, paciente: Paciente, medico: PersonalSalud, lineas,
                      fecha_hora: datetime = None) -> Receta:
        """Emite una receta y descuenta el stock. Solo prescribe quien tiene permiso (RF5).

        `lineas` es una lista de (medicamento, cantidad, indicaciones). Es "todo o nada": si falta
        stock de cualquier medicamento no se descuenta ninguno.
        """
        if not medico.puede_prescribir():
            raise PermisoDenegadoError(f"El rol {medico.rol()} no puede emitir recetas.")
        detalles = []
        for nombre, cantidad, indicaciones in lineas:
            med = self.inventario.obtener(nombre)               # error si no existe
            detalle = DetalleReceta(med.nombre, cantidad, indicaciones)
            if detalle.cantidad > med.stock:
                raise StockInsuficienteError(
                    f"Stock insuficiente de {med.nombre}: hay {med.stock} y la receta pide {detalle.cantidad}.")
            detalles.append(detalle)
        receta = Receta(self._siguiente_receta, paciente, medico, fecha_hora or datetime.now(), detalles)
        for d in receta.detalles:                                # recién aquí se descuenta el stock
            self.dispensar_medicamento(d.medicamento, d.cantidad, medico)
        self._siguiente_receta += 1
        self._recetas.append(receta)
        self.eventos.publicar("receta_emitida", receta=receta)
        return receta

    @property
    def recetas(self) -> tuple:
        return tuple(self._recetas)

    # --- inventario --------------------------------------------------
    def dispensar_medicamento(self, nombre, cantidad, personal=None):
        """Retira stock; con profesional indicado, exige permiso de prescribir (RF5)."""
        if personal is not None and not personal.puede_prescribir():
            raise PermisoDenegadoError(f"El rol {personal.rol()} no puede dispensar medicamentos.")
        med = self.inventario.obtener(nombre)
        med.retirar(cantidad)
        self.eventos.publicar("inventario_actualizado", medicamento=med.nombre)
        if med.en_stock_critico:
            self.eventos.publicar("stock_bajo", medicamento=med.nombre, stock=med.stock)

    def agregar_medicamento(self, nombre, stock, stock_minimo):
        """Registra un medicamento nuevo en el inventario y avisa a los oyentes."""
        medicamento = self.inventario.agregar(nombre, stock, stock_minimo)
        self.eventos.publicar("inventario_actualizado", medicamento=medicamento.nombre)
        return medicamento

    def reponer_medicamento(self, nombre, cantidad):
        self.inventario.obtener(nombre).reponer(cantidad)
        self.eventos.publicar("inventario_actualizado", medicamento=nombre)

    # --- persistencia segura -----------------------------------------
    def exportar_cifrado(self, ruta: str, clave: bytes) -> None:
        """Guarda pacientes, citas y recetas cifrados; el DNI solo va enmascarado."""
        datos = {
            "pacientes": [{"dni": p.dni_enmascarado, "nombres": p.nombres,
                           "apellidos": p.apellidos, "diagnosticos": list(p.diagnosticos)}
                          for p in self._pacientes.values()],
            "citas": [{"id": c.id, "paciente": c.paciente.dni_enmascarado,
                       "fecha": f"{c.fecha_hora:%d/%m/%Y %H:%M}", "estado": c.estado.value}
                      for c in self._citas],
            "recetas": [{"id": r.id, "paciente": r.paciente.dni_enmascarado,
                         "medico": r.medico.nombre_completo, "fecha": f"{r.fecha_hora:%d/%m/%Y %H:%M}",
                         "detalles": [{"medicamento": d.medicamento, "cantidad": d.cantidad,
                                       "indicaciones": d.indicaciones} for d in r.detalles]}
                        for r in self._recetas],
        }
        with open(ruta, "wb") as archivo:
            archivo.write(cifrar_texto(json.dumps(datos, ensure_ascii=False), clave))
