#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convierte una o varias liquidaciones Getnet (PDF) al Excel de importación
"GenImpExp_PagosEImputaciones". Si pasás varios PDFs, se combinan en un
único Excel (cada documento mantiene su propio Nº Liquidación / Establecimiento,
no se mezclan entre sí).

Uso:
    python pdf_a_excel_getnet.py liquidacion1.pdf [liquidacion2.pdf ...] [-o salida.xlsx] [-c establecimientos.csv]

Requiere:
    pip install pdfplumber openpyxl
"""

import argparse
import sys
from pathlib import Path

from getnet_converter import load_establecimientos, process_batch, write_excel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", help="Uno o varios PDF de liquidación Getnet")
    parser.add_argument("-o", "--output", default=None,
                         help="Ruta del Excel de salida (default: nombre del primer PDF, "
                              "o 'liquidaciones_combinadas.xlsx' si son varios)")
    parser.add_argument("-c", "--config", default=None,
                         help="CSV con Cliente/CUENTAIMP/CCCI por Establecimiento "
                              "(default: establecimientos.csv junto al script)")
    args = parser.parse_args()

    pdf_paths = [Path(p) for p in args.pdfs]
    for p in pdf_paths:
        if not p.exists():
            sys.exit(f"No existe el archivo: {p}")

    if args.output:
        out_path = Path(args.output)
    elif len(pdf_paths) == 1:
        out_path = pdf_paths[0].with_suffix(".xlsx")
    else:
        out_path = Path("liquidaciones_combinadas.xlsx")

    cfg_path = Path(args.config) if args.config else Path(__file__).parent / "establecimientos.csv"
    if not cfg_path.exists():
        sys.exit(f"No se encontró la tabla de configuración: {cfg_path}")

    cfg = load_establecimientos(cfg_path)
    rows, warnings, resumen = process_batch(pdf_paths, cfg, names=[p.name for p in pdf_paths])

    if not rows:
        sys.exit("No se generó ninguna fila. Revisá los avisos:\n" + "\n".join(warnings))

    write_excel(rows, out_path)

    for r in resumen:
        print(f"{r['archivo']}: Liquidación Nº {r['nro_liquidacion']} "
              f"(Establecimiento {r['establecimiento']}) -> {r['filas']} filas")
    print(f"\nTotal: {len(rows)} filas -> {out_path}")
    for w in warnings:
        print(f"ADVERTENCIA: {w}")


if __name__ == "__main__":
    main()
