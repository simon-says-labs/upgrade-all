<p align="center"><img src="logo.png" width="250" alt="Upgrade All logo"></p>

# Upgrade All

<p align="center"><b><a href="../README.md#deutsch">🇩🇪 Deutsch</a> · <a href="../README.md#english">🇬🇧 English</a> · 🇫🇷 Français · <a href="README.it.md">🇮🇹 Italiano</a> · <a href="README.es.md">🇪🇸 Español</a></b></p>

> **Simon says: upgrade all!** Maintient votre Mac à jour avec [topgrade](https://github.com/topgrade-rs/topgrade),
> sans surveillance, tous les quelques jours, corrige lui-même les accrocs habituels et vous indique dans un rapport
> clair ce qui s'est passé. Né de la recherche d'un équivalent de `winget upgrade --all` pour le Mac.

<p align="center"><img src="report-light.png" width="760" alt="Rapport d'une exécution : votre Mac est à jour, des erreurs ont été corrigées automatiquement. npm a d'abord échoué, puis réussi lors de la nouvelle tentative ; topgrade a été mis à jour en premier et un service Homebrew a été redémarré."></p>

## Pourquoi tout maintenir à jour, surtout pour l'IA et le vibe coding

Quand vous programmez avec un assistant IA, celui-ci travaille avec les outils de **votre** machine : git, Node,
Python, uv, GitHub CLI, les compilateurs, les serveurs MCP, l'outil en ligne de commande de l'assistant et son
extension d'éditeur. Il ne peut pas voir que l'un d'eux est obsolète. Il lit de la documentation et des exemples
écrits pour les versions actuelles, utilise des options que votre ancienne version ne connaît pas, et vous fait
perdre du temps à traquer des erreurs qu'une seule mise à jour aurait éliminées. Ce sont les outils d'IA eux-mêmes
qui évoluent le plus vite : nouveaux modèles, nouvelles commandes et corrections arrivent sous forme de mises à jour.

Les mises à jour apportent aussi les correctifs de sécurité pour tout ce qu'un agent de programmation exécute en
votre nom.

Ce que cela représente en pratique, mesuré sur le Mac d'où vient ce projet : entre le 17 juillet et le 6 octobre
2026, 24 exécutions ont mis à jour **356 paquets Homebrew** (formules et apps), plus npm, pipx, des extensions
VS Code, des conteneurs et des modèles d'IA. Personne ne tient ce rythme à la main.

## D'où vient ce projet

Sous Windows, `winget upgrade --all` met à jour toutes les applications installées d'un seul coup. Je cherchais la
même chose pour le Mac et j'ai trouvé [topgrade](https://github.com/topgrade-rs/topgrade), un excellent outil qui
met à jour Homebrew, les apps, les gestionnaires de paquets des langages, les extensions d'éditeur et bien plus
encore en une seule commande. Il manquait seulement de le faire tourner de façon fiable sans moi : selon un
calendrier, sans questions, en corrigeant lui-même les accrocs habituels et en me disant ensuite ce qui s'est passé.
C'est Upgrade All. Depuis qu'il tourne tous les quelques jours en arrière-plan, je n'ai plus du tout à penser aux
mises à jour.

## Ce que fait une exécution

1. **Met d'abord à jour topgrade.** Sinon, l'étape Homebrew de l'exécution met à jour topgrade lui-même et
   `--cleanup` supprime le dossier de la version encore en cours d'exécution. Les étapes suivantes qui touchent des
   emplacements protégés (par exemple un disque externe) sont alors refusées par macOS, avec des messages trompeurs.
2. **Lance topgrade sans questions** (`--yes --no-ask-retry --no-self-update --cleanup`, sans les mises à jour
   système de macOS, car elles demandent un mot de passe).
3. **Redémarre les services Homebrew** qui exécutent encore une version dont le dossier vient d'être supprimé.
4. **Relance une fois chaque étape échouée**, après une courte pause, avec exactement cette étape
   (`topgrade --only <step>`). Les noms d'étapes proviennent du code source de topgrade, si bien que le résumé est
   compris dans toutes les langues que parle topgrade.
5. **Exécute vos étapes supplémentaires** depuis le dossier hooks.
6. **Rédige un rapport** et l'ouvre dans votre navigateur (toujours, seulement en cas de problème, ou jamais). Les
   anciennes exécutions vont à la Corbeille au bout d'un moment ; rien n'est supprimé.

## Installation

Nécessite macOS, [Homebrew](https://brew.sh) et topgrade (`brew install topgrade`). Upgrade All lui-même n'a aucune
dépendance : il fonctionne avec `/usr/bin/python3`, fourni avec les Command Line Tools d'Apple. L'installateur
Homebrew les installe ; sinon `xcode-select --install`.

```bash
git clone https://github.com/simon-says-labs/upgrade-all
cd upgrade-all
/usr/bin/python3 -m upgrade_all install
```

Cela copie le programme dans `~/Library/Application Support/upgrade-all/` et configure la tâche d'arrière-plan
`labs.simon-says.upgrade-all` (tous les 3 jours). Essayez-le tout de suite :

```bash
~/Library/Application\ Support/upgrade-all/upgrade-all run
```

## Commandes

| Commande | Effet |
|---|---|
| `upgrade-all run` | Mettre à jour maintenant (c'est ce qu'exécute la tâche d'arrière-plan). |
| `upgrade-all status` | Tâche d'arrière-plan, dernière exécution, prochaine exécution, dernier rapport. |
| `upgrade-all grant-access [step]` | Permet à macOS de redemander l'accès pour le topgrade actuel (voir plus bas). |
| `upgrade-all install` | Installer ou mettre à jour ; vos réglages sont conservés. `--no-agent` omet la tâche d'arrière-plan. |
| `upgrade-all uninstall` | Désactive la tâche d'arrière-plan et déplace le programme dans la Corbeille. `--logs` déplace aussi les journaux. |

## Réglages

`~/Library/Application Support/upgrade-all/config.json` :

| Réglage | Par défaut | Signification |
|---|---|---|
| `interval_days` | `3` | Jours entre deux exécutions. Relancez `install` après l'avoir modifié. |
| `language` | `auto` | Langue du rapport : `auto` (langue de macOS), `en`, `de`, `fr`, `it`, `es`. |
| `disable_steps` | `["system"]` | Étapes de topgrade à omettre, p. ex. `["system", "uv"]`. |
| `cleanup` | `true` | Supprimer les anciennes versions après la mise à jour (`--cleanup`). |
| `pre_upgrade_topgrade` | `true` | Mettre à jour topgrade avec Homebrew avant l'exécution. |
| `restart_outdated_services` | `true` | Redémarrer les services Homebrew qui exécutent encore une version supprimée. |
| `retry_failed` | `true` | Relancer une fois les étapes échouées. |
| `retry_delay_seconds` | `30` | Pause avant la nouvelle tentative. |
| `timeout_minutes` | `180` | Arrêter topgrade s'il dure plus longtemps. |
| `open_report` | `always` | `always` (toujours), `problems` (seulement en cas de problème) ou `never` (jamais). |
| `keep_runs` | `60` | Exécutions conservées ; les journaux et rapports plus anciens vont à la Corbeille. |
| `access_probe_step` | `skills` | Étape utilisée par `grant-access` si la dernière exécution n'en a nommé aucune. |
| `extra_topgrade_args` | `[]` | Arguments supplémentaires pour topgrade, p. ex. `["--disable", "containers"]`. |

## Étapes supplémentaires (hooks)

Placez des fichiers exécutables dans `~/Library/Application Support/upgrade-all/hooks/`. Ils s'exécutent après
topgrade, dans l'ordre de leurs noms. Le code de sortie `0` signifie OK, `3` ignoré, tout autre code échec. Une
ligne commençant par `Summary:` apparaît dans le rapport. `UPGRADE_ALL_LANGUAGE` et `UPGRADE_ALL_LOGS` sont
définies. Une étape supplémentaire ne modifie jamais le résultat de topgrade. Voir
[examples/hooks](../examples/hooks) pour un exemple qui tient à jour un Brewfile de tout ce qui est installé.

Un hook situé sur un disque externe peut échouer en arrière-plan avec `Operation not permitted` (code de sortie
126) : macOS vérifie l'accès programme par programme, et `/bin/sh` n'y a généralement pas l'autorisation. Placez ces
hooks sur le disque interne, ou faites-les lancer par un interpréteur qui a déjà l'accès (par exemple
`#!/opt/homebrew/bin/python3`).

## Quand macOS refuse l'accès

macOS mémorise certaines autorisations, comme l'accès aux fichiers d'un disque externe, **par fichier de
programme**. Le chemin du fichier de topgrade contient sa version : chaque mise à jour de topgrade repart donc sans
cette autorisation, et depuis un terminal, macOS ne la demande jamais, car c'est alors l'app de terminal qui est
responsable, pas topgrade. Si une étape est toujours refusée après la nouvelle tentative, le rapport l'indique et
donne la commande :

```bash
upgrade-all grant-access skills
```

Elle exécute cette seule étape comme tâche d'arrière-plan, comme le fait l'exécution planifiée, afin que macOS pose
la question ; cliquez alors sur **Autoriser**.

## Développement

```bash
/usr/bin/python3 -m unittest discover -s tests       # substituts pour topgrade et brew, rien n'est mis à jour
/usr/bin/python3 -m upgrade_all sample-report /tmp/report.html --language de
/usr/bin/python3 tools/update_steps.py v17.12.3       # actualise la table des étapes depuis le code source de topgrade
```

Voir [CONTRIBUTING.md](../CONTRIBUTING.md). Modifications : [CHANGELOG.md](../CHANGELOG.md).

## Licence

[MIT](../LICENSE) © 2026 Simon Eckmiller · publié par [Simon Says](https://github.com/simon-says-labs).
Composants tiers : [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Upgrade All est un projet indépendant et ne
fait pas partie de topgrade.

<p align="right"><a href="#upgrade-all">↑</a></p>
