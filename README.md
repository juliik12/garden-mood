# Garden Mood

Aplicación web emocional construida con Flask para registrar cómo te sentís cada día, guardar una nota personal y transformar ese historial en un jardín visual.

La idea del proyecto es combinar seguimiento emocional, una experiencia cálida y una representación visual simple: cada emoción registrada se convierte en una flor dentro del jardín del usuario.

## Qué hace

- Registro e inicio de sesión.
- Guardado de emociones por día.
- Nota personal asociada a cada registro.
- Jardín visual por fecha.
- Calendario emocional mensual.
- Sistema de racha diaria.
- Límite dinámico de registros por día según la racha.
- Persistencia local con archivos JSON.
- Validaciones básicas de seguridad.

## Funcionalidades principales

### 1. Registro diario emocional

Cada usuario puede registrar su estado emocional del día junto con:

- una emoción seleccionada
- una nota breve
- una imagen asociada a esa emoción

Los datos se guardan por fecha y luego pueden visualizarse dentro del jardín o en el calendario.

### 2. Jardín visual

Cada emoción registrada aparece como una flor dentro del jardín del día seleccionado.

Esto convierte el seguimiento emocional en una experiencia más visual, amable y personal.

### 3. Calendario emocional

La vista de calendario permite:

- navegar entre meses
- ver qué días tienen emociones registradas
- abrir una fecha específica
- revisar el jardín correspondiente a ese día

### 4. Sistema de racha

La app calcula si el usuario viene registrando emociones de forma continua.

- Si hoy ya registró una emoción, la racha se calcula desde hoy.
- Si hoy todavía no registró, la racha se calcula desde ayer.

La racha modifica el límite de entradas diarias:

- base: `5`
- bonus: `+1` cada 3 días de racha
- máximo bonus: `+3`

## Stack

- Backend: Flask
- Frontend: HTML + CSS embebido en templates
- Seguridad: sesiones Flask, hash de contraseñas con Werkzeug
- Persistencia: archivos JSON
- Assets visuales: imágenes estáticas para emociones y jardín

## Estructura del proyecto

```text
garden-mood/
├── app.py
├── README.md
├── static/
│   └── images/
│       ├── asco.png
│       ├── angustia.png
│       ├── calma.png
│       ├── enojo.png
│       ├── feliz.png
│       ├── frustracion.png
│       ├── jardin.jpeg
│       ├── miedo.png
│       ├── semilla.png
│       ├── tristeza.png
│       └── verguenza.png
└── templates/
    ├── calendario.html
    ├── index.html
    ├── jardin.html
    ├── login.html
    ├── navbar.html
    └── register.html
```

## Requisitos

- Python 3.10 o superior
- `pip`

## Instalación local

1. Cloná el repositorio:

```bash
git clone https://github.com/juliik12/garden-mood.git
cd garden-mood
```

2. Creá un entorno virtual:

```bash
python -m venv .venv
```

3. Activá el entorno virtual:

### Windows

```powershell
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
source .venv/bin/activate
```

4. Instalá dependencias:

```bash
pip install flask
```

5. Configurá la variable de entorno `SECRET_KEY`:

### Windows

```powershell
$env:SECRET_KEY="cambia_esto_por_un_valor_largo_y_seguro"
```

### Linux / macOS

```bash
export SECRET_KEY="cambia_esto_por_un_valor_largo_y_seguro"
```

6. Ejecutá la app:

```bash
python app.py
```

La aplicación se levanta por defecto en:

`http://127.0.0.1:5000`

## Variables de entorno

- `SECRET_KEY`
  Obligatoria. Se usa para la sesión de Flask.

## Persistencia de datos

La app usa dos archivos JSON en la raíz del proyecto:

- `users.json`
- `emociones.json`

Si no existen, se crean automáticamente al iniciar el flujo de uso.

Esto hace que el proyecto sea simple de correr y probar, sin necesidad de base de datos externa.

## Seguridad implementada

El proyecto incluye una base de seguridad razonable para una app simple:

- contraseñas hasheadas con `generate_password_hash`
- validación de login
- `login_required` para rutas privadas
- rate limit simple por IP en login
- cookies de sesión con:
  - `HttpOnly`
  - `Secure`
  - `SameSite=Lax`
- lock de escritura para evitar corrupción de JSON en escrituras simultáneas

## Rutas principales

- `GET /login`
  Pantalla de inicio de sesión.

- `GET /registro`
  Pantalla de registro.

- `GET /`
  Vista principal del día, con formulario de emociones y nota.

- `GET /calendario`
  Calendario emocional por mes.

- `GET /jardin/<fecha>`
  Jardín visual para la fecha elegida.

- `POST /logout`
  Cierre de sesión.

## Experiencia del usuario

La app está pensada para sentirse:

- cálida
- visual
- íntima
- simple de usar

En lugar de mostrar los registros como una lista fría, los transforma en un jardín emocional con una identidad propia.

## Limitaciones actuales

- Los datos se guardan en JSON, por lo que no es ideal para escalar a muchos usuarios.
- No hay panel administrativo.
- No hay exportación de datos.
- No hay recuperación de contraseña.
- La seguridad está pensada para un proyecto personal o académico, no para un entorno de alto tráfico.

## Nota importante para desarrollo local

En `app.py`, la configuración actual usa:

```python
SESSION_COOKIE_SECURE=True
```

Eso significa que la cookie de sesión está pensada para HTTPS.

Si estás probando la app en local con `http://127.0.0.1:5000`, puede que el login no persista correctamente en algunos entornos. Para desarrollo local, podés cambiar temporalmente esa línea a:

```python
SESSION_COOKIE_SECURE=False
```

Y volver a activarla en producción o cuando uses HTTPS.

## Ideas de mejora futuras

- migrar persistencia de JSON a SQLite o PostgreSQL
- agregar gráficos o métricas emocionales
- permitir edición y eliminación de entradas
- sumar categorías o etiquetas para notas
- mejorar accesibilidad y responsive
- separar estilos en archivos CSS dedicados
- agregar tests

## Licencia

No se especifica una licencia en este repositorio.

