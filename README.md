# SistemaRural-PE

SistemaRural-PE es un sistema local de gestión para establecimientos de salud rurales del Perú. El proyecto plantea una alternativa modular para registrar pacientes y personal de salud, administrar citas, controlar el inventario de medicamentos y generar reportes, incluso en entornos con conectividad limitada.

## Problema que aborda

El caso estudiado considera al Centro de Salud Rural «Santa Rosa», ubicado en el distrito de Chugur, Cajamarca. El registro manual de la atención puede ocasionar duplicidad de pacientes, conflictos en la programación de citas, demoras y pérdida de información.

SistemaRural-PE reúne las operaciones principales en una aplicación de escritorio que funciona localmente y organiza el código por responsabilidades.

## Funcionalidades

- **Pacientes:** registro con validación del DNI de 8 dígitos y rechazo de registros duplicados.
- **Personal de salud:** registro y diferenciación de médicos y enfermeros mediante sus roles.
- **Citas:** programación, atención y cancelación; se impiden citas simultáneas del mismo profesional. Las fechas se ingresan y muestran como DD/MM/AAAA.
- **Recetas médicas:** emisión por médicos, asociadas a un paciente y opcionalmente a una cita. Cada receta registra medicamento, dosis, frecuencia, duración, cantidad e indicaciones.\n- **Alertas:** confirmaciones visuales para el registro de pacientes, citas y recetas; los errores se muestran sin cerrar el programa.\n- **Inventario:** registro y control de medicamentos, validación de cantidades y alertas cuando el stock llega a un nivel crítico.
- **Permisos por rol:** la dispensación de medicamentos está restringida al personal médico.
- **Reportes:** resumen de citas por estado, citas por día, edad promedio y medicamentos con stock crítico.
- **Respaldo:** exportación cifrada de la información mediante Fernet.
- **Interfaz gráfica:** aplicación de escritorio con pestañas para Pacientes, Personal, Citas, Inventario y Reportes.

## Tecnologías y paradigmas

| Elemento -> Uso en el proyecto |
| Python 3.12 o superior -> Lenguaje principal |
| Tkinter -> Interfaz gráfica de escritorio |
| pytest -> Pruebas automatizadas |
| cryptography (Fernet) -> Cifrado de respaldos |
| HMAC-SHA256 -> Protección del identificador DNI |
| Git y GitHub -> Control de versiones y trabajo colaborativo |
| Programación orientada a objetos -> Modelado de pacientes, personal, citas e inventario |
| Programación funcional -> Validaciones y generación de reportes con `map`, `filter`, `reduce` y `lambda` |
| Programación orientada a eventos -> Comunicación entre módulos y notificaciones mediante Observer |
| Programación estructurada -> Punto de entrada y demostración del sistema |

### Patrones de diseño

- **Singleton — `RegistroCentral`:** mantiene una única instancia como fuente central de los datos en memoria.
- **Factory — `PersonalFactory`:** centraliza la creación de los tipos de personal de salud.
- **Observer — `BusEventos`:** permite publicar y atender eventos, como `stock_bajo`, sin acoplar el inventario a la interfaz gráfica.

## Arquitectura y estructura del repositorio

La estructura principal del programa es:

l_programación/
├── docs/
│   ├── DiagramaUML.png
│   └── Diagrama_Secuencia.png
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
cd LENGUAJES-DE-PROGRAMACI-N/l_programación
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

El informe del proyecto documenta **53 pruebas automatizadas aprobadas**:

| Archivo de prueba | Casos | Enfoque |
|---|---:|---|
| `test_validaciones.py` | 9 | Validación de nombres, DNI, fechas, colegiatura, diagnósticos, medicamentos y cantidades. |
| `test_seguridad.py` | 3 | Hash y enmascaramiento del DNI; cifrado, descifrado y manejo de claves incorrectas. |
| `test_modelos.py` | 5 | Modelos, herencia, polimorfismo, Factory, propiedades y reglas del dominio. |
| `test_registro.py` | 7 | Singleton, duplicados, conflictos de citas, permisos, inventario y eventos. |
| `test_reportes.py` | 3 | Reportes por estado y día, resumen y protección del DNI. |
| `test_controlador.py` | 14 | Flujos de la aplicación, validaciones desde formularios, reportes y exportación. |
| **Total** | **53** | |

