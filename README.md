# SistemaRural-PE

SistemaRural-PE es un sistema local de gestión para establecimientos de salud rurales del Perú. El proyecto plantea una alternativa modular para registrar pacientes y personal de salud, administrar citas, controlar el inventario de medicamentos y generar reportes, incluso en entornos con conectividad limitada.

## Problema que aborda

El caso estudiado considera al Centro de Salud Rural «Santa Rosa», ubicado en el distrito de Chugur, Cajamarca. El registro manual de la atención puede ocasionar duplicidad de pacientes, conflictos en la programación de citas, demoras y pérdida de información.

SistemaRural-PE reúne las operaciones principales en una aplicación de escritorio que funciona localmente y organiza el código por responsabilidades.

## Funcionalidades

- **Pacientes:** registro con validación del DNI de 8 dígitos y rechazo de registros duplicados.
- **Personal de salud:** registro y diferenciación de médicos y enfermeros mediante sus roles.
- **Citas:** programación, atención y cancelación; se impiden citas simultáneas del mismo profesional. Las fechas se ingresan y muestran como DD/MM/AAAA.
- **Recetas médicas:** emisión solo por médicos, asociadas a un paciente. Cada línea de la receta registra medicamento, cantidad e indicaciones, y la emisión es «todo o nada»: si falta stock de cualquier medicamento no se descuenta ninguno.
- **Alertas:** confirmaciones visuales para el registro de pacientes, citas y recetas; los errores se muestran sin cerrar el programa.
- **Inventario:** registro y control de medicamentos, validación de cantidades y alertas cuando el stock llega a un nivel crítico.
- **Permisos por rol:** la dispensación de medicamentos está restringida al personal médico.
- **Reportes:** resumen de citas por estado, citas por día, edad promedio y medicamentos con stock crítico.
- **Respaldo:** exportación cifrada de la información mediante Fernet.
- **Interfaz gráfica:** aplicación de escritorio con pestañas para Pacientes, Personal, Citas, Recetas, Inventario y Reportes.

## Tecnologías y paradigmas

| Elemento | Uso en el proyecto |
|---|---|
| Python 3.12 o superior | Lenguaje principal |
| Tkinter | Interfaz gráfica de escritorio |
| pytest | Pruebas automatizadas |
| cryptography (Fernet) | Cifrado de respaldos |
| HMAC-SHA256 | Protección del identificador DNI |
| Git y GitHub | Control de versiones y trabajo colaborativo |
| Programación orientada a objetos | Modelado de pacientes, personal, citas, recetas e inventario |
| Programación funcional | Reportes con `map`, `filter`, `reduce`, `sorted(key=...)` y `lambda` |
| Programación orientada a eventos | Comunicación entre módulos y notificaciones mediante Observer |
| Programación estructurada | Punto de entrada y demostración del sistema |

### Patrones de diseño

- **Singleton — `RegistroCentral`:** mantiene una única instancia como fuente central de los datos en memoria.
- **Factory — `PersonalFactory`:** centraliza la creación de los tipos de personal de salud.
- **Observer — `BusEventos`:** permite publicar y atender eventos, como `stock_bajo`, sin acoplar el inventario a la interfaz gráfica.

## Arquitectura y estructura del repositorio

La estructura principal del programa es:

l_programación/
├── docs/
│   ├── UML_Diagrama.png
│   └── diagrama_secuencia.png
├── sistema_rural/
│   ├── __init__.py
│   ├── controlador.py
│   ├── eventos.py
│   ├── excepciones.py
│   ├── fabricas.py
│   ├── main.py
│   ├── modelos.py
│   ├── registro.py
│   ├── reportes.py
│   ├── seguridad.py
│   ├── ui_tkinter.py
│   └── validaciones.py
├── tests/
│   ├── conftest.py
│   ├── test_controlador.py
│   ├── test_main.py
│   ├── test_modelos.py
│   ├── test_recetas.py
│   ├── test_registro.py
│   ├── test_reportes.py
│   ├── test_seguridad.py
│   ├── test_validaciones.py
│   └── test_ventana.py
├── .gitignore
├── requirements.txt
└── README.md


