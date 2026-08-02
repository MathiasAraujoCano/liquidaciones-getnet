# -*- coding: utf-8 -*-
"""Registro de liquidaciones cargadas, guardado como CSV versionado en un
repositorio de GitHub (usando la API de contenidos). Así el historial
persiste aunque la app de Streamlit se reinicie o se redeploye, y tu
clienta lo puede revisar directo en GitHub si quiere.
"""

import base64
import csv
import io

import requests

API_ROOT = "https://api.github.com"
FIELDNAMES = ["NRODOC", "Establecimiento", "FechaPresentacion", "FechaCarga", "Archivo", "Filas"]


def _headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def _url(owner, repo, path):
    return f"{API_ROOT}/repos/{owner}/{repo}/contents/{path}"


def fetch_registro(owner, repo, path, token, branch="main"):
    """Devuelve (rows, sha). rows=[] y sha=None si el archivo todavía no existe."""
    resp = requests.get(
        _url(owner, repo, path), headers=_headers(token),
        params={"ref": branch}, timeout=15,
    )
    if resp.status_code == 404:
        return [], None
    resp.raise_for_status()
    payload = resp.json()
    content = base64.b64decode(payload["content"]).decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(content)))
    return rows, payload["sha"]


def save_registro(owner, repo, path, token, rows, sha, branch="main",
                   message="Actualiza registro de liquidaciones"):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
    content_b64 = base64.b64encode(buf.getvalue().encode("utf-8")).decode("utf-8")

    body = {"message": message, "content": content_b64, "branch": branch}
    if sha:
        body["sha"] = sha

    resp = requests.put(_url(owner, repo, path), headers=_headers(token), json=body, timeout=15)
    resp.raise_for_status()
    return resp.json()["content"]["sha"]
