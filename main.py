import csv
import re
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from database import supabase_get, supabase_post, supabase_patch, supabase_head

app = FastAPI(title="Llamadas CRM")

USERS = ["LUIS", "NAYELI", "MARCOS"]
BATCH_SIZE = 10

STATUS_OPTIONS = [
    ("contacted", "Contactado"),
    ("no_answer", "No contestó"),
    ("busy", "Ocupado"),
    ("wrong_number", "Número equivocado"),
    ("interested", "Interesado"),
    ("not_interested", "No interesado"),
    ("callback", "Llamar después"),
]


def normalize_phone(phone: str) -> str:
    return re.sub(r"[^\d+]", "", phone)


def seed_users():
    existing = supabase_get("crm_users", {"select": "name"})
    existing_names = {u["name"] for u in existing}
    for name in USERS:
        if name not in existing_names:
            supabase_post("crm_users", {"name": name})


def import_contacts():
    count = supabase_head("crm_contacts")
    if count > 0:
        return
    rows = []
    with open("contacts_merged.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "").strip()
            phone = normalize_phone(row.get("Phone", "").strip())
            if name and phone:
                rows.append({"name": name, "phone": phone})
    # Insert in batches of 500
    for i in range(0, len(rows), 500):
        supabase_post("crm_contacts", rows[i : i + 500])


@app.on_event("startup")
def startup():
    seed_users()
    import_contacts()


# ─── HTML HELPERS ───

def page(title: str, body: str) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - Llamadas CRM</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#f0f2f5; color:#333; }}
  .container {{ max-width:900px; margin:0 auto; padding:20px; }}
  h1 {{ color:#1a73e8; margin-bottom:20px; }}
  h2 {{ color:#333; margin-bottom:15px; }}
  .btn {{ display:inline-block; padding:12px 30px; margin:8px; border:none; border-radius:8px;
          font-size:16px; font-weight:600; cursor:pointer; text-decoration:none; color:#fff; transition:transform 0.1s; }}
  .btn:hover {{ transform:scale(1.05); }}
  .btn-luis {{ background:#1a73e8; }}
  .btn-nayeli {{ background:#e91e63; }}
  .btn-marcos {{ background:#ff9800; }}
  .btn-submit {{ background:#4caf50; padding:10px 25px; }}
  .btn-next {{ background:#1a73e8; padding:10px 25px; margin-top:15px; }}
  .btn-sm {{ padding:8px 16px; font-size:14px; margin:4px; }}
  .btn-stats {{ background:#9c27b0; }}
  .btn-back {{ background:#757575; padding:8px 16px; font-size:14px; }}
  .card {{ background:#fff; border-radius:10px; padding:20px; margin-bottom:15px; box-shadow:0 2px 8px rgba(0,0,0,0.1); }}
  .contact-row {{ display:flex; align-items:center; gap:15px; flex-wrap:wrap; }}
  .contact-info {{ flex:1; min-width:200px; }}
  .contact-info h3 {{ font-size:16px; margin-bottom:4px; }}
  .contact-info p {{ color:#666; font-size:14px; }}
  .form-group {{ margin:8px 0; }}
  .form-group label {{ font-weight:600; font-size:13px; display:block; margin-bottom:4px; }}
  .form-group select, .form-group input, .form-group textarea {{
    width:100%; padding:8px; border:1px solid #ddd; border-radius:5px; font-size:14px; }}
  .form-group textarea {{ resize:vertical; min-height:60px; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; color:#fff; }}
  .badge-pending {{ background:#9e9e9e; }}
  .badge-completed {{ background:#4caf50; }}
  .user-select {{ text-align:center; padding:60px 20px; }}
  .user-select h1 {{ font-size:32px; margin-bottom:30px; }}
  .progress {{ background:#e0e0e0; border-radius:10px; height:20px; margin:15px 0; overflow:hidden; }}
  .progress-bar {{ height:100%; background:#4caf50; border-radius:10px; transition:width 0.3s; }}
  .stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(200px,1fr)); gap:15px; margin:20px 0; }}
  .stat-card {{ background:#fff; border-radius:10px; padding:20px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.1); }}
  .stat-card .number {{ font-size:36px; font-weight:700; color:#1a73e8; }}
  .stat-card .label {{ font-size:14px; color:#666; margin-top:5px; }}
  table {{ width:100%; border-collapse:collapse; margin:15px 0; }}
  th, td {{ padding:10px; text-align:left; border-bottom:1px solid #eee; }}
  th {{ background:#f5f5f5; font-weight:600; }}
  .nav {{ display:flex; gap:10px; margin-bottom:20px; flex-wrap:wrap; align-items:center; }}
  .completed-mark {{ color:#4caf50; font-weight:bold; }}
  .phone-link {{ color:#1a73e8; text-decoration:none; font-weight:500; }}
</style>
</head>
<body>
<div class="container">
{body}
</div>
</body>
</html>"""
    return HTMLResponse(html)


# ─── ROUTES ───

@app.get("/", response_class=HTMLResponse)
def home():
    body = """
    <div class="user-select">
        <h1>Llamadas CRM</h1>
        <p style="font-size:18px; color:#666; margin-bottom:30px;">Selecciona tu nombre para comenzar</p>
        <div>
            <a href="/dashboard/LUIS" class="btn btn-luis">LUIS</a>
            <a href="/dashboard/NAYELI" class="btn btn-nayeli">NAYELI</a>
            <a href="/dashboard/MARCOS" class="btn btn-marcos">MARCOS</a>
        </div>
        <div style="margin-top:40px;">
            <a href="/stats" class="btn btn-stats">Estadisticas Generales</a>
        </div>
    </div>
    """
    return page("Inicio", body)


def get_user(username: str):
    users = supabase_get("crm_users", {"name": f"eq.{username}", "select": "*"})
    return users[0] if users else None


@app.get("/dashboard/{username}", response_class=HTMLResponse)
def dashboard(username: str):
    username = username.upper()
    user = get_user(username)
    if not user:
        return page("Error", "<h1>Usuario no encontrado</h1><a href='/' class='btn btn-back'>Volver</a>")

    user_id = user["id"]
    total_contacts = supabase_head("crm_contacts")

    # Count completed logs for this user
    completed_count = supabase_head("crm_call_logs", {
        "user_id": f"eq.{user_id}",
        "completed": "eq.true",
    })

    # Get IDs already handled by this user
    handled = supabase_get("crm_call_logs", {
        "user_id": f"eq.{user_id}",
        "select": "contact_id",
    })
    handled_ids = [h["contact_id"] for h in handled]

    # Get next batch of unhandled contacts
    if handled_ids:
        not_in = ",".join(str(i) for i in handled_ids)
        pending_contacts = supabase_get("crm_contacts", {
            "id": f"not.in.({not_in})",
            "order": "id.asc",
            "limit": str(BATCH_SIZE),
            "select": "*",
        })
    else:
        pending_contacts = supabase_get("crm_contacts", {
            "order": "id.asc",
            "limit": str(BATCH_SIZE),
            "select": "*",
        })

    pending_total = total_contacts - len(handled_ids)
    progress_pct = round((completed_count / total_contacts * 100), 1) if total_contacts > 0 else 0

    # Check if current batch has logs
    batch_ids = [c["id"] for c in pending_contacts]
    batch_logs = []
    if batch_ids:
        in_ids = ",".join(str(i) for i in batch_ids)
        batch_logs = supabase_get("crm_call_logs", {
            "user_id": f"eq.{user_id}",
            "contact_id": f"in.({in_ids})",
            "select": "*",
        })
    logs_by_contact = {l["contact_id"]: l for l in batch_logs}

    batch_complete = len(batch_logs) >= len(pending_contacts) and all(
        logs_by_contact.get(c["id"], {}).get("completed", False) for c in pending_contacts
    ) if pending_contacts else True

    nav = f"""
    <div class="nav">
        <a href="/" class="btn btn-back">Cambiar usuario</a>
        <a href="/stats/{username}" class="btn btn-sm btn-stats">Mis estadisticas</a>
        <a href="/stats" class="btn btn-sm btn-stats">Stats generales</a>
    </div>
    <h1>Hola, {username}</h1>
    <div class="card">
        <p><strong>{completed_count}</strong> de <strong>{total_contacts}</strong> contactos completados
           &nbsp;|&nbsp; <strong>{pending_total}</strong> pendientes</p>
        <div class="progress"><div class="progress-bar" style="width:{progress_pct}%"></div></div>
    </div>
    """

    if not pending_contacts:
        nav += '<div class="card"><h2>Todos los contactos han sido completados!</h2></div>'
        return page(f"Dashboard - {username}", nav)

    contacts_html = ""
    for c in pending_contacts:
        log = logs_by_contact.get(c["id"])
        is_done = log and log.get("completed")

        if is_done:
            contacts_html += f"""
            <div class="card" style="opacity:0.7;">
                <div class="contact-row">
                    <div class="contact-info">
                        <h3>{c['name']} <span class="completed-mark">OK</span></h3>
                        <p><a href="tel:{c['phone']}" class="phone-link">{c['phone']}</a></p>
                    </div>
                    <span class="badge badge-completed">{log['status']}</span>
                    <p style="font-size:13px; color:#666;">{log.get('notes', '') or ''}</p>
                </div>
            </div>
            """
        else:
            current_status = log["status"] if log else ""
            current_notes = log["notes"] if log else ""
            current_callback = log.get("callback_date", "") if log else ""

            options = ""
            for val, label in STATUS_OPTIONS:
                sel = "selected" if val == current_status else ""
                options += f'<option value="{val}" {sel}>{label}</option>'

            contacts_html += f"""
            <div class="card">
                <form method="post" action="/log/{username}/{c['id']}">
                    <div class="contact-row">
                        <div class="contact-info">
                            <h3>{c['name']}</h3>
                            <p><a href="tel:{c['phone']}" class="phone-link">{c['phone']}</a></p>
                        </div>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
                        <div class="form-group">
                            <label>Estado</label>
                            <select name="status" required>
                                <option value="">-- Seleccionar --</option>
                                {options}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Fecha callback</label>
                            <input type="date" name="callback_date" value="{current_callback or ''}">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Notas</label>
                        <textarea name="notes" placeholder="Escribe tus notas aqui...">{current_notes or ''}</textarea>
                    </div>
                    <button type="submit" class="btn btn-submit btn-sm">Guardar</button>
                </form>
            </div>
            """

    next_btn = ""
    if batch_complete:
        next_btn = f'<a href="/dashboard/{username}" class="btn btn-next">Siguiente 10 contactos</a>'
    else:
        next_btn = '<p style="color:#999; margin-top:10px;">Completa todos los contactos del lote para avanzar.</p>'

    body = nav + f"<h2>Lote actual ({BATCH_SIZE} contactos)</h2>" + contacts_html + next_btn
    return page(f"Dashboard - {username}", body)


@app.post("/log/{username}/{contact_id}")
def save_log(
    username: str,
    contact_id: int,
    status: str = Form(...),
    notes: str = Form(""),
    callback_date: str = Form(""),
):
    username = username.upper()
    user = get_user(username)
    if not user:
        return RedirectResponse("/", status_code=303)

    user_id = user["id"]
    now = datetime.now(timezone.utc).isoformat()

    # Check if log exists
    existing = supabase_get("crm_call_logs", {
        "user_id": f"eq.{user_id}",
        "contact_id": f"eq.{contact_id}",
        "select": "id",
    })

    log_data = {
        "status": status,
        "notes": notes,
        "callback_date": callback_date or None,
        "interested": status == "interested",
        "completed": True,
        "updated_at": now,
    }

    if existing:
        supabase_patch("crm_call_logs", {"id": f"eq.{existing[0]['id']}"}, log_data)
    else:
        log_data.update({
            "user_id": user_id,
            "contact_id": contact_id,
            "created_at": now,
        })
        supabase_post("crm_call_logs", log_data)

    return RedirectResponse(f"/dashboard/{username}", status_code=303)


@app.get("/stats", response_class=HTMLResponse)
def general_stats():
    total_contacts = supabase_head("crm_contacts")
    total_logs = supabase_head("crm_call_logs", {"completed": "eq.true"})

    # All completed logs with user info
    all_logs = supabase_get("crm_call_logs", {
        "completed": "eq.true",
        "select": "status,user_id,crm_users(name)",
    })

    # Status counts
    status_counts = {}
    user_stats = {}
    for log in all_logs:
        s = log["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

        uname = log.get("crm_users", {}).get("name", "?")
        if uname not in user_stats:
            user_stats[uname] = {"total": 0, "interested": 0, "not_interested": 0, "no_answer": 0, "contacted": 0, "callback": 0, "wrong_number": 0, "busy": 0}
        user_stats[uname]["total"] += 1
        if s in user_stats[uname]:
            user_stats[uname][s] += 1

    status_labels = dict(STATUS_OPTIONS)

    stats_cards = f"""
    <div class="stats-grid">
        <div class="stat-card"><div class="number">{total_contacts}</div><div class="label">Total contactos</div></div>
        <div class="stat-card"><div class="number">{total_logs}</div><div class="label">Llamadas realizadas</div></div>
        <div class="stat-card"><div class="number">{total_contacts - total_logs}</div><div class="label">Pendientes</div></div>
    </div>
    """

    status_rows = ""
    for s, count in status_counts.items():
        pct = round(count / total_logs * 100, 1) if total_logs > 0 else 0
        status_rows += f"<tr><td>{status_labels.get(s, s)}</td><td>{count}</td><td>{pct}%</td></tr>"

    status_table = f"""
    <div class="card">
        <h2>Desglose por estado</h2>
        <table><tr><th>Estado</th><th>Cantidad</th><th>%</th></tr>{status_rows}</table>
    </div>
    """

    user_rows = ""
    for uname, us in user_stats.items():
        user_rows += f"""<tr>
            <td><strong>{uname}</strong></td><td>{us['total']}</td><td>{us['interested']}</td>
            <td>{us['not_interested']}</td><td>{us['no_answer']}</td><td>{us['contacted']}</td>
            <td>{us['callback']}</td><td>{us['wrong_number']}</td><td>{us['busy']}</td>
        </tr>"""

    user_table = f"""
    <div class="card">
        <h2>Por usuario</h2>
        <table>
            <tr><th>Usuario</th><th>Total</th><th>Interesado</th><th>No interesado</th><th>No contesto</th><th>Contactado</th><th>Callback</th><th>Num. equivocado</th><th>Ocupado</th></tr>
            {user_rows}
        </table>
    </div>
    """

    body = f"""
    <div class="nav"><a href="/" class="btn btn-back">Volver</a></div>
    <h1>Estadisticas Generales</h1>
    {stats_cards}{status_table}{user_table}
    """
    return page("Estadisticas", body)


@app.get("/stats/{username}", response_class=HTMLResponse)
def user_stats_page(username: str):
    username = username.upper()
    user = get_user(username)
    if not user:
        return page("Error", "<h1>Usuario no encontrado</h1>")

    user_id = user["id"]
    total_contacts = supabase_head("crm_contacts")
    total = supabase_head("crm_call_logs", {"user_id": f"eq.{user_id}", "completed": "eq.true"})

    logs = supabase_get("crm_call_logs", {
        "user_id": f"eq.{user_id}",
        "completed": "eq.true",
        "select": "status",
    })

    status_counts = {}
    for l in logs:
        s = l["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    status_labels = dict(STATUS_OPTIONS)

    stats_cards = f"""
    <div class="stats-grid">
        <div class="stat-card"><div class="number">{total}</div><div class="label">Llamadas realizadas</div></div>
        <div class="stat-card"><div class="number">{total_contacts - total}</div><div class="label">Pendientes</div></div>
        <div class="stat-card"><div class="number">{round(total/total_contacts*100,1) if total_contacts else 0}%</div><div class="label">Progreso</div></div>
    </div>
    """

    rows = ""
    for s, count in status_counts.items():
        pct = round(count / total * 100, 1) if total > 0 else 0
        rows += f"<tr><td>{status_labels.get(s, s)}</td><td>{count}</td><td>{pct}%</td></tr>"

    # Recent logs
    recent = supabase_get("crm_call_logs", {
        "user_id": f"eq.{user_id}",
        "completed": "eq.true",
        "select": "status,notes,updated_at,crm_contacts(name,phone)",
        "order": "updated_at.desc",
        "limit": "20",
    })

    recent_rows = ""
    for log in recent:
        c = log.get("crm_contacts", {})
        recent_rows += f"""<tr>
            <td>{c.get('name','')}</td><td>{c.get('phone','')}</td>
            <td>{status_labels.get(log['status'], log['status'])}</td>
            <td>{log.get('notes','') or '-'}</td>
            <td>{(log.get('updated_at','') or '')[:16]}</td>
        </tr>"""

    body = f"""
    <div class="nav">
        <a href="/dashboard/{username}" class="btn btn-back">Mi dashboard</a>
        <a href="/stats" class="btn btn-sm btn-stats">Stats generales</a>
        <a href="/" class="btn btn-back">Inicio</a>
    </div>
    <h1>Estadisticas de {username}</h1>
    {stats_cards}
    <div class="card">
        <h2>Desglose por estado</h2>
        <table><tr><th>Estado</th><th>Cantidad</th><th>%</th></tr>{rows}</table>
    </div>
    <div class="card">
        <h2>Ultimas 20 llamadas</h2>
        <table><tr><th>Nombre</th><th>Telefono</th><th>Estado</th><th>Notas</th><th>Fecha</th></tr>{recent_rows}</table>
    </div>
    """
    return page(f"Stats - {username}", body)