### Responsabilidad de los módulos

| Archivo | Responsabilidad |
|---|---|
| `excepciones.py` | Excepciones propias del dominio y jerarquía de errores del sistema. |
| `validaciones.py` | Validación de nombres, DNI, fechas, cantidades y otros datos de entrada. |
| `seguridad.py` | Validación, enmascaramiento y hash del DNI; derivación de clave y cifrado Fernet. |
| `modelos.py` | Clases del dominio: `Persona`, `Paciente`, `PersonalSalud`, `Medico`, `Enfermero`, `Cita`, `Medicamento` e `Inventario`. |
| `eventos.py` | Bus de eventos: suscripción y publicación de notificaciones. |
| `fabricas.py` | `PersonalFactory`, responsable de crear tipos de personal de salud. |
| `registro.py` | `RegistroCentral`: coordinación de pacientes, personal, citas, inventario y exportación cifrada. |
| `reportes.py` | Cálculo de reportes mediante operaciones funcionales. |
| `controlador.py` | `ControladorSistema`: conecta los datos de la interfaz con las operaciones del dominio. |
| `ui_tkinter.py` | Ventana principal y pestañas de la aplicación Tkinter; gestiona los eventos de la interfaz. |
| `main.py` | Punto de entrada para ejecutar la demostración con datos ficticios. |

### Requisitos previos

- Python 3.12 o superior.
- Tkinter disponible en la instalación de Python para ejecutar la interfaz gráfica.
- `pip` para instalar las dependencias.

### 1. Clonar el repositorio

```bash
git clone https://github.com/sagtpv23-ux/SistemaRural-PE.git
cd SistemaRural-PE
```

### 2. Crear y activar un entorno virtual (recomendado)

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar la sal secreta del DNI

El sistema utiliza la variable de entorno `SISTEMA_RURAL_SAL` como sal secreta para el HMAC-SHA256 del DNI.
Si no está configurada, el sistema genera una sal **aleatoria** para esa ejecución y lo avisa en el log: el código ya no contiene ninguna sal fija (con una sal conocida, un DNI de 8 dígitos se recuperaría probando 100 millones de combinaciones). Como los datos viven solo en memoria, no hace falta fijarla para usar el programa; si algún día se guardan los hashes, la sal debe fijarse con esta variable.

**Windows (PowerShell):**

```powershell
$env:SISTEMA_RURAL_SAL = "coloca_aqui_un_valor_secreto"
```

### 5. Ejecutar el sistema

Desde la carpeta que contiene `sistema_rural/`:

**Demostración por consola:**

```bash
python -m sistema_rural.main
```

**Interfaz gráfica:**

```bash
python -m sistema_rural.ui_tkinter
```

## Seguridad y protección de datos

El proyecto considera la protección de datos personales conforme al enfoque de la Ley N.° 29733:

- El DNI se valida con 8 dígitos y no se conserva en texto plano: se almacena su hash HMAC-SHA256 y una representación enmascarada.
- Los reportes muestran el DNI enmascarado, no el número completo.
- Los respaldos se cifran con Fernet.
- Los diagnósticos se mantienen protegidos y se incluyen únicamente en la exportación cifrada.
- Las pruebas y demostraciones deben utilizar exclusivamente datos ficticios.


## Pruebas automatizadas

Las pruebas se ejecutan con `pytest`. Desde la carpeta raíz del proyecto:

```bash
pytest -v
```

La suite tiene **62 pruebas**: 58 se ejecutan sin interfaz (resultado: `58 passed`) y las 4 de `test_ventana.py` abren la ventana de Tkinter, por lo que requieren Tkinter y una pantalla disponible (si no la hay, `pytest` las omite en lugar de fallar).

