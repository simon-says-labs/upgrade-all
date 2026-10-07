<p align="center"><img src="social-preview.png" width="100%" alt="Upgrade All. Simon says: upgrade all!"></p>

# Upgrade All

<p align="center"><b><a href="../README.md#deutsch">🇩🇪 Deutsch</a> · <a href="../README.md#english">🇬🇧 English</a> · <a href="README.fr.md">🇫🇷 Français</a> · 🇮🇹 Italiano · <a href="README.es.md">🇪🇸 Español</a></b></p>

> **Simon says: upgrade all!** Mantiene aggiornato il tuo Mac con [topgrade](https://github.com/topgrade-rs/topgrade),
> in automatico, ogni pochi giorni, risolve da solo gli intoppi tipici e ti spiega in un rapporto chiaro cosa è
> successo. Nato dalla ricerca di un equivalente di `winget upgrade --all` per il Mac.

<p align="center"><img src="report-light.png" width="760" alt="Rapporto di un'esecuzione: il tuo Mac è aggiornato, gli errori sono stati corretti automaticamente. npm all'inizio non è riuscito e ha funzionato al secondo tentativo; topgrade è stato aggiornato per primo e un servizio Homebrew è stato riavviato."></p>

## Perché tenere tutto aggiornato, soprattutto per l'IA e il vibe coding

Quando programmi con un assistente IA, l'assistente lavora con gli strumenti del **tuo** computer: git, Node,
Python, uv, GitHub CLI, i compilatori, i server MCP, lo strumento da riga di comando dell'assistente e la sua
estensione per l'editor. Non può vedere che uno di questi è obsoleto. Legge documentazione ed esempi scritti per le
versioni attuali, usa opzioni che la tua vecchia versione non conosce e ti fa perdere tempo a inseguire errori che
un solo aggiornamento avrebbe eliminato. Gli strumenti di IA stessi sono quelli che cambiano più in fretta: nuovi
modelli, nuovi comandi e correzioni arrivano come aggiornamenti.

Gli aggiornamenti portano anche le correzioni di sicurezza per tutto ciò che un agente di programmazione esegue per
conto tuo.

Quanto vale tutto questo nella pratica, misurato sul Mac da cui nasce questo progetto: tra il 17 luglio e il
6 ottobre 2026, 24 esecuzioni hanno aggiornato **356 pacchetti Homebrew** (formule e app), più npm, pipx, estensioni
di VS Code, container e modelli di IA. Nessuno riesce a stare al passo a mano.

## Da dove nasce

Su Windows, `winget upgrade --all` aggiorna tutte le applicazioni installate in un colpo solo. Cercavo la stessa
cosa per il Mac e ho trovato [topgrade](https://github.com/topgrade-rs/topgrade), uno strumento eccellente che
aggiorna Homebrew, le app, i gestori di pacchetti dei linguaggi, le estensioni dell'editor e molto altro con un solo
comando. Mancava solo un modo per farlo girare in modo affidabile senza di me: a intervalli programmati, senza
domande, risolvendo da solo gli intoppi tipici e dicendomi poi cosa è successo. Questo è Upgrade All. Da quando gira
in background ogni pochi giorni, non devo più pensare agli aggiornamenti.

## Cosa fa un'esecuzione

1. **Aggiorna prima topgrade.** Altrimenti il passaggio Homebrew dell'esecuzione aggiorna topgrade stesso e
   `--cleanup` rimuove la cartella della versione ancora in esecuzione. I passaggi successivi che toccano posizioni
   protette (per esempio un disco esterno) vengono allora negati da macOS, con messaggi fuorvianti.
2. **Avvia topgrade senza domande** (`--yes --no-ask-retry --no-self-update --cleanup`, esclusi gli aggiornamenti di
   sistema di macOS perché chiedono una password).
3. **Riavvia i servizi Homebrew** che eseguono ancora una versione la cui cartella è appena stata rimossa.
4. **Ripete una volta ogni passaggio non riuscito**, dopo una breve pausa, proprio quel passaggio
   (`topgrade --only <step>`). I nomi dei passaggi provengono dal codice sorgente di topgrade, quindi il riepilogo
   viene compreso in ogni lingua che topgrade parla.
5. **Esegue i tuoi passaggi aggiuntivi** dalla cartella hooks.
6. **Scrive un rapporto** e lo apre nel browser (sempre, solo in caso di problemi o mai). Le vecchie esecuzioni
   finiscono nel Cestino dopo un po'; non viene eliminato nulla.

## Installazione

Richiede macOS, [Homebrew](https://brew.sh) e topgrade (`brew install topgrade`). Upgrade All in sé non ha
dipendenze: gira con `/usr/bin/python3`, incluso negli Command Line Tools di Apple. Li installa l'installer di
Homebrew; altrimenti `xcode-select --install`.

```bash
git clone https://github.com/simon-says-labs/upgrade-all
cd upgrade-all
/usr/bin/python3 -m upgrade_all install
```

Questo copia il programma in `~/Library/Application Support/upgrade-all/` e configura il processo in background
`labs.simon-says.upgrade-all` (ogni 3 giorni). Provalo subito:

```bash
~/Library/Application\ Support/upgrade-all/upgrade-all run
```

## Comandi

| Comando | Cosa fa |
|---|---|
| `upgrade-all run` | Aggiorna adesso (è ciò che esegue il processo in background). |
| `upgrade-all status` | Processo in background, ultima esecuzione, prossima esecuzione, ultimo rapporto. |
| `upgrade-all grant-access [step]` | Fa sì che macOS chieda di nuovo l'accesso per il topgrade attuale (vedi sotto). |
| `upgrade-all install` | Installa o aggiorna; le tue impostazioni restano. `--no-agent` salta il processo in background. |
| `upgrade-all uninstall` | Disattiva il processo in background e sposta il programma nel Cestino. `--logs` sposta anche i log. |

## Impostazioni

`~/Library/Application Support/upgrade-all/config.json`:

| Impostazione | Predefinito | Significato |
|---|---|---|
| `interval_days` | `3` | Giorni tra due esecuzioni. Dopo averlo cambiato, esegui di nuovo `install`. |
| `language` | `auto` | Lingua del rapporto: `auto` (lingua di macOS), `en`, `de`, `fr`, `it`, `es`. |
| `disable_steps` | `["system"]` | Passaggi di topgrade da escludere, ad es. `["system", "uv"]`. |
| `cleanup` | `true` | Rimuovere le vecchie versioni dopo l'aggiornamento (`--cleanup`). |
| `pre_upgrade_topgrade` | `true` | Aggiornare topgrade con Homebrew prima dell'esecuzione. |
| `restart_outdated_services` | `true` | Riavviare i servizi Homebrew che eseguono ancora una versione rimossa. |
| `retry_failed` | `true` | Ripetere una volta i passaggi non riusciti. |
| `retry_delay_seconds` | `30` | Pausa prima del nuovo tentativo. |
| `timeout_minutes` | `180` | Interrompere topgrade se dura più a lungo. |
| `open_report` | `always` | `always` (sempre), `problems` (solo in caso di problemi) o `never` (mai). |
| `keep_runs` | `60` | Esecuzioni da conservare; log e rapporti più vecchi finiscono nel Cestino. |
| `access_probe_step` | `skills` | Passaggio usato da `grant-access` se l'ultima esecuzione non ne ha indicato nessuno. |
| `extra_topgrade_args` | `[]` | Altri argomenti per topgrade, ad es. `["--disable", "containers"]`. |

## Passaggi aggiuntivi (hook)

Metti file eseguibili in `~/Library/Application Support/upgrade-all/hooks/`. Vengono eseguiti dopo topgrade, in
ordine di nome. Il codice di uscita `0` significa OK, `3` saltato, qualsiasi altro non riuscito. Una riga che inizia
con `Summary:` compare nel rapporto. Sono impostate `UPGRADE_ALL_LANGUAGE` e `UPGRADE_ALL_LOGS`. Un passaggio
aggiuntivo non cambia mai il risultato di topgrade. In [examples/hooks](../examples/hooks) trovi un esempio che
mantiene un Brewfile di tutto ciò che è installato.

Un hook che si trova su un disco esterno può fallire in background con `Operation not permitted` (uscita 126):
macOS controlla l'accesso per ogni programma, e `/bin/sh` di solito lì non ha il permesso. Tieni questi hook sul
disco interno, oppure falli avviare da un interprete che ha già l'accesso (per esempio
`#!/opt/homebrew/bin/python3`).

## Quando macOS nega l'accesso

macOS ricorda alcuni permessi, come l'accesso ai file su un disco esterno, **per ogni file di programma**. Il
percorso del file di topgrade contiene la sua versione, quindi ogni aggiornamento di topgrade riparte senza quel
permesso, e da un terminale macOS non lo chiede mai: lì è responsabile l'app del terminale, non topgrade. Se un
passaggio viene ancora negato dopo il nuovo tentativo, il rapporto lo dice e indica il comando:

```bash
upgrade-all grant-access skills
```

Esegue quel singolo passaggio come processo in background, come fa l'esecuzione programmata, così macOS chiede;
poi fai clic su **Consenti**.

## Sviluppo

```bash
/usr/bin/python3 -m unittest discover -s tests       # sostituti di topgrade e brew, non viene aggiornato nulla
/usr/bin/python3 -m upgrade_all sample-report /tmp/report.html --language de
/usr/bin/python3 tools/update_steps.py v17.12.3       # aggiorna la tabella dei passaggi dal codice sorgente di topgrade
```

Vedi [CONTRIBUTING.md](../CONTRIBUTING.md). Modifiche: [CHANGELOG.md](../CHANGELOG.md).

## Licenza

[MIT](../LICENSE) © 2026 Simon Eckmiller · pubblicato da [Simon Says](https://github.com/simon-says-labs).
Componenti di terze parti: [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Upgrade All è un progetto
indipendente e non fa parte di topgrade.

<p align="right"><a href="#upgrade-all">↑</a></p>
