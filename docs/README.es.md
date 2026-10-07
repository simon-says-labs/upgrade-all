<p align="center"><img src="social-preview.png" width="100%" alt="Upgrade All. Simon says: upgrade all!"></p>

# Upgrade All

<p align="center"><b><a href="../README.md#deutsch">🇩🇪 Deutsch</a> · <a href="../README.md#english">🇬🇧 English</a> · <a href="README.fr.md">🇫🇷 Français</a> · <a href="README.it.md">🇮🇹 Italiano</a> · 🇪🇸 Español</b></p>

> **Simon says: upgrade all!** Mantiene tu Mac al día con [topgrade](https://github.com/topgrade-rs/topgrade), sin
> supervisión, cada pocos días, soluciona por sí mismo los tropiezos habituales y te cuenta en un informe claro lo
> que ha pasado. Nació de la búsqueda de un equivalente de `winget upgrade --all` para el Mac.

<p align="center"><img src="report-light.png" width="760" alt="Informe de una ejecución: tu Mac está al día, los errores se corrigieron automáticamente. npm falló al principio y funcionó en el reintento; topgrade se actualizó primero y se reinició un servicio de Homebrew."></p>

## Por qué mantenerlo todo actualizado, sobre todo para la IA y el vibe coding

Cuando programas con un asistente de IA, el asistente trabaja con las herramientas de **tu** equipo: git, Node,
Python, uv, GitHub CLI, compiladores, servidores MCP, la herramienta de línea de comandos del propio asistente y su
extensión del editor. No puede ver que una de ellas está desactualizada. Lee documentación y ejemplos escritos para
las versiones actuales, usa opciones que tu versión antigua no conoce y te hace perder tiempo persiguiendo errores
que una sola actualización habría eliminado. Las propias herramientas de IA son las que más rápido cambian: nuevos
modelos, nuevos comandos y correcciones llegan como actualizaciones.

Las actualizaciones también traen las correcciones de seguridad para todo lo que un agente de programación ejecuta
en tu nombre.

Cuánto supone eso en la práctica, medido en el Mac del que procede este proyecto: entre el 17 de julio y el 6 de
octubre de 2026, 24 ejecuciones actualizaron **356 paquetes de Homebrew** (fórmulas y apps), además de npm, pipx,
extensiones de VS Code, contenedores y modelos de IA. Nadie mantiene ese ritmo a mano.

## De dónde viene

En Windows, `winget upgrade --all` actualiza todas las aplicaciones instaladas de una vez. Buscaba lo mismo para el
Mac y encontré [topgrade](https://github.com/topgrade-rs/topgrade), una herramienta excelente que actualiza
Homebrew, apps, gestores de paquetes de lenguajes, extensiones del editor y mucho más con un solo comando. Lo que
faltaba era ejecutarla de forma fiable sin mí: según un calendario, sin preguntas, solucionando por sí misma los
tropiezos habituales y contándome después lo que había pasado. Eso es Upgrade All. Desde que se ejecuta en segundo
plano cada pocos días, ya no tengo que pensar en las actualizaciones.

## Qué hace una ejecución

1. **Actualiza primero topgrade.** De lo contrario, el paso de Homebrew de la ejecución actualiza el propio topgrade
   y `--cleanup` elimina la carpeta de la versión que todavía se está ejecutando. Los pasos posteriores que tocan
   ubicaciones protegidas (por ejemplo, un disco externo) son entonces denegados por macOS, con mensajes engañosos.
2. **Ejecuta topgrade sin preguntas** (`--yes --no-ask-retry --no-self-update --cleanup`; las actualizaciones del
   sistema de macOS quedan fuera porque piden una contraseña).
3. **Reinicia los servicios de Homebrew** que todavía ejecutan una versión cuya carpeta acaba de eliminarse.
4. **Reintenta una vez cada paso fallido**, tras una breve pausa, exactamente ese paso (`topgrade --only <step>`).
   Los nombres de los pasos proceden del propio código fuente de topgrade, por lo que el resumen se entiende en
   todos los idiomas que habla topgrade.
5. **Ejecuta tus pasos adicionales** desde la carpeta de hooks.
6. **Escribe un informe** y lo abre en tu navegador (siempre, solo si hay problemas o nunca). Las ejecuciones
   antiguas van a la Papelera al cabo de un tiempo; no se borra nada.

## Instalación

Necesita macOS, [Homebrew](https://brew.sh) y topgrade (`brew install topgrade`). Upgrade All en sí no tiene
dependencias: funciona con `/usr/bin/python3`, que viene con las Command Line Tools de Apple. El instalador de
Homebrew las configura; si no, `xcode-select --install`.

```bash
git clone https://github.com/simon-says-labs/upgrade-all
cd upgrade-all
/usr/bin/python3 -m upgrade_all install
```

Esto copia el programa en `~/Library/Application Support/upgrade-all/` y configura la tarea en segundo plano
`labs.simon-says.upgrade-all` (cada 3 días). Pruébalo enseguida:

```bash
~/Library/Application\ Support/upgrade-all/upgrade-all run
```

## Comandos

| Comando | Qué hace |
|---|---|
| `upgrade-all run` | Actualizar ahora (es lo que ejecuta la tarea en segundo plano). |
| `upgrade-all status` | Tarea en segundo plano, última ejecución, próxima ejecución, último informe. |
| `upgrade-all grant-access [step]` | Hace que macOS vuelva a pedir acceso para el topgrade actual (ver abajo). |
| `upgrade-all install` | Instalar o actualizar; conserva tus ajustes. `--no-agent` omite la tarea en segundo plano. |
| `upgrade-all uninstall` | Desactiva la tarea en segundo plano y mueve el programa a la Papelera. `--logs` también mueve los registros. |

## Ajustes

`~/Library/Application Support/upgrade-all/config.json`:

| Ajuste | Predeterminado | Significado |
|---|---|---|
| `interval_days` | `3` | Días entre dos ejecuciones. Después de cambiarlo, vuelve a ejecutar `install`. |
| `language` | `auto` | Idioma del informe: `auto` (idioma de macOS), `en`, `de`, `fr`, `it`, `es`. |
| `disable_steps` | `["system"]` | Pasos de topgrade que se omiten, p. ej. `["system", "uv"]`. |
| `cleanup` | `true` | Eliminar las versiones antiguas tras actualizar (`--cleanup`). |
| `pre_upgrade_topgrade` | `true` | Actualizar topgrade con Homebrew antes de la ejecución. |
| `restart_outdated_services` | `true` | Reiniciar los servicios de Homebrew que todavía ejecutan una versión eliminada. |
| `retry_failed` | `true` | Reintentar una vez los pasos fallidos. |
| `retry_delay_seconds` | `30` | Pausa antes del reintento. |
| `timeout_minutes` | `180` | Detener topgrade si tarda más. |
| `open_report` | `always` | `always` (siempre), `problems` (solo si hay problemas) o `never` (nunca). |
| `keep_runs` | `60` | Ejecuciones que se conservan; los registros e informes más antiguos van a la Papelera. |
| `access_probe_step` | `skills` | Paso que usa `grant-access` cuando la última ejecución no indicó ninguno. |
| `extra_topgrade_args` | `[]` | Más argumentos para topgrade, p. ej. `["--disable", "containers"]`. |

## Pasos adicionales (hooks)

Coloca archivos ejecutables en `~/Library/Application Support/upgrade-all/hooks/`. Se ejecutan después de topgrade,
por orden de nombre. El código de salida `0` significa OK, `3` omitido y cualquier otro, fallido. Una línea que
empiece por `Summary:` aparece en el informe. Se definen `UPGRADE_ALL_LANGUAGE` y `UPGRADE_ALL_LOGS`. Un paso
adicional nunca cambia el resultado de topgrade. En [examples/hooks](../examples/hooks) hay uno que mantiene un
Brewfile de todo lo instalado.

Un hook ubicado en un disco externo puede fallar en segundo plano con `Operation not permitted` (salida 126): macOS
comprueba el acceso por programa, y `/bin/sh` normalmente no tiene permiso allí. Guarda esos hooks en el disco
interno o haz que los ejecute un intérprete que ya tenga acceso (por ejemplo `#!/opt/homebrew/bin/python3`).

## Cuando macOS deniega el acceso

macOS recuerda algunos permisos, como el acceso a archivos de un disco externo, **por archivo de programa**. La ruta
del archivo de topgrade contiene su versión, así que cada actualización de topgrade empieza sin ese permiso, y desde
un terminal macOS nunca lo pide: ahí el responsable es la app de terminal, no topgrade. Si un paso sigue denegado
tras el reintento, el informe lo indica y da el comando:

```bash
upgrade-all grant-access skills
```

Ejecuta ese único paso como tarea en segundo plano, igual que la ejecución programada, para que macOS pregunte;
después haz clic en **Permitir**.

## Desarrollo

```bash
/usr/bin/python3 -m unittest discover -s tests       # sustitutos de topgrade y brew, no se actualiza nada
/usr/bin/python3 -m upgrade_all sample-report /tmp/report.html --language de
/usr/bin/python3 tools/update_steps.py v17.12.3       # actualiza la tabla de pasos a partir del código fuente de topgrade
```

Consulta [CONTRIBUTING.md](../CONTRIBUTING.md). Cambios: [CHANGELOG.md](../CHANGELOG.md).

## Licencia

[MIT](../LICENSE) © 2026 Simon Eckmiller · publicado por [Simon Says](https://github.com/simon-says-labs).
Componentes de terceros: [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Upgrade All es un proyecto
independiente y no forma parte de topgrade.

<p align="right"><a href="#upgrade-all">↑</a></p>