| Archivo de prueba | Casos | Enfoque |
|---|---:|---|
| `test_validaciones.py` | 9 | Validación de nombres, DNI, fechas, colegiatura, diagnósticos, medicamentos y cantidades. |
| `test_seguridad.py` | 5 | Hash y enmascaramiento del DNI; sal desde el entorno o aleatoria; cifrado, descifrado y clave incorrecta. |
| `test_modelos.py` | 5 | Modelos, herencia, polimorfismo, Factory, propiedades y reglas del dominio. |
| `test_registro.py` | 9 | Singleton, duplicados de pacientes y de personal, conflictos de citas, permisos, inventario, eventos y log. |
| `test_reportes.py` | 5 | Reportes por estado y día, resumen, protección del DNI y pureza funcional (no modifican los datos). |
| `test_controlador.py` | 16 | Flujos de la aplicación, validaciones desde formularios (fechas DD/MM/AAAA), reportes y exportación. |
| `test_recetas.py` | 8 | Receta con detalle y descuento de stock; enfermero sin permiso; «todo o nada»; recetas inválidas; reportes de recetas; borrado; respaldo cifrado; controlador. |
| `test_main.py` | 1 | Demostración por consola de principio a fin: errores controlados, alerta de stock y respaldo cifrado verificable. |
| `test_ventana.py` | 4 | Ventana: alertas de éxito al registrar, error por fecha mal escrita, flujo de cita y receta con detalle, receta rechazada para el enfermero. |
| **Total** | **62** | |

Para ejecutar un archivo de pruebas específico:

```bash
pytest tests/test_modelos.py -v
```

El informe también registra una cobertura del 97 % en la lógica del sistema y del 59 % a nivel global (medida con la suite anterior a estas pruebas nuevas); la interfaz se verifica con `test_ventana.py` y con las pruebas de su controlador.

## Distribución de módulos entre los integrantes

| Integrante | Módulos y archivos asignados | Responsabilidad principal |
|---|---|---|
| **Arias Correa, Evelin Milagritos** | `modelos.py, `, `fabricas.py`, `tests/test_modelos.py, test_ventana` | Modelado de entidades, herencia, polimorfismo y creación de personal mediante Factory. |
| **Luicho Mosqueira, Hector Alexander** | `seguridad.py, conftest.py`, `validaciones.py`, `tests/test_seguridad.py`, `tests/test_validaciones.py` | Validación de entradas y protección del DNI; hash, enmascaramiento y cifrado de respaldos. |
| **Malca Malca, Ivan Edilberto** | `registro.py`, `eventos.py`, `excepciones.py`, `tests/test_reportes.py` | Registro central, patrón Singleton, eventos Observer, reglas de coordinación y excepciones del dominio. |
| **Mosqueira Tanta, Saul Alexander** | `controlador.py`, `ui_tkinter.py`, `tests/test_controlador.py` | Integración de la lógica con la interfaz, formularios, pestañas y ejecución de la aplicación. |
| **Valdez Quiroz, Victor Paul** | `reportes.py, main.py`, `tests/test_registro.py, test_recetas.py`, `docs/` y `README.md` | Reportes funcionales, documentación técnica y actualización de diagramas y guía del repositorio. |

## Limitaciones y mejoras futuras

De acuerdo con el informe, el prototipo presenta las siguientes limitaciones:

- **Persistencia parcial:** los datos se mantienen en memoria y existe exportación cifrada, pero no hay una base de datos ni recarga automática de respaldos al reiniciar.
- **Autenticación pendiente:** no existe inicio de sesión ni control de acceso por cuenta de usuario.
- **Gestión de claves:** la sal y las claves dependen de variables de entorno y no cuentan con rotación automática.
- **Consentimiento digital pendiente:** el registro del consentimiento informado no está integrado en el sistema.
- **Interfaz:** las pruebas de la ventana (`test_ventana.py`) necesitan Tkinter y una pantalla, por lo que no corren en servidores sin interfaz gráfica.
- **Recetas:** cada línea registra medicamento, cantidad e indicaciones; la dosis, la frecuencia y la duración se escriben dentro de las indicaciones y aún no son campos separados ni se vinculan a una cita.

