import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

# --- Configuracion ---
CLICKUP_TOKEN = os.environ["CLICKUP_TOKEN"]
LIST_ID = "901303620567"  # DOC PROVEEDORES - Contratistas
EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_TO = os.environ["EMAIL_TO"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

HEADERS = {"Authorization": CLICKUP_TOKEN}

def get_tasks():
    url = f"https://api.clickup.com/api/v2/list/{LIST_ID}/task"
    params = {
        "include_closed": "true",
        "subtasks": "true",
        "order_by": "updated",
        "reverse": "true",
    }
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json().get("tasks", [])

def get_updated_tasks(tasks):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    cutoff_ms = int(cutoff.timestamp() * 1000)
    updated = []
    for task in tasks:
        date_updated = int(task.get("date_updated", 0))
        if date_updated >= cutoff_ms:
            updated.append(task)
    return updated

def build_email_html(tasks, check_time):
    if not tasks:
        body = "<p>No se encontraron tareas actualizadas en las ultimas 24 horas.</p>"
    else:
        rows = ""
        for task in tasks:
            name = task.get("name", "Sin nombre")
            task_url = task.get("url", "#")
            status = task.get("status", {}).get("status", "desconocido")
            date_updated_ms = int(task.get("date_updated", 0))
            date_updated = datetime.fromtimestamp(
                date_updated_ms / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M UTC")
            rows += f"""
            <tr>
                <td style="padding:8px;border:1px solid #ddd;">
                    <a href="{task_url}">{name}</a>
                </td>
                <td style="padding:8px;border:1px solid #ddd;">{status}</td>
                <td style="padding:8px;border:1px solid #ddd;">{date_updated}</td>
            </tr>"""
        body = f"""
        <p>Se encontraron <strong>{len(tasks)}</strong> tarea(s) con actualizaciones en las ultimas 24 horas:</p>
        <table style="border-collapse:collapse;width:100%">
            <thead>
                <tr style="background:#f2f2f2">
                    <th style="padding:8px;border:1px solid #ddd;text-align:left">Tarea</th>
                    <th style="padding:8px;border:1px solid #ddd;text-align:left">Estado</th>
                    <th style="padding:8px;border:1px solid #ddd;text-align:left">Ultima actualizacion</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>"""
    html = f"""
    <html>
    <body>
        <h2>Revision diaria - Espacio Contratistas</h2>
        <p><em>Revisado el: {check_time}</em></p>
        {body}
        <br>
        <p>Ver espacio en <a href="https://app.clickup.com/9013251178/v/l/6-901303620567-1">ClickUp</a>.</p>
    </body>
    </html>"""
    return html

def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    part = MIMEText(html_body, "html")
    msg.attach(part)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

def main():
    now = datetime.now(timezone.utc)
    check_time = now.strftime("%Y-%m-%d %H:%M UTC")
    print(f"Iniciando revision: {check_time}")
    tasks = get_tasks()
    print(f"Total de tareas encontradas: {len(tasks)}")
    updated_tasks = get_updated_tasks(tasks)
    print(f"Tareas actualizadas en las ultimas 24h: {len(updated_tasks)}")
    if updated_tasks:
        subject = f"[ClickUp] {len(updated_tasks)} actualizacion(es) en Contratistas - {check_time}"
    else:
        subject = f"[ClickUp] Sin actualizaciones en Contratistas - {check_time}"
    html_body = build_email_html(updated_tasks, check_time)
    send_email(subject, html_body)
    print("Email enviado correctamente.")

if __name__ == "__main__":
    main()
