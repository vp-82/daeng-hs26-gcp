"""Die Werkzeuge des Triage-Agenten. Alle lesen nur, keines ändert etwas.

Ein Werkzeug ist eine Python-Funktion. Das Modell sieht ihren Namen, ihren Docstring und ihre
Parameter, und entscheidet selbst, wann es sie aufruft. Darum sind die Docstrings auf Deutsch und
sagen genau, was zurückkommt: sie sind die Bedienungsanleitung für das Modell.

Drei Regeln gelten für jedes Werkzeug hier:
1. Nur bekannte Ressourcen. Projekt, Region, Workflow, Scan und die erlaubten Jobs stehen in der
   Konfiguration des Jobs (Umgebungsvariablen), nicht im Modell. Das Modell wählt aus dieser
   Liste, es kann keine Ressource erfinden.
2. Knappe Antworten. Felder statt Rohtext, feste Obergrenzen. Jede Antwort wandert bei jedem
   weiteren Modellaufruf mit, was früh gelesen wird, geht zwanzigmal mit.
3. Kein Absturz. Ein Fehler im Werkzeug kommt als Ergebnis zurück ("status": "ERROR"), nicht als
   Exception. Sonst bricht der ganze Lauf ab, und das Modell kann nicht anders weitersuchen.
"""

import functools
import json
import os
import re
from datetime import datetime, timedelta, timezone

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
REGION = os.environ.get("PIPELINE_REGION", "europe-west6")
WORKFLOW = os.environ.get("WORKFLOW_NAME", "gtfs-pipeline")
DATASCAN = os.environ.get("DATASCAN_NAME", "trips-quality")
JOBS = [j.strip() for j in os.environ.get("PIPELINE_JOBS", "ingest-gtfs,transform-gtfs").split(",")]

_WF = f"projects/{PROJECT}/locations/{REGION}/workflows/{WORKFLOW}"
# Schritte im except-Zweig des Workflows: scheitert die Execution dort, ist das der Ort des
# raise, nicht die Ursache.
_EXCEPT_STEPS = {"rethrow", "start_triage", "log_triage_error", "pipeline"}
_SCAN = f"projects/{PROJECT}/locations/{REGION}/dataScans/{DATASCAN}"


def _job_path(job: str) -> str:
    return f"projects/{PROJECT}/locations/{REGION}/jobs/{job}"


def _ts(t):
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None


def _check_job(job_name: str):
    if job_name not in JOBS:
        raise ValueError(f"Unbekannter Job {job_name!r}. Erlaubt: {JOBS}")


