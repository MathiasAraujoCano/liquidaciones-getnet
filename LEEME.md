# Liquidaciones Getnet → Excel

Convierte liquidaciones Getnet (PDF) al Excel de importación
`GenImpExp_PagosEImputaciones`. Hay dos formas de usarlo: línea de comandos
(CLI) o app web (para tu clienta). Ambas comparten la misma lógica en
`getnet_converter.py`, así que se comportan igual.

## Archivos

- `getnet_converter.py` — toda la lógica (parseo del PDF, mapeo a filas, escritura del Excel). No se ejecuta solo.
- `github_store.py` — lee/escribe el registro de liquidaciones cargadas como un CSV versionado en GitHub.
- `pdf_a_excel_getnet.py` — CLI. Acepta uno o varios PDFs.
- `app.py` — app web (Streamlit) para subir PDFs desde el navegador.
- `establecimientos.csv` — tabla con Cliente/CUENTAIMP/CCCI fijos por establecimiento.
- `requirements.txt` — dependencias (para instalar local o para el deploy).
- `DEPLOY.md` — pasos para publicar la app web gratis, incluido el token de GitHub para el registro.

## Uso por línea de comandos

```
pip install -r requirements.txt
python pdf_a_excel_getnet.py liquidacion.pdf
```

Con varios PDFs, se combinan en un solo Excel (cada documento mantiene su
propio Nº Liquidación/Establecimiento, no se mezclan entre sí):

```
python pdf_a_excel_getnet.py liquidacion1.pdf liquidacion2.pdf liquidacion3.pdf -o combinado.xlsx
```

(El CLI no guarda el registro en GitHub, eso solo lo hace la app web.)

## Uso como app web (local, para probar)

```
pip install -r requirements.txt
streamlit run app.py
```

Se abre en el navegador. Sin los secrets de GitHub configurados, el registro
de liquidaciones cargadas se guarda en un archivo local (`registro_liquidaciones.csv`)
solo para pruebas — perfecto para correrlo en tu PC. Para que tu clienta la
use desde cualquier PC y el registro sea permanente, ver `DEPLOY.md`.

## Tabla `establecimientos.csv`

Cliente, CUENTAIMP y CCCI no están en el PDF: son fijos por establecimiento.
Agregá una fila por cada establecimiento Getnet que uses:

```
Establecimiento,Cliente,CUENTAIMP,CCCI
112038,1304,1130022,00000130
```

Si subís un PDF de un establecimiento que no está en esta tabla, la app web
te deja completarlo en pantalla para esa sesión (pero no queda guardado
permanentemente — para eso hay que agregarlo al CSV en GitHub).

## Registro de liquidaciones cargadas ("memoria")

Cada vez que se procesa un lote en la app web, se agrega una fila a
`registro_liquidaciones.csv` con Nº Liquidación, Establecimiento, Fecha de
Presentación, fecha en que se cargó, archivo y cantidad de filas generadas.

- Con los secrets de GitHub configurados (ver `DEPLOY.md`), ese CSV se
  commitea al repo automáticamente: persiste siempre, aunque la app se
  reinicie o duerma, y tu clienta lo puede ver directo en GitHub.
- Dentro de la misma app hay un desplegable **"Historial de liquidaciones
  ya cargadas"** con una tabla — no hace falta entrar a GitHub para
  revisarlo.
- Si subís una liquidación cuyo Nº ya estaba en el registro (de una carga
  anterior), la app **avisa pero igual la genera** — no bloquea, por si
  necesitás reprocesarla a propósito.

## Lógica de mapeo (por liquidación → filas del Excel)

- **PLAN 12**: suma de los ítems "Retención" de la sección Ajustes del PDF.
- **PLAN 13**: suma de los ítems "Dev. IVA" de Ajustes.
- **PLAN 14**: columna I.V.A de la fila Total de "Información de totales".
- **PLAN 15**: Servicio Financiero + Otros Servicios (misma fila Total).
- **PLAN 44**: una fila por cada línea de "Detalle de Transferencia" (VtoPago=Vencimiento, Importe=Importe, NumPago=Referencia, NameOnDoc=SANTANDER).
- En todas las filas: FECHA=Fecha Presentación, NRODOC=Nº Liquidación, Cliente/CUENTAIMP/CCCI según el establecimiento.

Si el PDF trae un tipo de ajuste que no es "Retención" ni "Dev. IVA", se
avisa en vez de adivinar y no se incluye en el Excel.

## Múltiples PDFs sin pisarse

Cada PDF se parsea y arma de forma completamente independiente (su propio
Nº Liquidación, Establecimiento, Cliente, etc.) y recién al final se
concatenan todas las filas en un solo archivo.

## Supuestos que no me confirmaste — revisalos

1. **NumPago en PLAN 44**: usé el número de Referencia de "Detalle de Transferencia".
2. **VtoPago y NameOnDoc en PLAN 12/13/14/15**: usé Fecha Presentación como VtoPago y dejé NameOnDoc vacío.

Si tu sistema espera otra cosa ahí, decime y ajusto.
