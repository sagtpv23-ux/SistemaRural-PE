"""Excepciones propias del dominio (manejo de errores explícito)."""


class ErrorSistemaRural(Exception):
    """Excepción base del sistema."""


class DniInvalidoError(ErrorSistemaRural):
    """El DNI no tiene exactamente 8 dígitos."""


class PacienteDuplicadoError(ErrorSistemaRural):
    """Ya existe un paciente con el mismo DNI."""


class PacienteNoEncontradoError(ErrorSistemaRural):
    """No existe el paciente buscado."""


class CitaConflictoError(ErrorSistemaRural):
    """El personal ya tiene una cita en esa fecha y hora."""


class CitaNoEncontradaError(ErrorSistemaRural):
    """No existe la cita indicada."""


class StockInsuficienteError(ErrorSistemaRural):
    """No hay unidades suficientes del medicamento."""


class MedicamentoNoEncontradoError(ErrorSistemaRural):
    """El medicamento no está en el inventario."""


class CifradoNoDisponibleError(ErrorSistemaRural):
    """Falta la biblioteca 'cryptography' para cifrar datos en reposo."""


class PermisoDenegadoError(ErrorSistemaRural):
    """El rol del personal no tiene permiso para la operación (p. ej., dispensar)."""


class TipoPersonalInvalidoError(ErrorSistemaRural, ValueError):
    """El tipo de personal solicitado a la fábrica no existe."""


class RecetaInvalidaError(ErrorSistemaRural):
    """La receta no cumple las reglas (sin medicamentos o con medicamentos repetidos)."""
