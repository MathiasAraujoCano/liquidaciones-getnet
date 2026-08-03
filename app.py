# -*- coding: utf-8 -*-
"""App web (Streamlit) para convertir liquidaciones Getnet (PDF) al Excel
"GenImpExp_PagosEImputaciones". Corre con:  streamlit run app.py
"""

from datetime import datetime
from io import BytesIO
from pathlib import Path

import streamlit as st

from getnet_converter import (
    ConversionError,
    build_rows,
    load_establecimientos,
    parse_pdf,
    write_excel,
)
from github_store import FIELDNAMES, fetch_registro, save_registro

CONFIG_PATH = Path(__file__).parent / "establecimientos.csv"
LOCAL_REGISTRO_PATH = Path(__file__).parent / "registro_liquidaciones.csv"


def _get_secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


GITHUB_TOKEN = _get_secret("github_token")
GITHUB_OWNER = _get_secret("github_owner")
GITHUB_REPO = _get_secret("github_repo")
GITHUB_BRANCH = _get_secret("github_branch", "main")
GITHUB_REGISTRO_PATH = "registro_liquidaciones.csv"

MODO_GITHUB = bool(GITHUB_TOKEN and GITHUB_OWNER and GITHUB_REPO)


def cargar_registro():
    """Devuelve (rows, sha_o_None). sha solo aplica en modo GitHub."""
    if MODO_GITHUB:
        try:
            return fetch_registro(GITHUB_OWNER, GITHUB_REPO, GITHUB_REGISTRO_PATH,
                                   GITHUB_TOKEN, GITHUB_BRANCH)
        except Exception as e:
            st.error(f"No se pudo leer el registro desde GitHub: {e}")
            return [], None
    if LOCAL_REGISTRO_PATH.exists():
        import csv
        with open(LOCAL_REGISTRO_PATH, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f)), None
    return [], None


def guardar_registro(rows, sha):
    if MODO_GITHUB:
        return save_registro(GITHUB_OWNER, GITHUB_REPO, GITHUB_REGISTRO_PATH,
                              GITHUB_TOKEN, rows, sha, GITHUB_BRANCH)
    import csv
    with open(LOCAL_REGISTRO_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return None


st.set_page_config(page_title="Liquidaciones Getnet → Excel", page_icon="📄")
st.title("Liquidaciones Getnet → Excel")
st.write(
    "Subí uno o varios PDF de liquidación Getnet. Cada documento se procesa "
    "por separado (no se mezclan datos entre liquidaciones) y se combinan "
    "todos en un único Excel para descargar."
)

if not MODO_GITHUB:
    st.info(
        "El registro de liquidaciones cargadas se está guardando solo en "
        "este servidor (no en GitHub) - configurá los secrets `github_token`, "
        "`github_owner` y `github_repo` para que sea permanente. Ver DEPLOY.md."
    )

if "uploader_version" not in st.session_state:
    st.session_state.uploader_version = 0
if "resultado" not in st.session_state:
    st.session_state.resultado = None

registro_rows, registro_sha = cargar_registro()
nrodocs_previos = {r["NRODOC"]: r for r in registro_rows}

with st.expander(f"Historial de liquidaciones ya cargadas ({len(registro_rows)})"):
    if registro_rows:
        st.dataframe(sorted(registro_rows, key=lambda r: r["FechaCarga"], reverse=True),
                     use_container_width=True)
    else:
        st.caption("Todavía no se cargó ninguna liquidación.")

cfg = load_establecimientos(CONFIG_PATH) if CONFIG_PATH.exists() else {}

archivos = st.file_uploader(
    "PDFs de liquidación", type=["pdf"], accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_version}",
)

