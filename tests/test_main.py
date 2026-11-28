"""Prueba de humo de la demostración por consola (programación estructurada)."""
import pytest


def test_demostracion_por_consola_genera_respaldo_cifrado(tmp_path, monkeypatch, capsys):
    pytest.importorskip("cryptography")
    from sistema_rural import main
    monkeypatch.chdir(tmp_path)                       # el respaldo se crea en una carpeta temporal
    main.main()
    salida = capsys.readouterr().out
    assert "Error controlado" in salida               # los errores esperados se muestran sin romper
    assert "ALERTA: stock crítico" in salida          # el evento stock_bajo llegó al oyente
    assert "se descifró bien y no contiene el DNI completo: True" in salida
    assert (tmp_path / "respaldo_demo.bin").exists()
