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
          "page": 0
      }
      response = requests.get(url, headers=HEADERS, params=params)
      response.raise_for_status()
      return response.json().get("tasks", [])

def check_updates():
      now = datetime.now(timezone.utc)
      since = now - timedelta(hours=24)
      since_ms = int(since.timestamp() * 1000)

    tasks = get_tasks()
    updated_tasks = []

    for task in tasks:
              date_updated = int(task.get("date_updated", 0))
              if date_updated >= since_ms:
                            updated_tasks.append({
                                              "name": task.get("name", "Sin nombre"),
                                              "status": task.get("status", {}).get("status", "N/A"),
                                              "updated": datetime.fromtimestamp(date_updated / 1000, tz=timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
                                              "url": task.get("url", "")
                            })

          return updated_tasks

def build_email_body(tasks):
      fecha = datetime.now(timezone.utc).strftime("%d/%m/%Y")
      if not tasks:
                return f"""
                <h2>Reporte diario - Espacio Contratistas</h2>
                <p><b>Fecha:</b> {fecha}</p>
                <p>No se encontraron actualizaciones en las ultimas 24 horas en el espacio Contratistas.</p>
                """
            rows = ""
    for t in tasks:
              rows += f"""
              <tr>
                <td style="padding:8px;border:1px solid #ddd;">{t['name']}</td>
                  <td style="padding:8px;border:1px solid #ddd;">{t['status']}</td>
                    <td style="padding:8px;border:1px solid #ddd;">{t['updated']}</td>
                      <td style="padding:8px;border:1px solid #ddd;"><a href="{t['url']}">Ver tarea</a></td>
      </tr>"""
          return f"""
<h2>Reporte diario - Espacio Contratistas</h2>
<p><b>Fecha:</b> {fecha}</p>
<p>Se encontraron <b>{len(tasks)}</b> tarea(s) actualizadas en las ultimas 24 horas:</p>
<table style="border-collapse:collapse;width:100%">
  <tr style="background:#f2f2f2;">
    <th style="padding:8px;border:1px solid #ddd;">Tarea</th>
    <th style="padding:8px;border:1px solid #ddd;">Estado</th>
    <th style="padding:8px;border:1px solid #ddd;">Ultima actualizacion</th>
    <th style="padding:8px;border:1px solid #ddd;">Link</th>
  </tr>
  {rows}
</table>
<br><p style="color:gray;font-size:12px;">Generado automaticamente por GitHub Actions</p>
"""

def send_email(body, task_count):
    subject = f"[Contratistas] {task_count} tarea(s) actualizadas hoy" if task_count > 0 else "[Contratistas] Sin cambios hoy"
    msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
            msg["From"] = EMAIL_FROM
                msg["To"] = EMAIL_TO
                    msg.attach(MIMEText(body, "html"))

                        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                                server.login(EMAIL_FROM, EMAIL_PASSWORD)
                                        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
                                            print(f"Email enviado: {subject}")

                                            if __name__ == "__main__":
                                                print("Revisando tareas del espacio Contratistas...")
                                                    updated = check_updates()
                                                        print(f"Tareas actualizadas en las ultimas 24hs: {len(updated)}")
                                                            body = build_email_body(updated)
                                                                send_email(body, len(updated))
                                                                
