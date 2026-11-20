# AURA · Laboratorio RAG IA — V2

Aplicación web de aspecto SaaS basada en la práctica original, con **Streamlit + Gemini + Pinecone**, sin instalación de software en la computadora de los estudiantes.

## Características

- Chat conversacional con caja de escritura fija abajo e historial visual durante la sesión.
- Subida de PDF, DOCX y TXT, extracción de texto e indexación en Pinecone.
- Estados de archivo: indexado o error, y barra de avance por fragmento.
- Biblioteca de documentos con tamaño, fecha, número de fragmentos y **vista previa del texto extraído**.
- **Eliminar un documento de Pinecone** mediante todos sus IDs vectoriales, o **eliminar todos los documentos** de la sesión con confirmación.
- Fuentes recuperadas por pregunta, valor de similitud y panel de inspección.
- Parámetros editables: top-k y temperatura de generación.
- Namespace diferente por sesión de Streamlit para aislar consultas entre navegadores.
- Estética oscura, transparencias, tarjetas y diseño responsive de Streamlit.

## Publicación en tu aplicación actual (sin crear una nueva)

1. Guarda una copia de tu actual `streamlit_app.py` de GitHub antes de sustituirlo.
2. Descomprime este ZIP.
3. Abre el repositorio GitHub vinculado a tu app en Streamlit Cloud.
4. **Reemplaza el archivo `streamlit_app.py`** por el de este proyecto (mismo nombre y ubicación raíz).
5. Actualiza/añade **`requirements.txt`** en la raíz del repositorio.
6. Crea/actualiza **`.streamlit/config.toml`** dentro de la carpeta `.streamlit`.
7. Guarda con **Commit changes**. Streamlit Community Cloud generalmente vuelve a desplegar la versión nueva automáticamente.
8. En `https://share.streamlit.io`, abre tu app > menú ⋮ > **Settings > Secrets**. Conserva las claves existentes:

   ```toml
   GEMINI_API_KEY = "TU_CLAVE_REAL"
   PINECONE_API_KEY = "TU_CLAVE_REAL"
   ```

   **Nunca** pongas las claves reales en GitHub. `secrets.example.toml` es solo una plantilla.
9. Abre tu dirección `.streamlit.app` y comienza con un archivo pequeño de texto seleccionable.

## Cómo usarlo

1. **Subir:** abre la barra lateral, selecciona PDF/DOCX/TXT y pulsa «Procesar documentos».
2. **Comprobar:** en la biblioteca derecha aparecerán la etiqueta «Indexado», el total de fragmentos, una vista previa y la opción de eliminar.
3. **Consultar:** usa el cuadro de chat inferior, por ejemplo «Resume este archivo».
4. **Verificar:** expande «Consultar fuentes utilizadas» o inspecciona el panel «Fuentes de la última respuesta».
5. **Eliminar uno:** pulsa «Eliminar» bajo su tarjeta. Se llama a Pinecone para borrar los IDs de sus vectores, no solo a ocultar la tarjeta.
6. **Vaciar biblioteca:** desde la barra izquierda pulsa «Eliminar todos los documentos» y confirma.
7. **Limpiar chat:** borra solo la conversación; los vectores permanecen almacenados.

## Cómo funciona

`Archivos → extracción de texto → fragmentos (350 caracteres aprox.) → Gemini gemini-embedding-001 → Pinecone 3072 dimensiones / cosine → top-k → contexto → Gemini gemini-3.5-flash → chat`.

El índice utilizado sigue siendo **`documentos-tae2026-01`** y el entorno AWS `us-east-1`. No se cambia la estructura de los embeddings. Se mantiene la lógica original de dividir por puntos; se añade soporte de texto de tablas DOCX.

## Consideraciones importantes

- La **separación por namespace es por sesión del navegador**, no equivale a una cuenta de usuario ni a control de acceso fuerte.
- Los **documentos indexados persisten en Pinecone**. Eliminar un documento o vaciar la biblioteca borra sus vectores; cerrar el navegador o limpiar el chat **no los borra**. Si la sesión desaparece sin eliminarlos, quedan huérfanos y se deberá hacer limpieza administrativa desde Pinecone. Para un despliegue permanente con muchos alumnos, conviene implementar autenticación y política de retención.
- La eliminación de Pinecone puede tardar brevemente en reflejarse en las búsquedas debido a consistencia eventual.
- La app almacena el **texto extraído** de los documentos en la memoria de sesión para la vista previa, y fragmentos en los metadatos de Pinecone. No subas información confidencial.
- No se admite OCR de PDFs escaneados. El tamaño máximo dentro de esta app es **15 MB por archivo**.
- Los límites y costos de Gemini, Pinecone y Streamlit dependen de sus planes y cuotas. El hosting puede ser gratuito, pero no garantiza uso ilimitado de APIs.
- Si el modelo `gemini-3.5-flash` deja de estar disponible para tu clave, actualiza `CHAT_MODEL` al modelo habilitado por Google para tu cuenta.
- El sistema es un **asistente documental RAG**, no un agente autónomo con herramientas externas.

## Archivos

- `streamlit_app.py` — aplicación completa V2.
- `requirements.txt` — librerías para Cloud.
- `.streamlit/config.toml` — apariencia y carga de archivos.
- `secrets.example.toml` — ejemplo SIN claves reales.
- `.gitignore` — evita publicar credenciales locales.

## Solución de problemas

- **No responde Gemini:** revisa `Settings > Secrets`, disponibilidad de `gemini-3.5-flash` y Logs de Streamlit.
- **No se puede indexar:** consulta «Archivos con incidencias». Los PDFs escaneados no tienen texto extraíble.
- **Se perdieron documentos al recargar:** el estado de Streamlit es temporal; el namespace anterior sigue existiendo en Pinecone. La nueva sesión no puede recuperarlo automáticamente.
- **Error de dimensión:** el índice debe ser de 3072 dimensiones para usar `gemini-embedding-001` como configurado.
- **Eliminar no parece inmediato:** Pinecone puede presentar demoras de consistencia; vuelve a consultar después.
