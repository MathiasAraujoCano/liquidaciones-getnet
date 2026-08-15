# Publicar la app web gratis (Streamlit Community Cloud)

No puedo crear el repositorio ni la cuenta por vos (necesita tu login), pero
son ~15 minutos siguiendo estos pasos. Es gratis y no pide tarjeta.

## 1. Subir estos archivos a GitHub

Necesitás: `app.py`, `getnet_converter.py`, `github_store.py`,
`establecimientos.csv`, `requirements.txt`.

1. Entrá a [github.com](https://github.com) y creá una cuenta si no tenés.
2. Creá un repositorio nuevo (botón "New repository"). Ponele un nombre, ej.
   `liquidaciones-getnet`.
   - **Importante para privacidad**: como el Excel modelo, `establecimientos.csv`
     y el registro de liquidaciones tienen datos de tu cliente (RUT, cuentas),
     marcá el repo como **Private**.
3. Subí los archivos: en la página del repo, "Add file" → "Upload files",
   arrastralos y confirmá ("Commit changes").

## 2. Generar un Token de GitHub (para que la app guarde el registro)

La app necesita permiso para escribir en tu repo el archivo
`registro_liquidaciones.csv` cada vez que se procesa una liquidación.

1. En GitHub: click en tu foto de perfil → **Settings** → (al final del menú
   izquierdo) **Developer settings** → **Personal access tokens** →
   **Tokens (classic)** → **Generate new token (classic)**.
2. Ponele un nombre (ej. "app liquidaciones"), expiración la que prefieras,
   y tildá el permiso **repo** (acceso completo a repos privados).
3. Generá el token y **copialo ya** (no lo vas a poder ver de nuevo).

## 3. Conectar con Streamlit Community Cloud

1. Entrá a [share.streamlit.io](https://share.streamlit.io) y entrá con tu
   cuenta de GitHub (botón "Sign in with GitHub").
2. Autorizá a Streamlit a acceder a tus repos (podés limitarlo solo al repo
   que creaste).
3. "New app" → elegí tu repositorio → branch `main` → archivo principal
   `app.py` → antes de darle a "Deploy", abrí **"Advanced settings"**.
4. En **Secrets**, pegá esto (reemplazando con tus datos):

   ```
   github_token = "el_token_que_copiaste"
   github_owner = "tu_usuario_de_github"
   github_repo = "liquidaciones-getnet"
   github_branch = "main"
   ```

5. Dale a "Deploy". Esperá 1-2 minutos. Te da una URL pública para
   compartirle a tu clienta (ej. `https://tu-app.streamlit.app`).

Si en algún momento necesitás cambiar el token o el repo, lo hacés en
"Settings" → "Secrets" de la app, sin tocar el código.

## 4. Restringir quién puede verla (recomendado, datos financieros)

Community Cloud permite **1 app privada gratis** con lista de emails
autorizados:

1. En el dashboard de tu app (share.streamlit.io) → "Settings" → "Sharing".
2. Elegí "Only specific people can view this app" y agregá el email de tu
   clienta (y el tuyo).
3. Ella va a tener que iniciar sesión con ese email (Google o GitHub) para
   entrar.

Si no restringís esto, cualquiera con el link puede abrir la app y subir/ver
resultados — no lo compartas públicamente.

## 5. Actualizaciones

Cualquier cambio que subas a GitHub (por ejemplo agregar un establecimiento
nuevo a `establecimientos.csv`) redeploya la app sola en unos segundos. El
registro de liquidaciones (`registro_liquidaciones.csv`) también se va a ir
actualizando solo en el repo cada vez que alguien procese una liquidación —
lo podés ver directo en GitHub, o desde el desplegable "Historial de
liquidaciones ya cargadas" dentro de la propia app.

## Nota sobre "se duerme"

Si nadie la usa por 12 horas, la app se pausa. La primera vez que alguien
entra después de eso tarda ~30 segundos en despertar — es normal. El
registro no se pierde porque vive en GitHub, no en el servidor de la app.
