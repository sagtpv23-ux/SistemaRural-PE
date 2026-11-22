# Garantiza que cada prueba se ejecute con RegistroCentral.
import pytest
from sistema_rural.registro import RegistroCentral


@pytest.fixture(autouse=True)
def registro_limpio():
    """Cada prueba parte de un registro vacío."""
    return RegistroCentral.reiniciar()
