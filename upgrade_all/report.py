"""The HTML report of a run: one self-contained file, no scripts, no web fonts, no external requests.

Every value that comes from a log or a program is escaped.

Copyright (c) 2026 Simon Eckmiller. MIT License.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from html import escape
from pathlib import Path

from . import summary
from .texts import text

LOGO = (
    '<svg viewBox="0 0 1024 1024" width="44" height="44" aria-hidden="true"><g transform="translate(0,1024) scale(0.1,-0.1)">'
    '<path fill="#e39ab1" d="M4415 8323c-700-68-1224-375-1468-858-288-571-66-1211 556-1597 352-219 808-350 1617-463 603-84 855-128 '
    '1105-192 691-176 1116-495 1304-978 22-55 45-128 52-162 7-35 16-63 20-63 12 0 22 246 15 359-10 154-32 270-76 404-147 441-447 '
    '736-950 937-256 102-536 169-1110 265-267 45-329 59-402 92-182 81-198 267-31 350l58 28 580 3 580 3 175-82c96-45 265-123 '
    '375-174 110-51 317-147 459-214 143-67 269-121 281-121 27 0 55 29 55 57 0 12-76 158-168 325-93 167-174 312-180 324-9 18-7 27 '
    '17 60 115 156 182 391 167 584-18 245-124 462-320 655-232 229-544 375-946 441-93 15-199 18-915 19-445 1-828 1-850-2z"/>'
    '<path fill="#ffffff" d="M2676 6657c-46-234-63-759-31-999 81-615 473-1073 1142-1335 62-24 157-56 210-71l97-27-425-6c-473-6'
    '-476-7-625-80-334-163-495-553-375-908 66-195 188-348 387-484l62-42-179-357c-99-197-179-368-179-381 0-28 29-57 56-57 11 0 '
    '134 61 274 136 140 75 368 196 506 269l251 132 139-20c129-18 207-20 1074-24 992-5 1069-2 1275 41 490 104 900 410 1066 796 '
    '257 596-11 1215-666 1542-359 180-699 259-1489 349-682 77-971 127-1286 225-724 225-1142 654-1237 1270-10 63-20 114-24 '
    '114-3 0-14-37-23-83z"/></g></svg>')

STYLE = """
:root{--blue:#1a6e99;--wine:#7a1f3d;--ok:#2f855a;--warn:#c05621;--bg:#f4f6f8;--card:#fff;--text:#14202b;--muted:#5b6b78;
--line:#e2e8ee;--shadow:0 8px 24px rgba(10,24,34,.07)}
@media (prefers-color-scheme:dark){:root{--bg:#0d151c;--card:#14202a;--text:#e8eef3;--muted:#9fb0bd;--line:#26343f;
--shadow:0 8px 24px rgba(0,0,0,.35)}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 -apple-system,BlinkMacSystemFont,
"Segoe UI",Helvetica,Arial,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:20px 16px 72px}
header{border-radius:18px;overflow:hidden;box-shadow:var(--shadow);margin-bottom:18px;
background:radial-gradient(900px 400px at 0 0,#12405c 0,transparent 60%),radial-gradient(700px 400px at 100% 100%,#3d0f22 0,
transparent 60%),#0a1822;color:#eef3f7;padding:22px 22px 18px}
.brand{display:flex;align-items:center;gap:12px}.brand small{display:block;color:#e39ab1;font-weight:700;letter-spacing:.02em}
h1{margin:14px 0 4px;font-size:26px;line-height:1.2}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.meta span{background:rgba(255,255,255,.1);border-radius:999px;
padding:4px 12px;font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);margin-top:16px;overflow:hidden}
.card h2{margin:0;padding:12px 16px;font-size:16px;border-bottom:1px solid var(--line)}
.body{padding:14px 16px}
.callout{border-left:6px solid var(--ok);background:rgba(47,133,90,.08);padding:10px 14px;border-radius:10px;margin:0 0 12px}
.callout.warn{border-left-color:var(--warn);background:rgba(192,86,33,.09)}
.kv{display:grid;grid-template-columns:minmax(140px,220px) 1fr;gap:6px 14px;font-size:14px}.kv .k{color:var(--muted)}
.table{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}th{color:var(--muted);font-weight:600}
.badge{display:inline-block;border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700;color:#fff;background:#56636e}
.badge.ok{background:var(--ok)}.badge.failed{background:var(--warn)}
code,pre{font:12.5px/1.45 ui-monospace,Menlo,monospace}
code{background:rgba(127,140,150,.15);border-radius:6px;padding:1px 6px;word-break:break-all}
details{border:1px solid var(--line);border-radius:12px;margin:10px 0}summary{cursor:pointer;padding:10px 14px;font-weight:600}
pre{margin:0;padding:12px 14px;background:#0b1117;color:#e8eef3;overflow:auto;max-height:520px;border-radius:0 0 12px 12px}
footer{color:var(--muted);font-size:13px;margin-top:18px}a{color:var(--blue)}
.bar{position:fixed;left:0;right:0;bottom:0;background:rgba(10,24,34,.92);color:#fff;font-size:13px}
.bar div{max-width:1040px;margin:0 auto;padding:8px 16px;display:flex;gap:10px;flex-wrap:wrap}
.bar span{border:1px solid rgba(255,255,255,.2);border-radius:999px;padding:2px 10px}
"""


def _badge(status: str, language: str) -> str:
    kind = summary.outcome(status)
    word = text(language, "outcome_" + kind) if kind in ("ok", "failed", "skipped") else status
    return '<span class="badge %s">%s</span>' % (kind if kind in ("ok", "failed") else "", escape(word))


def _join(items) -> str:
    return ", ".join(escape(str(i)) for i in items)


def _log_block(label: str, path: str) -> str:
    if not path or not Path(path).exists():
        return ""
    content = summary.clean(Path(path).read_text(errors="replace"))
    return "<details><summary>%s</summary><pre>%s</pre></details>" % (escape(label), escape(content))


def _short(path: str) -> str:
    """~/... instead of /Users/<name>/... in what the report shows."""
    home = str(Path.home())
    return "~" + path[len(home):] if path.startswith(home + "/") else path


def _duration(seconds: int) -> str:
    return "%d:%02d min" % (seconds // 60, seconds % 60)


def render(result) -> str:
    t = lambda key, *args: text(result.language, key, *args)  # noqa: E731
    started = datetime.fromisoformat(result.started)
    when = started.strftime("%Y-%m-%d %H:%M")
    next_run = (started + timedelta(days=float(result.interval_days))).strftime("%Y-%m-%d %H:%M")
    problems = result.outcome == "failed"

    if result.outcome == "ok" and not result.hook_problems:
        hero, pill = t("hero_ok"), t("pill_ok")
    elif result.outcome == "fixed" and not result.hook_problems:
        hero, pill = t("hero_fixed"), t("pill_fixed")
    elif not problems:
        hero, pill = t("hero_hooks"), t("pill_warn")
    else:
        hero, pill = t("hero_failed"), t("pill_warn")

    notes = []
    if result.timed_out:
        notes.append(("warn", escape(t("status_timeout", result.timeout_minutes))))
    elif result.outcome == "ok":
        notes.append(("", escape(t("status_ok"))))
    elif result.outcome == "fixed":
        notes.append(("", escape(t("status_fixed", ", ".join(result.fixed)))))
    elif result.still_failed:
        notes.append(("warn", escape(t("status_failed", ", ".join(result.still_failed)))))
    else:
        notes.append(("warn", escape(t("status_aborted"))))
    if result.hook_problems:
        notes.append(("warn", escape(t("status_hooks", ", ".join(result.hook_problems)))))
    if result.access_problem:
        step = result.access_steps[0] if result.access_steps else "skills"
        notes.append(("warn", "<b>%s</b><br>%s <code>upgrade-all grant-access %s</code>" % (
            escape(t("access_title")), escape(t("access_text", result.topgrade_path)), escape(step))))
    callouts = "".join('<p class="callout %s">%s</p>' % (kind, body) for kind, body in notes)

    if result.pre_exit is None:
        pre = t("fix_pre_off")
    elif result.pre_exit != 0:
        pre = t("fix_pre_failed", result.pre_exit, result.version_after or "?")
    elif result.version_before != result.version_after:
        pre = t("fix_pre_updated", result.version_before, result.version_after)
    else:
        pre = t("fix_pre_current", result.version_after)
    fixes = [pre]
    fixes.append(t("fix_retry", ", ".join(result.retried), len(result.fixed), len(result.still_failed))
                 if result.retried else t("fix_no_retry"))
    if result.unknown_failed:
        fixes.append(t("fix_unknown", ", ".join(result.unknown_failed)))
    if result.services_restarted:
        fixes.append(t("fix_services", ", ".join(result.services_restarted)))
    if result.services_failed:
        fixes.append(t("fix_services_failed", ", ".join(result.services_failed)))

    rows = []
    for row in result.rows:
        if row.outcome == "failed":
            retry = (escape(t("retry_result", "")) + _badge(row.retry_status, result.language)) if row.retried \
                else escape(t("not_retried")) if not row.known else "–"
        else:
            retry = escape(t("no_retry_needed"))
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (escape(row.label), _badge(row.status, result.language), retry))
    if not rows:
        rows.append('<tr><td colspan="3">%s</td></tr>' % escape(t("no_summary")))

    hooks = ""
    if result.hooks:
        items = []
        for hook in result.hooks:
            state = t("hook_ok") if hook.outcome == "ok" else t("hook_skipped") if hook.outcome == "skipped" \
                else t("hook_failed", hook.exit_code)
            items.append("<tr><td>%s</td><td><span class=\"badge %s\">%s</span></td><td>%s%s</td></tr>" % (
                escape(hook.name), "ok" if hook.outcome == "ok" else "failed" if hook.outcome == "failed" else "",
                escape(state), escape(hook.summary), _log_block(t("show_hook_log"), hook.log_file)))
        hooks = ('<section class="card"><h2>%s</h2><div class="body table"><table><tbody>%s</tbody></table></div></section>'
                 % (escape(t("section_hooks")), "".join(items)))

    logs = _log_block(t("show_log", Path(result.log_file).name), result.log_file)
    logs += _log_block(t("show_retry_log", Path(result.retry_log_file).name), result.retry_log_file) if result.retry_log_file else ""

    return """<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="author" content="Simon Eckmiller"><meta name="generator" content="Upgrade All {version}">
<title>{title} · {when}</title><style>{style}</style></head>
<body id="top"><div class="wrap">
<header><div class="brand">{logo}<div><b>Upgrade All</b><small>{tagline}</small></div></div>
<h1>{hero}</h1>
<div class="meta"><span>{l_run}: {when}</span><span>{l_duration}: {duration}</span><span>{l_host}: {host}</span>
<span>topgrade {topgrade}</span></div></header>
<section class="card"><h2>{l_status}</h2><div class="body">{callouts}
<div class="kv"><div class="k">{l_next}</div><div>{next_run} ({every})</div>
<div class="k">{l_log}</div><div><code>{log}</code></div></div></div></section>
<section class="card"><h2>{l_steps}</h2><div class="body table"><table>
<thead><tr><th>{c_step}</th><th>{c_result}</th><th>{c_retry}</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="card"><h2>{l_fixes}</h2><div class="body"><ul>{fixes}</ul></div></section>
{hooks}
<section class="card"><h2>{l_logs}</h2><div class="body">{logs}</div></section>
<footer>{footer} · <a href="#top">{back}</a></footer></div>
<div class="bar" role="status"><div><span>Upgrade All</span><span>{pill}</span><span>exit {exit_code}</span><span>{when}</span></div></div>
</body></html>
""".format(
        lang=escape(result.language), version=escape(result.upgrade_all), title=escape(t("title")), when=escape(when),
        style=STYLE, logo=LOGO, tagline=escape(t("tagline")), hero=escape(hero),
        l_run=escape(t("run")), l_duration=escape(t("duration")), duration=escape(_duration(result.seconds)),
        l_host=escape(t("host")), host=escape(result.host), topgrade=escape(result.version_after or "?"),
        l_status=escape(t("section_status")), callouts=callouts, l_next=escape(t("next_run")),
        next_run=escape(next_run), every=escape(t("every_days", ("%g" % float(result.interval_days)))),
        l_log=escape(t("log_file")), log=escape(result.log_display or _short(result.log_file)), l_steps=escape(t("section_steps")),
        c_step=escape(t("col_step")), c_result=escape(t("col_result")), c_retry=escape(t("col_retry")),
        rows="".join(rows), l_fixes=escape(t("section_fixes")),
        fixes="".join("<li>%s</li>" % escape(f) for f in fixes), hooks=hooks, l_logs=escape(t("section_log")),
        logs=logs, footer=escape(t("footer", result.upgrade_all)), back=escape(t("back_to_top")),
        pill=escape(pill), exit_code=result.exit_code)