Como mejoras futuras se propone incorporar SQLite cifrada, autenticación por usuario, auditoría de accesos, registro del consentimiento, pruebas de interfaz y evaluar la interoperabilidad con la historia clínica electrónica del MINSA.

## Integrantes

- Arias Correa, Evelin Milagritos
- Luicho Mosqueira, Hector Alexander
- Malca Malca, Ivan Edilberto
- Mosqueira Tanta, Saul Alexander
- Valdez Quiroz, Victor Paul

## Repositorio

[GitHub — LENGUAJES-DE-PROGRAMACI-N] https://github.com/sagtpv23-ux/SistemaRural-PE.git


## Actualización funcional (noviembre de 2026)

- Las fechas de nacimiento y de citas se escriben únicamente como `DD/MM/AAAA` (por ejemplo, `20/11/2000`); cualquier otro formato (`2000-11-20`, `5/1/2000`) se rechaza con un mensaje claro. En las tablas, las fechas se muestran también como `DD/MM/AAAA`.
- La pestaña **Recetas** permite seleccionar un paciente y un médico y armar una receta con uno o más medicamentos.
- Solo el personal con rol **Médico** puede emitir recetas; al emitirla se descuenta el stock («todo o nada»).
- El respaldo cifrado incluye las recetas y sus detalles.

### Ejecutar y probar

```bash
python -m pip install -r requirements.txt
python -m sistema_rural.ui_tkinter
pytest -v
```

### Formato de una línea de receta

| Campo | Ejemplo ficticio |
|---|---|
| Medicamento | Paracetamol 500 mg |
| Cantidad | 9 |
| Indicaciones | 1 tableta cada 8 horas por 3 días, después de los alimentos |

Los ejemplos son demostrativos y no constituyen indicaciones médicas reales.

## Calidad del código: principios SOLID y buenas prácticas

### Principios SOLID aplicados

| Principio | Dónde se ve en el código | Prueba que lo respalda |
|---|---|---|
| **S** — Responsabilidad única | `reportes.py` solo calcula reportes; `seguridad.py` solo protege datos; `controlador.py` solo traduce formularios en operaciones del dominio; `ui_tkinter.py` solo dibuja y captura acciones. | `test_controlador.py` prueba la lógica sin abrir la ventana. |
| **O** — Abierto/cerrado | `PersonalFactory.registrar_tipo()` permite añadir un rol nuevo sin modificar `crear()` ni a quienes la usan; el `BusEventos` admite oyentes nuevos sin tocar el inventario. | `test_factory_rechaza_tipo_desconocido_y_admite_tipos_nuevos`, `test_evento_stock_bajo_notifica_al_oyente`. |
| **L** — Sustitución de Liskov | `Medico` y `Enfermero` se usan donde se espera un `PersonalSalud`: `RegistroCentral.emitir_receta()` solo consulta `puede_prescribir()` y funciona con cualquier subclase. Los errores de duplicado heredan de `RegistroDuplicadoError`. | `test_polimorfismo_y_factory`, `test_enfermero_no_puede_emitir_recetas`, `test_personal_duplicado_lanza_su_propio_error`. |
| **D** — Inversión de dependencias | `ControladorSistema(registro=None)` recibe el registro por parámetro en lugar de crearlo a la fuerza; el inventario notifica por eventos y no conoce la ventana. | `test_controlador_funciona_con_un_registro_inyectado` usa un registro falso sin tocar el real. |

### Buenas prácticas con ejemplos

