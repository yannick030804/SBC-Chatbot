# Movie and Series Chatbot

Aplicacion web con Flask para recomendar peliculas y series usando TMDB. El chatbot guarda usuarios, historial de chat, preferencias por usuario y estado de conversacion para poder tener una experiencia mas natural.

## Que hace

- Permite registrar usuarios e iniciar sesion.
- Guarda el historial de chat por usuario.
- Guarda titulos por usuario como `watched`, `liked`, `favorite` o `disliked`.
- Mantiene estado de conversacion, por ejemplo cuando pregunta si quieres pelicula o serie.
- Usa TMDB para buscar titulos, obtener informacion y recomendar peliculas/series.
- Resuelve titulos ambiguos como `Star Wars` preguntando cual quieres decir.
- Soporta recomendaciones por genero, mood, tipo, duracion, director y actor.

## Requisitos

Necesitas tener instalado:

- Python 3.10 o superior.
- PostgreSQL.
- Una API key de TMDB.

La API key se consigue creando una cuenta en TMDB y generando una clave en la seccion de API.

## Instalacion

Ejecuta todo desde la raiz del proyecto:

```bash
cd "/Users/yannicksuchy/La Salle 2025 - 2026/SBC/Practica/SBC-Chatbot"
```

Crea y activa un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instala dependencias:

```bash
pip install -r requirements.txt
```

Prepara el archivo de variables de entorno:

```bash
cp .env.example .env
```

Edita `.env` y pon tu API key de TMDB:

```env
TMDB_API_KEY=your_real_tmdb_api_key
```

Tambien configura PostgreSQL. Puedes hacerlo con una URL completa:

```env
DATABASE_URL=postgresql+psycopg2://your_postgres_user@localhost:5432/sbc_chatbot
```

O con variables separadas:

```env
PGUSER=your_postgres_user
PGPASSWORD=your_postgres_password
PGHOST=localhost
PGPORT=5432
PGDATABASE=sbc_chatbot
```

Si tu usuario local de PostgreSQL no tiene password y la base de datos se llama `sbc_chatbot`, puedes dejar solo:

```env
TMDB_API_KEY=your_real_tmdb_api_key
PGDATABASE=sbc_chatbot
```

## Base de datos

Crea la base de datos en PostgreSQL:

```bash
createdb sbc_chatbot
```

Comprueba la conexion:

```bash
python3 database.py
```

Crea las tablas:

```bash
python3 models.py
```

Tambien se crean automaticamente al arrancar `app.py`, pero ejecutar `models.py` sirve para comprobar que todo esta bien.

## Arrancar la aplicacion

Desde la raiz del proyecto, con el entorno virtual activado:

```bash
python3 app.py
```

Abre el navegador en:

```text
http://127.0.0.1:5001
```

Primero registra un usuario en `/register`, luego inicia sesion en `/login`.

## Estructura del proyecto

```text
app.py                 Rutas Flask, login, registro, chat y reset
database.py            Conexion a PostgreSQL
models.py              Modelos SQLAlchemy y creacion de tablas
src/chatbot.py         Logica principal del chatbot y estado conversacional
src/processing.py      Deteccion de intenciones, titulos, filtros y preferencias
src/tmdb.py            Integracion con la API de TMDB
templates/             HTML de login, registro y chat
static/style.css       Estilos de la interfaz
requirements.txt       Dependencias Python
.env.example           Plantilla de variables de entorno
```

## Como funciona por dentro

Cuando el usuario envia un mensaje, Flask llama a:

```python
process_user_message(user_message, db=db, user_id=user_id)
```

El flujo principal es:

1. Detecta intencion: saludo, recomendacion, informacion, liked, watched, favorite, disliked, another one.
2. Extrae preferencias: tipo, genero, mood, duracion, ano, director, actor y titulos.
3. Consulta TMDB si necesita buscar titulos, informacion o recomendaciones.
4. Guarda cambios en la base de datos si el usuario ha dicho que vio/gusto/favorito/no gusto un titulo.
5. Actualiza el estado de conversacion si necesita hacer una pregunta intermedia.
6. Devuelve una respuesta natural para mostrar en el chat.

## Tablas principales

`users`

- Guarda usuarios registrados.
- Tiene `username`, `email` y `password_hash`.

`chat_messages`

- Guarda cada mensaje del usuario y del bot.
- Permite mantener el historial por usuario.

`user_titles`

- Guarda la libreria personal de cada usuario.
- Campos importantes: `watched`, `liked`, `favorite`, `disliked`.

`conversation_states`

- Guarda si el bot esta esperando una respuesta concreta.
- Ejemplos: esperando tipo (`movie` o `series`), esperando mood, o esperando seleccion de titulo ambiguo.

## Ejemplos para probar

Saludo:

```text
Hello
```

Recomendacion sin datos guardados:

```text
Recommend me something
```

El bot deberia pedir algunos titulos que te gusten.

Guardar gustos y resolver ambiguedad:

```text
Interstellar, Star Wars
```

El bot deberia guardar `Interstellar` y preguntar que `Star Wars` quieres decir. Luego puedes responder:

```text
1
```

Pedir otra recomendacion:

```text
Another one
```

Guardar dislike:

```text
I did not like Inception
```

Guardar favorito:

```text
Dark is one of my favorites
```

Recomendacion por genero/tipo:

```text
Recommend me a sci-fi movie please
```

Recomendacion por director:

```text
Recommend me a Christopher Nolan movie please
```

Recomendacion por director y duracion:

```text
Recommend me a long Christopher Nolan movie
```

Recomendacion por actor:

```text
Recommend me a movie with Leonardo DiCaprio
```

Recomendacion por genero y actor:

```text
I want a horror movie with Toni Collette
```

Informacion sobre un titulo:

```text
Tell me about Interstellar
```

## Demo con dos usuarios

Para demostrar que la base de datos separa la informacion por usuario:

1. Crea un usuario `demo1`.
2. Prueba mensajes como `Interstellar, Star Wars`, `1`, `Dark is one of my favorites`.
3. Mira la libreria lateral: deberian aparecer liked/watched/favorites.
4. Cierra sesion.
5. Crea otro usuario `demo2`.
6. Comprueba que la libreria esta vacia.
7. Prueba otros gustos, por ejemplo `Parasite, Breaking Bad`.

Cada cuenta tiene su propio historial, libreria y estado conversacional.

## Resetear datos durante pruebas

El boton `Reset chat` borra el historial de chat y el estado conversacional del usuario actual, pero no borra su libreria de titulos.

Si quieres borrar todos los datos de todas las tablas en PostgreSQL, puedes hacerlo con:

```bash
psql sbc_chatbot
```

Dentro de `psql`:

```sql
TRUNCATE TABLE conversation_states, chat_messages, user_titles, users RESTART IDENTITY CASCADE;
```

Sal de `psql` con:

```text
\q
```

## Problemas comunes

Si falta `TMDB_API_KEY`, el bot no podra consultar TMDB y muchas recomendaciones no funcionaran.

Si PostgreSQL no esta arrancado, `python3 app.py` fallara al conectar con la base de datos.

Si ves errores de columnas que no existen, probablemente la tabla ya existia con una estructura antigua. Para una demo limpia, borra las tablas o usa el comando `TRUNCATE` anterior si solo quieres borrar datos.

Si cambias codigo Python y la app ya estaba arrancada, reinicia Flask para asegurarte de probar la version nueva.