Para ejecutar un archivo de pruebas específico:

```bash
pytest tests/test_modelos.py -v
```

El informe también registra una cobertura del 97 % en la lógica del sistema y del 59 % a nivel global; la interfaz gráfica se verifica manualmente y mediante las pruebas de su controlador.

## Distribución de módulos entre los integrantes

| Integrante | Módulos y archivos asignados | Responsabilidad principal |
|---|---|---|
| **Arias Correa, Evelin Milagritos** | `modelos.py`, `fabricas.py`, `tests/test_modelos.py` | Modelado de entidades, herencia, polimorfismo y creación de personal mediante Factory. |
| **Luicho Mosqueira, Hector Alexander** | `seguridad.py`, `validaciones.py`, `tests/test_seguridad.py`, `tests/test_validaciones.py` | Validación de entradas y protección del DNI; hash, enmascaramiento y cifrado de respaldos. |
| **Malca Malca, Ivan Edilberto** | `registro.py`, `eventos.py`, `excepciones.py`, `tests/test_registro.py` | Registro central, patrón Singleton, eventos Observer, reglas de coordinación y excepciones del dominio. |
| **Mosqueira Tanta, Saul Alexander** | `controlador.py`, `ui_tkinter.py`, `main.py`, `tests/test_controlador.py` | Integración de la lógica con la interfaz, formularios, pestañas y ejecución de la aplicación. |
| **Valdez Quiroz, Victor Paul** | `reportes.py`, `tests/test_reportes.py`, `docs/` y `README.md` | Reportes funcionales, documentación técnica y actualización de diagramas y guía del repositorio. |

## Limitaciones y mejoras futuras

De acuerdo con el informe, el prototipo presenta las siguientes limitaciones:

- **Persistencia parcial:** los datos se mantienen en memoria y existe exportación cifrada, pero no hay una base de datos ni recarga automática de respaldos al reiniciar.
- **Autenticación pendiente:** no existe inicio de sesión ni control de acceso por cuenta de usuario.
- **Gestión de claves:** la sal y las claves dependen de variables de entorno y no cuentan con rotación automática.
- **Consentimiento digital pendiente:** el registro del consentimiento informado no está integrado en el sistema.
- **Interfaz:** la ventana gráfica no cuenta con pruebas automatizadas directas.

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

- Las fechas de nacimiento y citas aceptan el formato peruano `DD/MM/AAAA` (por ejemplo, `20/11/2000`). Para mantener compatibilidad con pruebas y datos anteriores, también se acepta `AAAA-MM-DD`.
- En las tablas, las fechas se muestran como `DD/MM/AAAA`.
- Se incorporó la pestaña **Recetas**, que permite seleccionar un paciente y un médico, asociar opcionalmente una cita y registrar un detalle de medicamento.
- Solo el personal con rol **Médico** puede emitir recetas. El sistema no dispensa medicamentos automáticamente al registrar una receta.
- El respaldo cifrado ahora incluye las recetas y sus detalles.
- Se agregaron pruebas de formato de fecha y del flujo de recetas. Resultado de la suite ejecutada durante esta actualización: **42 pruebas aprobadas**.

### Ejecutar y probar

```bash
python -m pip install -r requirements.txt
python -m sistema_rural.ui_tkinter
pytest -v
```

### Formato del detalle de receta

| Campo | Ejemplo ficticio |
|---|---|
| Medicamento | Paracetamol 500 mg |
| Dosis | 1 tableta |
| Frecuencia | Cada 8 horas |
| Duración | 3 días |
| Cantidad | 9 |
| Indicaciones | Tomar después de los alimentos |

Los ejemplos son demostrativos y no constituyen indicaciones médicas reales.