"""Laboratorio RAG IA · V2 — Streamlit + Gemini + Pinecone.

Conserva el flujo del notebook original: documentos -> fragmentos -> embeddings
-> Pinecone -> recuperación semántica -> respuesta con Gemini.
"""
from __future__ import annotations

import hashlib
import io
import re
import unicodedata
import uuid
from datetime import datetime, timezone

import streamlit as st
from docx import Document
from google import genai
from google.genai import types
from pinecone import Pinecone, ServerlessSpec
from pypdf import PdfReader

st.set_page_config(
    page_title="AURA | Laboratorio RAG IA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Conservamos los modelos y las características del proyecto que ya funciona.
EMBED_MODEL = "gemini-embedding-001"
CHAT_MODEL = "gemini-3.5-flash"
INDEX_NAME = "documentos-tae2026-01"
DIMENSIONS = 3072
BATCH_SIZE = 25
MAX_UPLOAD_MB = 15  # Límite por archivo de esta práctica, no de Streamlit.

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { color-scheme: dark; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { font-family:'DM Sans', sans-serif; }
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(ellipse 70% 55% at 75% -10%, rgba(65,90,185,.22), transparent 67%),
    radial-gradient(ellipse 50% 50% at 2% 75%, rgba(15,184,186,.11), transparent 72%),
    #090f1f;
  color:#eaf1ff;
}
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] {
  background:linear-gradient(180deg, rgba(15,25,46,.98), rgba(9,16,34,.98));
  border-right:1px solid rgba(172,194,241,.12);
}
[data-testid="stSidebar"] * { color:#e5edff; }
[data-testid="stMainBlockContainer"] { padding-top:1.1rem; padding-bottom:7rem; max-width:1550px; }
.block-container { max-width:1550px; }
h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.035em; }
.stButton button, .stDownloadButton button {
  border-radius:12px; font-weight:700; border:1px solid rgba(151,174,218,.21);
  background:rgba(121,152,215,.09); color:#e5edff; transition:all .18s ease;
}
.stButton button:hover, .stDownloadButton button:hover { border-color:#799cf5; background:rgba(81,112,207,.20); color:white; }
.stButton button[kind="primary"] { background:linear-gradient(110deg,#5b78ec,#7866dd); color:white; border:0; box-shadow:0 9px 25px #4865d32b; }
[data-testid="stFileUploader"] { border-radius:16px; }
[data-testid="stFileUploaderDropzone"] { border:1px dashed rgba(123,154,228,.55); background:rgba(111,150,230,.065); border-radius:15px; }
[data-testid="stChatMessage"] {
  background:rgba(18,31,54,.60); border:1px solid rgba(171,195,244,.11);
  border-radius:18px; padding:15px 17px; margin-bottom:12px;
  box-shadow:0 9px 35px #0208171f;
}
[data-testid="stChatInput"] { border:1px solid rgba(116,155,234,.5); border-radius:16px; background:rgba(15,26,49,.97); box-shadow:0 0 36px #0a153c70; }
[data-testid="stChatInput"] textarea { color:#eef4ff !important; }
[data-testid="stMetric"] { background:rgba(20,34,60,.72); padding:13px 17px; border-radius:15px; border:1px solid rgba(170,193,241,.1); }
[data-testid="stMetricValue"] { color:#eaf0ff; }
[data-testid="stExpander"] { border:1px solid rgba(166,193,242,.16); border-radius:14px; background:rgba(21,35,59,.45); }
[data-testid="stAlert"] { border-radius:14px; }
hr { border-color:rgba(170,193,241,.12) !important; }
.aura-top {display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:20px;}
.aura-logo { font-family:'Manrope',sans-serif; font-size:30px; font-weight:800; letter-spacing:-.065em; }
.aura-glyph { color:#90a8ff; margin-right:7px; }
.aura-sub { font-size:12px; color:#96a7c6; letter-spacing:.09em; text-transform:uppercase; font-weight:700; }
.aura-online {border:1px solid #28785d;color:#76e9b3;background:#0e392a7a;border-radius:99px;padding:7px 13px;font-size:12px;font-weight:700;white-space:nowrap;}
.aura-hero {border:1px solid rgba(147,175,238,.2);border-radius:23px;padding:27px 29px; margin:10px 0 22px;
  background:linear-gradient(118deg,rgba(71,91,158,.23),rgba(20,44,72,.5) 65%,rgba(21,78,101,.2)); box-shadow:0 20px 50px #040b1f35;}
.aura-kicker {color:#a3b6e2;font-size:12px;text-transform:uppercase;letter-spacing:.15em;font-weight:800;}
.aura-hero h1 {font-size:clamp(25px,3vw,39px);line-height:1.13;margin:12px 0;color:#f4f7ff;}
.aura-hero p { color:#aabbd6; margin:0; font-size:14px;line-height:1.7; max-width:760px;}
.aura-section {font-family:'Manrope',sans-serif;font-weight:800;font-size:17px;margin:7px 0 14px;color:#edf3ff;}
.aura-card {background:rgba(21,34,58,.67);border:1px solid rgba(163,185,228,.14);border-radius:17px;padding:17px 18px;margin-bottom:12px;}
.aura-card-title {font-size:14px;font-weight:750;color:#f0f4ff;overflow-wrap:anywhere;}
.aura-muted {color:#97a9c8;font-size:12px;line-height:1.6;}
.aura-pill {display:inline-block;background:rgba(49,173,130,.13);border:1px solid rgba(69,196,148,.3);border-radius:100px;padding:4px 10px;color:#7eebbd;font-size:11px;font-weight:750;}
.aura-error-pill {display:inline-block;background:#6b302b50;border:1px solid #a75b52;border-radius:100px;padding:4px 10px;color:#ffaaa1;font-size:11px;font-weight:700;}
.aura-empty {border:1px dashed rgba(155,181,236,.28);border-radius:19px;text-align:center;padding:32px 20px;background:rgba(18,32,57,.28);}
.aura-empty-icon {font-size:35px;color:#a0b7fd;}
.aura-empty h3 {margin:10px 0 7px;font-size:21px;}
.aura-empty p {max-width:450px;color:#9badca;font-size:13px;line-height:1.6;margin:0 auto;}
.aura-footer {color:#63789e;font-size:11px;text-align:center;margin:25px 0 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def bootstrap_state() -> None:
    """Datos por sesión del navegador; no son cuentas de usuario."""
    defaults = {
        "namespace": f"alumno-{uuid.uuid4().hex[:20]}",
        "historial": [],
        "documentos": {},  # hash SHA256 -> ficha con ids de vectores, texto y estado
        "errores_archivos": {},
        "ultima_fuente": [],
        "consultas": 0,
        "subidas_version": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def normalizar_id(valor: str) -> str:
    valor = unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9_-]", "_", valor)).strip("_") or "documento"


def extraer_texto(nombre: str, datos: bytes) -> str:
    """Lee archivos sin escribirlos en disco; no realiza OCR."""
    n = nombre.lower()
    if n.endswith(".pdf"):
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(datos)).pages)
    if n.endswith(".docx"):
        doc = Document(io.BytesIO(datos))
        parrafos = [p.text for p in doc.paragraphs]
        # Añade texto de tablas (que no cubría el código original).
        for tabla in doc.tables:
            for fila in tabla.rows:
                parrafos.append(" | ".join(celda.text for celda in fila.cells))
        return "\n".join(parrafos)
    if n.endswith(".txt"):
        try:
            return datos.decode("utf-8-sig")
        except UnicodeDecodeError:
            return datos.decode("latin-1")
    raise ValueError("Formato no compatible. Usa PDF, DOCX o TXT.")


def crear_chunks(texto: str, max_chars: int = 350) -> list[str]:
    """Mantiene la división por puntos utilizada por el notebook original."""
    partes = texto.split(".")
    chunks: list[str] = []
    actual = ""
    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue
        frase = parte + ". "
        if len(actual) + len(frase) < max_chars:
            actual += frase
        else:
            if actual.strip():
                chunks.append(actual.strip())
            actual = frase
    if actual.strip():
        chunks.append(actual.strip())
    return chunks


@st.cache_resource(show_spinner=False)
def conectar(gemini_key: str, pinecone_key: str):
    return genai.Client(api_key=gemini_key), Pinecone(api_key=pinecone_key)


def obtener_indice(pc):
    """Crea el índice solo cuando es necesario, como en la versión original."""
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSIONS,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(INDEX_NAME)


def eliminar_ids(indice, ids: list[str], namespace: str) -> None:
    """Eliminación REAL de los vectores en Pinecone; lotes pequeños."""
    for inicio in range(0, len(ids), 200):
        indice.delete(ids=ids[inicio:inicio + 200], namespace=namespace)


def indexar_un_archivo(archivo, gemini, indice, namespace, progreso):
    """Devuelve la ficha del documento solo tras completar toda la indexación.

    Si falla una llamada, intenta revertir los vectores que ya se hayan subido.
    """
    datos = archivo.getvalue()
    if len(datos) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"El archivo supera {MAX_UPLOAD_MB} MB.")
    digest = hashlib.sha256(datos).hexdigest()
    if digest in st.session_state.documentos:
        raise ValueError("Este archivo ya está indexado en la sesión.")
    texto = extraer_texto(archivo.name, datos)
    if not texto.strip():
        raise ValueError("No contiene texto extraíble. Si es un PDF escaneado, requiere OCR.")
    chunks = crear_chunks(texto)
    if not chunks:
        raise ValueError("No se pudieron generar fragmentos.")

    doc_id = f"{normalizar_id(archivo.name)}-{uuid.uuid4().hex[:10]}"
    ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
    almacenados: list[str] = []
    lote = []
    try:
        for i, chunk in enumerate(chunks):
            embedding = gemini.models.embed_content(model=EMBED_MODEL, contents=chunk)
            lote.append({
                "id": ids[i],
                "values": embedding.embeddings[0].values,
                "metadata": {"texto": chunk, "doc": archivo.name, "doc_id": doc_id, "chunk": i},
            })
            if len(lote) >= BATCH_SIZE:
                indice.upsert(vectors=lote, namespace=namespace)
                almacenados.extend(v["id"] for v in lote)
                lote = []
            progreso.progress((i + 1) / len(chunks), text=f"{archivo.name} · fragmento {i+1}/{len(chunks)}")
        if lote:
            indice.upsert(vectors=lote, namespace=namespace)
            almacenados.extend(v["id"] for v in lote)
    except Exception:
        # Revertir incluso un lote ambiguo es más seguro usando TODOS los ids previstos.
        try:
            eliminar_ids(indice, ids, namespace)
        except Exception:
            st.warning("Falló también la limpieza automática. Revisa el namespace de Pinecone.")
        raise

    return digest, {
        "nombre": archivo.name,
        "doc_id": doc_id,
        "bytes": len(datos),
        "chunks": len(chunks),
        "ids": ids,
        "texto": texto,
        "fecha": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
        "estado": "Indexado",
    }


def recuperar(indice, gemini, pregunta: str, namespace: str, top_k: int):
    embed = gemini.models.embed_content(model=EMBED_MODEL, contents=pregunta)
    respuesta = indice.query(
        vector=embed.embeddings[0].values,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace,
    )
    fuentes = []
    for match in respuesta.matches:
        meta = match.metadata or {}
        if meta.get("texto"):
            fuentes.append({
                "documento": meta.get("doc", "Documento"),
                "fragmento": meta["texto"],
                "similitud": float(match.score) if match.score is not None else None,
            })
    return fuentes


def generar_respuesta(gemini, pregunta: str, fuentes: list[dict], temperatura: float) -> str:
    contexto = "\n\n".join(f["fragmento"] for f in fuentes)
    if not contexto:
        return "No encontré información en los documentos cargados para responder esa pregunta."
    prompt = f"""Usa EXCLUSIVAMENTE el siguiente contexto para responder.
CONTEXTO:\n{contexto}\n\nPREGUNTA:\n{pregunta}\n\nINSTRUCCIONES:
- No inventes información.
- No agregues detalles que no estén en el contexto.
- Responde de forma clara y directa.
- Si la respuesta no está en el contexto, dilo expresamente."""
    resultado = gemini.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperatura),
    )
    return resultado.text or "Gemini no devolvió texto."


def presentar_fuentes(fuentes: list[dict], key_prefix: str):
    if not fuentes:
        return
    with st.expander(f"↗ Consultar fuentes utilizadas ({len(fuentes)})", expanded=False):
        for i, fuente in enumerate(fuentes, 1):
            score = fuente["similitud"]
            encabezado = f"{i}. {fuente['documento']}"
            if score is not None:
                encabezado += f" · similitud {score:.3f}"
            st.markdown(f"**{encabezado}**")
            st.caption(fuente["fragmento"])
            if i < len(fuentes):
                st.divider()


bootstrap_state()

# Claves: exclusivamente Streamlit Secrets (nunca exponerlas en GitHub).
try:
    gemini_key = st.secrets["GEMINI_API_KEY"]
    pinecone_key = st.secrets["PINECONE_API_KEY"]
except (FileNotFoundError, KeyError):
    st.error("Configura GEMINI_API_KEY y PINECONE_API_KEY en Settings → Secrets de Streamlit Cloud.")
    st.stop()

try:
    gemini, pc = conectar(gemini_key, pinecone_key)
except Exception as error:
    st.error(f"No fue posible conectar con los servicios: {error}")
    st.stop()

# ────────────────────────────── PANEL LATERAL ──────────────────────────────
with st.sidebar:
    st.markdown('<div class="aura-logo"><span class="aura-glyph">✦</span>AURA<span style="color:#7184a8">.AI</span></div><div class="aura-sub">Laboratorio de inteligencia documental</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<span class="aura-pill">● Sistema preparado</span>', unsafe_allow_html=True)
    st.divider()

    st.markdown('**📥 Biblioteca de conocimiento**')
    archivos = st.file_uploader(
        "Sube tus archivos", type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key=f"subir_{st.session_state.subidas_version}",
        help=f"Hasta {MAX_UPLOAD_MB} MB por archivo. El PDF debe contener texto seleccionable.",
    )
    if st.button("✦ Procesar documentos", type="primary", use_container_width=True, disabled=not archivos):
        try:
            indice = obtener_indice(pc)
            nuevos = 0
            fallos = 0
            for archivo in archivos:
                progreso = st.progress(0, text=f"Preparando {archivo.name}...")
                try:
                    digest, ficha = indexar_un_archivo(archivo, gemini, indice, st.session_state.namespace, progreso)
                    st.session_state.documentos[digest] = ficha
                    st.session_state.errores_archivos.pop(archivo.name, None)
                    nuevos += 1
                except Exception as error:
                    st.session_state.errores_archivos[archivo.name] = str(error)
                    fallos += 1
                finally:
                    progreso.empty()
            st.session_state.subidas_version += 1  # limpia el uploader para evitar duplicados visuales
            if nuevos:
                st.toast(f"{nuevos} documento(s) indexado(s)", icon="✅")
            if fallos:
                st.toast(f"{fallos} archivo(s) con incidencias; revisa la biblioteca", icon="⚠️")
            st.rerun()
        except Exception as error:
            st.error(f"No se pudo abrir el índice: {error}")

    st.divider()
    st.markdown("**⚙️ Parámetros de consulta**")
    top_k = st.slider("Fragmentos a recuperar", min_value=1, max_value=10, value=4)
    temperatura = st.slider("Temperatura de Gemini", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
    st.caption(f"Modelo de chat: `{CHAT_MODEL}`")
    with st.expander("Ver configuración técnica"):
        st.code(f"Embedding: {EMBED_MODEL}\nDimensiones: {DIMENSIONS}\nÍndice: {INDEX_NAME}\nNamespace: {st.session_state.namespace}", language="text")

    st.divider()
    if st.button("↺ Limpiar conversación", use_container_width=True):
        st.session_state.historial = []
        st.session_state.ultima_fuente = []
        st.session_state.consultas = 0
        st.rerun()

    if st.button("🗑 Eliminar todos los documentos", use_container_width=True, disabled=not st.session_state.documentos):
        st.session_state.confirmar_borrado = True
    if st.session_state.get("confirmar_borrado", False):
        st.warning("Se eliminarán los vectores de todos los documentos de esta sesión en Pinecone.")
        a, b = st.columns(2)
        with a:
            if st.button("Confirmar borrado", type="primary", use_container_width=True):
                try:
                    indice = obtener_indice(pc)
                    indice.delete(delete_all=True, namespace=st.session_state.namespace)
                    st.session_state.documentos = {}
                    st.session_state.errores_archivos = {}
                    st.session_state.ultima_fuente = []
                    st.session_state.historial = []
                    st.session_state.consultas = 0
                    st.session_state.confirmar_borrado = False
                    st.session_state.subidas_version += 1
                    st.toast("Documentos eliminados de Pinecone", icon="✅")
                    st.rerun()
                except Exception as error:
                    st.error(f"No se pudieron eliminar los documentos: {error}")
        with b:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.confirmar_borrado = False
                st.rerun()

# ─────────────────────────────── VISTA PRINCIPAL ───────────────────────────
st.markdown('<div class="aura-top"><div><div class="aura-logo"><span class="aura-glyph">✦</span>AURA / Workspace</div><div class="aura-sub">Tu conocimiento, en conversación</div></div><span class="aura-online">● Gemini + Pinecone</span></div>', unsafe_allow_html=True)

n_docs = len(st.session_state.documentos)
n_chunks = sum(doc["chunks"] for doc in st.session_state.documentos.values())
c1, c2, c3 = st.columns(3)
c1.metric("DOCUMENTOS ACTIVOS", n_docs)
c2.metric("FRAGMENTOS INDEXADOS", n_chunks)
c3.metric("CONSULTAS EN ESTA SESIÓN", st.session_state.consultas)
st.write("")

principal, panel = st.columns([2.05, 1], gap="large")
with panel:
    st.markdown('<div class="aura-section">Biblioteca de documentos</div>', unsafe_allow_html=True)
    if not st.session_state.documentos and not st.session_state.errores_archivos:
        st.markdown('<div class="aura-empty"><div class="aura-empty-icon">▤</div><h3>Tu biblioteca está vacía</h3><p>Sube PDF, Word o TXT desde la barra izquierda para comenzar.</p></div>', unsafe_allow_html=True)

    for digest, doc in list(st.session_state.documentos.items()):
        tam_kb = doc["bytes"] / 1024
        st.markdown(
            f'<div class="aura-card"><div class="aura-card-title">📄 {doc["nombre"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</div>'
            f'<div class="aura-muted">{doc["chunks"]} fragmentos · {tam_kb:.1f} KB · {doc["fecha"]}</div>'
            f'<div style="margin-top:8px"><span class="aura-pill">✓ Indexado</span></div></div>', unsafe_allow_html=True,
        )
        a, b = st.columns(2)
        with a:
            with st.popover("👁 Vista previa", use_container_width=True):
                st.markdown(f"**{doc['nombre']}**")
                st.caption("Texto extraído; vista previa de los primeros 10 000 caracteres.")
                st.text_area("Contenido", value=doc["texto"][:10000], height=285, disabled=True, key=f"preview_{digest}")
        with b:
            if st.button("🗑 Eliminar", key=f"delete_{digest}", use_container_width=True):
                try:
                    indice = obtener_indice(pc)
                    eliminar_ids(indice, doc["ids"], st.session_state.namespace)
                    del st.session_state.documentos[digest]
                    st.session_state.ultima_fuente = []
                    # Quitar fuentes antiguas de la interfaz; no altera el contenido pasado del chat.
                    st.toast(f"{doc['nombre']} eliminado de Pinecone", icon="✅")
                    st.rerun()
                except Exception as error:
                    st.error(f"No se pudo eliminar {doc['nombre']}: {error}")

    if st.session_state.errores_archivos:
        st.markdown('**Archivos con incidencias**')
        for nombre, error in list(st.session_state.errores_archivos.items()):
            with st.expander(f"⚠ {nombre}"):
                st.error(error)
                if st.button("Quitar aviso", key=f"dismiss_{nombre}"):
                    del st.session_state.errores_archivos[nombre]
                    st.rerun()

    st.write("")
    st.markdown('<div class="aura-section">Fuentes de la última respuesta</div>', unsafe_allow_html=True)
    if st.session_state.ultima_fuente:
        for i, fuente in enumerate(st.session_state.ultima_fuente, 1):
            with st.expander(f"{i}. {fuente['documento']}"):
                if fuente["similitud"] is not None:
                    st.caption(f"Similitud vectorial: {fuente['similitud']:.3f}")
                st.write(fuente["fragmento"])
    else:
        st.caption("Los fragmentos recuperados aparecerán aquí después de tu primera pregunta.")

with principal:
    if not st.session_state.historial:
        st.markdown('''<div class="aura-hero"><div class="aura-kicker">✦ Asistente inteligente · RAG</div>
        <h1>Pregúntale a tus documentos.<br/>Explora nuevas respuestas.</h1>
        <p>Convierte archivos en conocimiento consultable. Gemini responde con fragmentos recuperados de tu biblioteca en Pinecone y puedes verificar sus fuentes.</p></div>''', unsafe_allow_html=True)
        st.markdown('<div class="aura-section">Ideas para comenzar</div>', unsafe_allow_html=True)
        st.markdown('''<div class="aura-card">✧ ¿Cuál es el tema principal de los documentos?<br/><span class="aura-muted">✧ Resume los puntos más importantes<br/>✧ ¿Qué diferencias existen entre los conceptos del texto?</span></div>''', unsafe_allow_html=True)
    else:
        st.markdown('<div class="aura-section">Conversación con AURA</div>', unsafe_allow_html=True)

    for i, mensaje in enumerate(st.session_state.historial):
        with st.chat_message(mensaje["rol"], avatar="🤖" if mensaje["rol"] == "assistant" else "👤"):
            st.markdown(mensaje["texto"])
            if mensaje.get("fuentes"):
                presentar_fuentes(mensaje["fuentes"], f"hist_{i}")

# chat_input en el cuerpo PRINCIPAL: Streamlit lo fija automáticamente al pie de página.
pregunta = st.chat_input(
    "Pregunta lo que quieras sobre tus documentos…",
    disabled=n_docs == 0,
    max_chars=4000,
)
if pregunta:
    st.session_state.historial.append({"rol": "user", "texto": pregunta})
    with st.spinner("AURA está consultando tus documentos..."):
        try:
            indice = obtener_indice(pc)
            fuentes = recuperar(indice, gemini, pregunta, st.session_state.namespace, top_k)
            respuesta = generar_respuesta(gemini, pregunta, fuentes, temperatura)
            st.session_state.historial.append({"rol": "assistant", "texto": respuesta, "fuentes": fuentes})
            st.session_state.ultima_fuente = fuentes
            st.session_state.consultas += 1
        except Exception as error:
            st.session_state.historial.append({"rol": "assistant", "texto": f"⚠️ No se pudo completar la consulta: {error}", "fuentes": []})
    st.rerun()

st.markdown('<div class="aura-footer">AURA · Laboratorio RAG educativo · Gemini + Pinecone · No subas información sensible · Los datos de Pinecone persisten hasta su eliminación</div>', unsafe_allow_html=True)