1. **Validar en la frontera:** `validaciones.py` revisa cada dato antes de que entre al dominio y la interfaz bloquea teclas inválidas con los filtros `permitir_*`.
2. **Excepciones propias, en español, con jerarquía:** `excepciones.py` define `ErrorSistemaRural` y sus derivadas (`StockInsuficienteError`, `PermisoDenegadoError`…); la interfaz las captura en un solo punto (`_ejecutar`) y muestra un mensaje al usuario sin cerrar el programa.
3. **Inmutabilidad hacia afuera:** `pacientes`, `citas`, `diagnosticos` y `detalles` se entregan como tuplas, de modo que el código externo no puede alterar el estado interno.
4. **Sin secretos en el código:** la sal del DNI sale del entorno o es aleatoria (`seguridad.leer_sal`), y `.gitignore` excluye `.env` y los respaldos `*.bin`.
5. **Operaciones «todo o nada»:** `emitir_receta()` comprueba el stock de todas las líneas antes de descontar cualquiera.
6. **Registro de fallos con `logging`:** un oyente defectuoso se registra en el log y no interrumpe a los demás (`BusEventos.publicar`).
7. **Pruebas independientes:** el fixture `registro_limpio` reinicia el Singleton antes de cada prueba, así que ninguna depende del orden de ejecución.

## Consecuencias para los usuarios de una baja calidad o una exposición de datos

Los usuarios del sistema son los **profesionales de salud** que lo operan y los **pacientes** cuyos datos se guardan. Los datos de salud son datos sensibles según la Ley N.° 29733.

| Falla posible | Consecuencia concreta | Control en el código |
|---|---|---|
| DNI y diagnóstico visibles en reportes o respaldos | Un paciente podría sufrir discriminación o suplantación de identidad, y perder la confianza en el centro de salud, con lo que evitaría atenderse. El establecimiento respondería ante la normativa de protección de datos. | El DNI se guarda como hash HMAC y enmascarado (`****0002`); los diagnósticos solo salen en el respaldo cifrado con Fernet (`test_dni_no_queda_en_texto_plano`, `test_exportacion_cifrada_no_contiene_datos_legibles`). |
| Sal fija y conocida en el código | Cualquiera con el repositorio podría recuperar los DNI de los hashes probando combinaciones. | Sal por variable de entorno o aleatoria (`test_la_sal_viene_del_entorno_o_es_aleatoria`). |
| Dos citas del mismo profesional a la misma hora | Un paciente rural puede viajar horas hasta el centro y no ser atendido. | `CitaConflictoError` (`test_conflicto_de_citas_del_mismo_personal`). |
| Stock mal descontado o receta parcial | Se recetaría un medicamento que ya no hay, o el inventario quedaría inconsistente y faltaría medicina para otros pacientes. | Receta «todo o nada» (`test_receta_es_todo_o_nada_si_falta_stock`) y alerta de stock crítico por evento. |
| Un enfermero emite recetas | Una prescripción sin autorización puede dañar al paciente y comprometer legalmente al profesional. | `puede_prescribir()` y `PermisoDenegadoError` (`test_enfermero_no_puede_emitir_recetas`). |
| Datos inválidos (fechas o cantidades absurdas) | Edades erróneas en los reportes, o cantidades que corrompen el inventario. | Validaciones en la entrada (`test_formularios_rechazan_fechas_horas_y_motivos_invalidos`, `test_cantidades_solo_enteros_positivos_en_rango`). |
| Cerrar el programa sin respaldar | Se pierde el trabajo del día, porque los datos viven en memoria. | Aviso al cerrar (`test_aviso_de_cambios_sin_guardar_hasta_exportar_respaldo`). |

**Límites que conviene reconocer:** el prototipo no tiene inicio de sesión, así que cualquiera que abra la ventana puede operar; tampoco registra el consentimiento del paciente ni persiste los datos. Son riesgos reales para un uso clínico y están en la lista de mejoras futuras.