if archivos:
    # 1) Parsear y armar las filas es puro (no escribe nada): se puede hacer
    #    apenas se sube el archivo, sin esperar ningún click, y avisar de
    #    entrada si hay duplicados contra el registro.
    parsed = []
    parse_errores = []
    for archivo in archivos:
        try:
            data = parse_pdf(archivo)
            parsed.append((archivo.name, data))
        except ConversionError as e:
            parse_errores.append(f"{archivo.name}: {e}")

    for e in parse_errores:
        st.error(e)

    faltantes = sorted({d["establecimiento"] for _, d in parsed
                         if d["establecimiento"] not in cfg})
    fijos_sesion = {}
    if faltantes:
        st.warning(
            "Estos establecimientos no están en establecimientos.csv. "
            "Completá Cliente / CUENTAIMP / CCCI para esta sesión (para que "
            "quede guardado siempre, agregalos también al archivo en GitHub):"
        )
        for est in faltantes:
            st.markdown(f"**Establecimiento {est}**")
            c1, c2, c3 = st.columns(3)
            cliente = c1.text_input(f"Cliente ({est})", key=f"cliente_{est}")
            cuentaimp = c2.text_input(f"CUENTAIMP ({est})", key=f"cuentaimp_{est}")
            ccci = c3.text_input(f"CCCI ({est})", key=f"ccci_{est}")
            if cliente and cuentaimp and ccci:
                fijos_sesion[est] = {
                    "Cliente": cliente, "CUENTAIMP": cuentaimp, "CCCI": ccci,
                }

    cfg_completo = {**cfg, **fijos_sesion}
    listos = bool(parsed) and all(d["establecimiento"] in cfg_completo for _, d in parsed)

    if parsed and not listos:
        st.info("Completá los datos de establecimiento de arriba para generar el Excel.")

    if listos:
        # 2) Se arman las filas y se avisan los duplicados ya (sin efectos
        #    secundarios todavía) para que se vea apenas se sube el archivo.
        all_rows = []
        warnings = []
        resumen = []
        vistos = {}
        nuevas_entradas_registro = []
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M")

        for nombre, data in parsed:
            fijos = cfg_completo[data["establecimiento"]]
            rows, w = build_rows(data, fijos)
            nrodoc = data["nro_liquidacion"]

            if nrodoc in vistos:
                warnings.append(
                    f"{nombre}: la liquidación Nº {nrodoc} ya fue cargada en este "
                    f"mismo lote desde '{vistos[nrodoc]}'. Se agregó igual."
                )
            elif nrodoc in nrodocs_previos:
                prev = nrodocs_previos[nrodoc]
                warnings.append(
                    f"{nombre}: la liquidación Nº {nrodoc} ya había sido cargada "
                    f"antes ({prev['FechaCarga']}, archivo '{prev['Archivo']}'). "
                    f"Se generó igual, revisá que no sea un duplicado."
                )
            vistos[nrodoc] = nombre

            all_rows.extend(rows)
            warnings.extend(w)
            resumen.append((nombre, nrodoc, data["establecimiento"], len(rows)))
            nuevas_entradas_registro.append({
                "NRODOC": nrodoc,
                "Establecimiento": data["establecimiento"],
                "FechaPresentacion": data["fecha_presentacion"],
                "FechaCarga": ahora,
                "Archivo": nombre,
                "Filas": len(rows),
            })

        st.subheader("Resumen")
        st.table({
            "Archivo": [r[0] for r in resumen],
            "Nº Liquidación": [r[1] for r in resumen],
            "Establecimiento": [r[2] for r in resumen],
            "Filas generadas": [r[3] for r in resumen],
        })
        for w in warnings:
            st.warning(w)

        # 3) Esto sí es un efecto secundario real (Excel + commit al
        #    registro) y tiene que pasar una sola vez por lote. Se dispara
        #    automáticamente (sin botón), y apenas termina vacía el uploader
        #    para que un rerun posterior (ej. al descargar) no lo repita.
        if all_rows:
            buffer = BytesIO()
            write_excel(all_rows, buffer)
            excel_bytes = buffer.getvalue()
            try:
                registro_actualizado = registro_rows + nuevas_entradas_registro
                guardar_registro(registro_actualizado, registro_sha)
                registro_ok = True
            except Exception as e:
                warnings.append(f"No se pudo guardar el registro: {e}")
                registro_ok = False

            st.session_state.resultado = {
                "resumen": resumen,
                "warnings": warnings,
                "excel_bytes": excel_bytes,
                "total_filas": len(all_rows),
                "registro_ok": registro_ok,
            }
            st.session_state.uploader_version += 1
            st.rerun()

resultado = st.session_state.resultado
if resultado and not archivos:
    st.success(f"Listo: {resultado['total_filas']} filas en total.")
    st.download_button(
        "Descargar Excel combinado",
        data=resultado["excel_bytes"],
        file_name="liquidaciones_combinadas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    if resultado["registro_ok"]:
        st.caption("Registro actualizado ✓")

    if st.button("Empezar de nuevo"):
        st.session_state.resultado = None
        st.rerun()
