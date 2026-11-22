"""Paradigma orientado a eventos (sílabo, Tema 5.1: eventos, listeners y handlers).

Un "evento" es algo que ocurre en el sistema (por ejemplo, "stock_bajo").
Un "listener" (oyente) es una función que se suscribe a un evento y se ejecuta
cuando este ocurre. Esta clase actúa como un tablero de avisos (patrón Observer).
"""


class BusEventos:
    def __init__(self):
        # Diccionario: nombre del evento -> lista de funciones que escuchan ese evento
        self._oyentes = {}

    def suscribir(self, evento, manejador):
        """Registra una función (manejador) para que se ejecute cuando ocurra el evento."""
        if evento not in self._oyentes:
            self._oyentes[evento] = []
        self._oyentes[evento].append(manejador)

    def publicar(self, evento, **datos):
        """Avisa a todos los oyentes del evento y devuelve cuántos fueron notificados.

        Si un oyente falla, se muestra un aviso y se continúa con los demás.
        """
        notificados = 0
        for manejador in self._oyentes.get(evento, []):
            try:
                manejador(**datos)
                notificados += 1
            except Exception as error:
                print(f"[aviso] el manejador del evento '{evento}' falló: {error}")
        return notificados
