#!/usr/bin/env python3
"""
ЛР8: Coupling Matrix (матриця зв'язності) у вигляді HTML-сторінки.

Рядок = клас-клієнт, стовпець = клас-постачальник, "●" = клієнт напряму
використовує постачальника. Клас із найбільшим CBO підсвічується червоним.

Запуск (з кореня проєкту, після scripts/ck_metrics.py <мітка>):
    python3 scripts/coupling_matrix.py <мітка>
Результат: reports/lab8/coupling_<мітка>.html  (відкрий у браузері і зроби скріншот)
"""
import html
import json
import os
import sys


def load(label, folder="reports/lab8"):
    with open(os.path.join(folder, "ck_mood_%s.json" % label), encoding="utf-8") as f:
        return json.load(f)


def pick_axes(classes):
    """Рядки: класи, що залежать від інших проєктних класів. Стовпці: на кого вони залежать."""
    clients = [c for c in classes if c["CBO_project_classes"]]
    clients.sort(key=lambda c: (-c["CBO"], c["class"]))
    suppliers = sorted({s for c in clients for s in c["CBO_project_classes"]})
    return clients, suppliers


def cell(client, supplier, hot):
    if supplier in client["CBO_project_classes"]:
        cls = "dot hot" if hot else "dot"
        return '<td class="%s">●</td>' % cls
    return "<td></td>"


def row(client, suppliers, worst_cbo):
    hot = client["CBO"] == worst_cbo
    cells = "".join(cell(client, s, hot) for s in suppliers)
    ext = html.escape(", ".join(client["CBO_external"]) or "—")
    cls = ' class="worst"' if hot else ""
    return ("<tr%s><th class='rowh'>%s<br><small>%s</small></th>%s"
            "<td class='num'>%d</td><td class='ext'>%s</td></tr>"
            % (cls, html.escape(client["class"]), html.escape(client["file"]),
               cells, client["CBO"], ext))


CSS = """
body{font-family:-apple-system,Segoe UI,Arial,sans-serif;margin:24px;color:#222}
h1{font-size:20px} p{max-width:900px;color:#444}
table{border-collapse:collapse;font-size:12px}
th,td{border:1px solid #ccc;padding:4px 6px;text-align:center}
th.colh{height:130px;white-space:nowrap;vertical-align:bottom;padding:2px}
th.colh div{transform:rotate(-65deg);transform-origin:left bottom;width:24px;text-align:left}
th.rowh{text-align:left;background:#fafafa;white-space:nowrap}
.dot{color:#2b6cb0;font-size:15px} .dot.hot{color:#c53030}
tr.worst th.rowh{background:#fed7d7} tr.worst td{background:#fff5f5}
.num{font-weight:bold} .ext{text-align:left;color:#555;font-size:11px}
"""


def build(data):
    clients, suppliers = pick_axes(data["classes"])
    worst = max((c["CBO"] for c in data["classes"]), default=0)
    head = "".join("<th class='colh'><div>%s</div></th>" % html.escape(s) for s in suppliers)
    body = "".join(row(c, suppliers, worst) for c in clients)
    mood = data["mood"]
    return (
        "<!doctype html><meta charset='utf-8'><title>Coupling Matrix</title>"
        "<style>%s</style><h1>Coupling Matrix (%s): рядок залежить від стовпця</h1>"
        "<p>COF = %s%%, класів: %d, зв'язаних пар: %d. Червоний рядок: клас із найбільшим "
        "CBO (Coupling Between Objects). Стовпці CBO і «Зовнішні» додають залежності від "
        "бібліотек (db, func, date тощо).</p>"
        "<table><tr><th>клас-клієнт ↓ / постачальник →</th>%s"
        "<th>CBO</th><th>Зовнішні</th></tr>%s</table>"
        % (CSS, html.escape(data["label"]), mood["COF_percent"], mood["classes"],
           mood["coupled_pairs"], head, body))


def main():
    if len(sys.argv) < 2:
        sys.exit("Використання: python3 scripts/coupling_matrix.py <мітка>")
    label = sys.argv[1]
    out = os.path.join("reports/lab8", "coupling_%s.html" % label)
    with open(out, "w", encoding="utf-8") as f:
        f.write(build(load(label)))
    print("Збережено:", out)


if __name__ == "__main__":
    main()