def safe(fn):
    """Regel 3: Fehler als Ergebnis, nicht als Exception."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001, das Modell soll den Fehler sehen
            return {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"[:600]}
    return wrapper


# Der Workflow -----------------------------------------------------------------------------------

def get_workflow() -> dict:
    """Der überwachte Workflow: unter welchem Service-Account er läuft, aktuelle Revision und wann
    er zuletzt geändert wurde."""
    from google.cloud import workflows_v1

    w = workflows_v1.WorkflowsClient().get_workflow(name=_WF)
    return {"workflow": WORKFLOW, "service_account": w.service_account.rsplit("/", 1)[-1],
            "revision_id": w.revision_id, "revision_create_time": _ts(w.revision_create_time),
            "update_time": _ts(w.update_time), "state": w.state.name}


def get_workflow_execution(execution_id: str) -> dict:
    """Eine Execution des Workflows: Zustand, Start, Ende, der Schritt, in dem sie scheiterte, die
    Fehlermeldung (HTTP-Code und Text) und das Ergebnis, falls vorhanden."""
    from google.cloud.workflows import executions_v1

    ex = executions_v1.ExecutionsClient().get_execution(request=executions_v1.GetExecutionRequest(
        name=f"{_WF}/executions/{execution_id}", view=executions_v1.ExecutionView.FULL))
    out = {"execution_id": execution_id, "state": ex.state.name, "start": _ts(ex.start_time),
           "end": _ts(ex.end_time), "workflow_revision_id": ex.workflow_revision_id}
    if ex.error and ex.error.payload:
        steps = [e.step for e in ex.error.stack_trace.elements] if ex.error.stack_trace else []
        out["failed_step"] = steps[0] if steps else None
        if out["failed_step"] in _EXCEPT_STEPS:
            # Der Workflow hat den Fehler in seinem except-Zweig weitergeworfen. Die Execution
            # nennt dann den Schritt des raise, nicht den, der scheiterte. Den verrät die Meldung.
            out["failed_step"] = None
            out["note"] = (f"Fehler im except-Zweig weitergeworfen (Schritt {steps[0]}). Der Schritt, "
                           "der scheiterte, steht nicht in der Execution: aus error_message und "
                           "resource_in_error schliessen.")
        out["error_context"] = (ex.error.context or "").split("\n")[0][:200]
        try:
            p = json.loads(ex.error.payload)
            body = p.get("body") if isinstance(p.get("body"), dict) else {}
            err = body.get("error", {}) if body else {}
            out["http_code"] = p.get("code") or err.get("code")
            out["error_message"] = (err.get("message") or p.get("message") or str(p))[:500]
        except (ValueError, AttributeError):
            out["error_message"] = ex.error.payload[:500]
        m = re.search(r"(jobs|dataScans|workflows)/([A-Za-z0-9_-]+)", out.get("error_message") or "")
        if m:
            out["resource_in_error"] = f"{m.group(1)}/{m.group(2)}"
    if ex.result:
        try:
            out["result"] = json.loads(ex.result)
        except ValueError:
            out["result"] = ex.result[:500]
    return out


def list_workflow_executions() -> dict:
    """Die letzten 5 Executions des Workflows (neueste zuerst) mit Zustand, Start, Ende und dem
    Schritt, in dem sie scheiterten. Für den Vergleich mit der Historie."""
    from google.cloud.workflows import executions_v1

    req = executions_v1.ListExecutionsRequest(parent=_WF, page_size=5,
                                              view=executions_v1.ExecutionView.FULL)
    out = []
    for ex in executions_v1.ExecutionsClient().list_executions(request=req):
        steps = [e.step for e in ex.error.stack_trace.elements] if ex.error and ex.error.stack_trace else []
        failed = steps[0] if steps else None
        row = {"execution_id": ex.name.rsplit("/", 1)[-1], "state": ex.state.name,
               "start": _ts(ex.start_time), "end": _ts(ex.end_time),
               "failed_step": None if failed in _EXCEPT_STEPS else failed}
        if failed in _EXCEPT_STEPS:
            row["note"] = "im except-Zweig weitergeworfen, Schritt siehe Meldung"
        if ex.error and ex.error.payload:
            row["error_head"] = ex.error.payload[:120]
        out.append(row)
        if len(out) == 5:
            break
    return {"workflow": WORKFLOW, "executions": out}


# Die Jobs ---------------------------------------------------------------------------------------

def get_job(job_name: str) -> dict:
    """Konfiguration eines Cloud-Run-Jobs der Pipeline (ingest-gtfs oder transform-gtfs): Image mit
    Digest, Umgebungsvariablen, Service-Account, wann und von wem zuletzt geändert."""
    from google.cloud import run_v2

    _check_job(job_name)
    j = run_v2.JobsClient().get_job(name=_job_path(job_name))
    c = j.template.template.containers[0]
    return {"job": job_name, "image": c.image,
            "env": {e.name: (e.value if e.value else "(secret)") for e in c.env},
            "service_account": j.template.template.service_account,
            "update_time": _ts(j.update_time), "last_modifier": j.last_modifier,
            "generation": j.generation}


def list_job_executions(job_name: str) -> dict:
    """Die letzten 5 Executions eines Cloud-Run-Jobs der Pipeline (neueste zuerst): Name, Zustand,
    Start, Ende, Anzahl erfolgreicher und fehlgeschlagener Tasks."""
    from google.cloud import run_v2

    _check_job(job_name)
    out = []
    for ex in run_v2.ExecutionsClient().list_executions(parent=_job_path(job_name)):
        done = next((c for c in ex.conditions if c.type_ == "Completed"), None)
        out.append({"execution_name": ex.name.rsplit("/", 1)[-1],
                    "state": done.state.name.replace("CONDITION_", "") if done else "RUNNING",
                    "start": _ts(ex.start_time), "end": _ts(ex.completion_time),
                    "succeeded_tasks": ex.succeeded_count, "failed_tasks": ex.failed_count})
        if len(out) == 5:
            break
    return {"job": job_name, "executions": out}


def get_execution_log(execution_name: str) -> dict:
    """Die letzten 40 Logzeilen (nur Programmausgabe stdout und stderr, keine Audit-Einträge) einer
    Execution eines Cloud-Run-Jobs, zum Beispiel execution_name='ingest-gtfs-sf7bx'."""
    from google.cloud import logging as gcl

    job = execution_name.rsplit("-", 1)[0]
    _check_job(job)
    flt = (f'resource.type="cloud_run_job" AND resource.labels.job_name="{job}" '
           f'AND labels."run.googleapis.com/execution_name"="{execution_name}" '
           f'AND (logName="projects/{PROJECT}/logs/run.googleapis.com%2Fstdout" '
           f'OR logName="projects/{PROJECT}/logs/run.googleapis.com%2Fstderr")')
    entries = list(gcl.Client(project=PROJECT).list_entries(
        filter_=flt, order_by=gcl.DESCENDING, max_results=40, page_size=40))
    lines = []
    for e in reversed(entries):
        text = e.payload if isinstance(e.payload, str) else json.dumps(e.payload, ensure_ascii=False)
        lines.append(f"{e.timestamp.strftime('%H:%M:%S')} {text[:200]}")
    return {"execution_name": execution_name, "lines": lines}


# Was sich geändert hat --------------------------------------------------------------------------

_CHANGE_EXCLUDE = ("RunJob", "RunDataScan", "CreateExecution", "CancelExecution")


def _bindings(policy: dict | None) -> set[tuple[str, str]]:
    return {(b.get("role"), m) for b in (policy or {}).get("bindings", []) for m in b.get("members", [])}


def _scan_rules(request: dict | None) -> dict[str, str]:
    # Die Regeln eines UpdateDataScan- oder CreateDataScan-Aufrufs, Name -> Schwelle oder SQL,
    # damit sich zwei Fassungen der Spezifikation vergleichen lassen.
    spec = ((request or {}).get("dataScan") or {}).get("dataQualitySpec") or {}
    out = {}
    for r in spec.get("rules", []):
        if "sqlAssertion" in r:
            out[r.get("name")] = " ".join((r["sqlAssertion"].get("sqlStatement") or "").split())
        else:
            out[r.get("name")] = f"threshold={r.get('threshold')}"
    return out


def get_admin_activity(resource: str, days: int = 7) -> dict:
    """Admin-Activity-Audit-Log der letzten `days` Tage (höchstens 30) für eine Ressource der
    Pipeline: einen Job (ingest-gtfs, transform-gtfs), den Workflow (gtfs-pipeline) oder den
    Qualitäts-Scan (trips-quality). Nur Änderungen (Deploy, Update, IAM), keine Starts von Läufen.
    Pro Eintrag Zeit, Methode, Principal. Bei SetIamPolicy die hinzugefügten und entfernten
    Bindungen, bei UpdateDataScan die Regeln, die sich gegenüber der vorigen Fassung geändert
    haben. Höchstens 20 Einträge, neueste zuerst."""
    from google.cloud import logging as gcl

    days = max(1, min(int(days), 30))
    if resource in JOBS:
        sel = f'resource.type="cloud_run_job" AND resource.labels.job_name="{resource}"'
    elif resource == WORKFLOW:
        sel = f'protoPayload.resourceName:"workflows/{WORKFLOW}"'
    elif resource == DATASCAN:
        sel = f'protoPayload.resourceName:"dataScans/{DATASCAN}"'
    else:
        raise ValueError(f"Unbekannte Ressource {resource!r}. Erlaubt: {JOBS + [WORKFLOW, DATASCAN]}")
    base = (f'logName="projects/{PROJECT}/logs/cloudaudit.googleapis.com%2Factivity" AND {sel} '
            + "".join(f' AND NOT protoPayload.methodName:"{m}"' for m in _CHANGE_EXCLUDE))
    client = gcl.Client(project=PROJECT)

    # Deltas brauchen den Vorzustand, darum die Änderungen seit 90 Tagen aufsteigend lesen.
    # Ohne Zeitfilter sucht Cloud Logging nur die letzten 24 Stunden.
    lookback = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    deltas = {}
    prev_bindings = None
    for e in client.list_entries(filter_=base + f' AND protoPayload.methodName:"SetIamPolicy" AND timestamp>="{lookback}"',
                                 order_by=gcl.ASCENDING, max_results=50, page_size=50):
        cur = _bindings((e.payload.get("request") or {}).get("policy"))
        if prev_bindings is None:
            deltas[e.insert_id] = {"policy_after": sorted(f"{r} {m}" for r, m in cur),
                                   "note": "erste bekannte Änderung, kein Vorzustand im Log"}
        else:
            deltas[e.insert_id] = {"added": sorted(f"{r} {m}" for r, m in cur - prev_bindings),
                                   "removed": sorted(f"{r} {m}" for r, m in prev_bindings - cur)}
        prev_bindings = cur
    if resource == DATASCAN:
        prev_rules = None
        for e in client.list_entries(filter_=base + f' AND (protoPayload.methodName:"UpdateDataScan" OR protoPayload.methodName:"CreateDataScan") AND timestamp>="{lookback}"',
                                     order_by=gcl.ASCENDING, max_results=50, page_size=50):
            cur = _scan_rules(e.payload.get("request"))
            if not cur:
                deltas[e.insert_id] = {"note": "Spezifikation im Audit-Eintrag nicht enthalten"}
            elif prev_rules is None:
                deltas[e.insert_id] = {"rules_after": cur, "note": "erste bekannte Fassung"}
            else:
                changed = {n: {"before": prev_rules.get(n), "after": v}
                           for n, v in cur.items() if prev_rules.get(n) != v}
                changed.update({n: {"before": v, "after": None} for n, v in prev_rules.items() if n not in cur})
                deltas[e.insert_id] = {"rules_changed": changed}
            if cur:
                prev_rules = cur

    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    for e in client.list_entries(filter_=base + f' AND timestamp>="{since}"',
                                 order_by=gcl.DESCENDING, max_results=20, page_size=20):
        p = e.payload or {}
        row = {"time": _ts(e.timestamp), "method": (p.get("methodName") or "").rsplit(".", 1)[-1],
               "principal": (p.get("authenticationInfo") or {}).get("principalEmail"),
               "status": (p.get("status") or {}).get("message") or "ok"}
        if e.insert_id in deltas:
            row["delta"] = deltas[e.insert_id]
        out.append(row)
        if len(out) == 20:
            break
    return {"resource": resource, "days": days, "entries": out}


def get_datascan() -> dict:
    """Der Qualitäts-Scan der Pipeline: Tabelle, letzte Änderung der Spezifikation, jede Regel mit
    Name, Dimension, Schwelle bzw. SQL, und das Ergebnis der letzten 3 Scan-Jobs pro Regel."""
    from google.cloud import dataplex_v1

    client = dataplex_v1.DataScanServiceClient()
    s = client.get_data_scan(request=dataplex_v1.GetDataScanRequest(
        name=_SCAN, view=dataplex_v1.GetDataScanRequest.DataScanView.FULL))
    rules = []
    for r in s.data_quality_spec.rules:
        kind = dataplex_v1.DataQualityRule.pb(r).WhichOneof("rule_type")
        rule = {"name": r.name, "dimension": r.dimension, "type": kind}
        if kind == "sql_assertion":
            rule["sql"] = " ".join(r.sql_assertion.sql_statement.split())
        else:
            rule["column"], rule["threshold"] = r.column, r.threshold
        rule["results"] = []
        rules.append(rule)
    by_name = {r["name"]: r for r in rules}
    jobs = list(client.list_data_scan_jobs(request=dataplex_v1.ListDataScanJobsRequest(
        parent=_SCAN, page_size=3)))[:3]
    job_summaries = []
    for j in jobs:
        jj = client.get_data_scan_job(request=dataplex_v1.GetDataScanJobRequest(
            name=j.name, view=dataplex_v1.GetDataScanJobRequest.DataScanJobView.FULL))
        res = jj.data_quality_result
        job_summaries.append({"start": _ts(jj.start_time), "state": jj.state.name,
                              "passed": res.passed, "row_count": res.row_count})
        for rr in res.rules:
            entry = {"job_start": _ts(jj.start_time), "passed": rr.passed}
            if rr.rule.sql_assertion.sql_statement:
                entry["assertion_row_count"] = rr.assertion_row_count
            else:
                entry["evaluated"], entry["passed_count"] = rr.evaluated_count, rr.passed_count
            if rr.rule.name in by_name:
                by_name[rr.rule.name]["results"].append(entry)
    return {"scan": DATASCAN, "table": s.data.resource.split("/projects/")[-1],
            "spec_update_time": _ts(s.update_time), "jobs": job_summaries, "rules": rules,
            "note": ("Bei sql_assertion-Regeln zählt assertion_row_count: die Regel besteht, wenn die "
                     "Abfrage 0 Zeilen liefert. pass_ratio sagt bei diesen Regeln nichts aus.")}


def list_builds() -> dict:
    """Die letzten 5 Cloud Builds der Region (Deployments der Jobs aus dem Quellcode): Zeit,
    Status, Dauer, für welchen Job, Quelle."""
    from google.cloud.devtools import cloudbuild_v1

    req = cloudbuild_v1.ListBuildsRequest(project_id=PROJECT, page_size=5,
                                          parent=f"projects/{PROJECT}/locations/{REGION}")
    out = []
    for b in cloudbuild_v1.CloudBuildClient().list_builds(request=req):
        job = next((t[4:] for t in b.tags if t.startswith("job_")), None)
        src = b.source.storage_source
        dur = (b.finish_time - b.start_time).total_seconds() if b.finish_time and b.start_time else None
        out.append({"create_time": _ts(b.create_time), "status": b.status.name,
                    "duration_s": round(dur) if dur else None, "job": job,
                    "source": f"gs://{src.bucket}/{src.object_}" if src.bucket else None})
        if len(out) == 5:
            break
    return {"builds": out}


def get_load_jobs(table: str) -> dict:
    """Die letzten 10 Load-Jobs in eine Tabelle des Datasets raw (zum Beispiel table='trips'),
    neueste zuerst: Zeit, wer, Zieltabelle mit Partition, Schreibmodus (WRITE_TRUNCATE ersetzt die
    Partition, WRITE_APPEND hängt an), geladene Zeilen, Zustand. Das steht in keiner
    INFORMATION_SCHEMA-Sicht."""
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT, location=REGION)
    since = datetime.now(timezone.utc) - timedelta(days=7)
    out = []
    for job in client.list_jobs(all_users=True, min_creation_time=since, max_results=500, state_filter="done"):
        if job.job_type != "load" or not job.destination:
            continue
        dest = job.destination
        if dest.dataset_id != "raw" or dest.table_id.split("$")[0] != table:
            continue
        out.append({"created": _ts(job.created), "user": job.user_email,
                    "destination": f"{dest.dataset_id}.{dest.table_id}",
                    "write_disposition": job.write_disposition, "output_rows": job.output_rows,
                    "state": job.state, "error": (job.error_result or {}).get("message")})
        if len(out) == 10:
            break
    return {"table": f"raw.{table}", "load_jobs": out}


ALL = [get_workflow, get_workflow_execution, list_workflow_executions, get_job, list_job_executions,
       get_execution_log, get_admin_activity, get_datascan, list_builds, get_load_jobs]
