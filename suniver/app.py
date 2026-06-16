from flask import Flask, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "suniver-demo-ds517-usfx"

# ── Shared layout CSS ────────────────────────────────────────────────────────
_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',Tahoma,sans-serif; background:#f0f2f5; min-height:100vh; }

.topbar {
  background:#f5a01a; color:#fff;
  height:48px; padding:0 18px;
  display:flex; align-items:center; justify-content:space-between;
  position:fixed; top:0; left:0; right:0; z-index:200;
  box-shadow:0 2px 5px rgba(0,0,0,.2);
}
.topbar-left { display:flex; align-items:center; gap:14px; }
.topbar .hamburger { font-size:1.2rem; cursor:pointer; }
.topbar .brand { font-size:1.1rem; font-weight:700; letter-spacing:.3px; }
.topbar-right { display:flex; align-items:center; gap:20px; font-size:0.83rem; }
.topbar-right .carreras { cursor:pointer; opacity:.9; }

.layout { display:flex; margin-top:48px; min-height:calc(100vh - 48px); }

.sidebar {
  width:222px; background:#fff; flex-shrink:0;
  border-right:1px solid #e2e2e2;
  position:fixed; top:48px; bottom:0; overflow-y:auto; z-index:100;
}
.sidebar-profile {
  padding:14px 12px 12px; border-bottom:1px solid #eee;
  display:flex; gap:10px; align-items:flex-start;
}
.avatar {
  width:44px; height:44px; border-radius:50%;
  background:#ccc; display:flex; align-items:center; justify-content:center;
  font-size:1.5rem; flex-shrink:0; overflow:hidden;
}
.profile-info { font-size:0.77rem; }
.profile-name { font-weight:700; color:#333; margin-bottom:2px; }
.profile-carrera { color:#999; font-size:0.7rem; margin-bottom:5px; }
.logout-link { color:#e74c3c; text-decoration:none; font-size:0.71rem; }
.logout-link:hover { text-decoration:underline; }

.nav-label {
  font-size:0.62rem; color:#aaa; letter-spacing:.07em; font-weight:700;
  padding:12px 14px 4px; text-transform:uppercase;
}
.nav-list { list-style:none; }
.nav-link {
  display:flex; align-items:center; justify-content:space-between;
  padding:9px 14px; font-size:0.82rem; color:#444;
  text-decoration:none; cursor:pointer; transition:background .15s;
}
.nav-link:hover { background:#fff8ee; color:#f5a01a; }
.nav-link.active-parent { color:#f5a01a; background:#fff8ee; }
.nav-caret { color:#bbb; font-size:.85rem; }
.nav-sub { list-style:none; background:#fafafa; border-top:1px solid #f0f0f0; }
.sub-link {
  display:block; padding:7px 14px 7px 34px;
  font-size:0.79rem; color:#555; text-decoration:none;
  transition:color .15s;
}
.sub-link:hover { color:#f5a01a; }
.sub-link.active { color:#f5a01a; font-weight:600; }
.sub-link.off { color:#ccc; cursor:default; pointer-events:none; }

.main { margin-left:222px; flex:1; padding:22px 28px 40px; }

.breadcrumb {
  text-align:right; font-size:0.74rem; color:#aaa; margin-bottom:14px;
}
.breadcrumb .bc-active { color:#f5a01a; }

.page-h1 { font-size:1.3rem; font-weight:600; color:#333; margin-bottom:6px; }
.page-sub { font-size:0.85rem; color:#888; font-weight:600; margin-bottom:18px; letter-spacing:.03em; }

.card {
  background:#fff; border-radius:2px;
  box-shadow:0 1px 3px rgba(0,0,0,.09); margin-bottom:18px;
}
.card-header {
  border-top:3px solid #00bcd4; padding:10px 16px;
  font-size:0.88rem; font-weight:600; color:#444;
  display:flex; justify-content:space-between; align-items:center;
}
.card-close { color:#ccc; font-size:.8rem; cursor:pointer; }
.card-body { padding:16px 18px; }

.info-table { width:100%; border-collapse:collapse; font-size:0.84rem; }
.info-table tr { border-bottom:1px solid #f4f4f4; }
.info-table td { padding:9px 12px; }
.info-table td:first-child { font-weight:600; color:#555; width:36%; }
.info-table td:last-child { color:#222; }

.tabs { display:flex; margin-bottom:14px; }
.tab {
  padding:6px 20px; border:1px solid #ddd; background:#f7f7f7;
  font-size:0.79rem; color:#666; cursor:pointer;
}
.tab.active {
  background:#fff; border-bottom:2px solid #00bcd4;
  color:#00bcd4; font-weight:600;
}

.grade-wrap { overflow-x:auto; }
.grade-table { width:100%; border-collapse:collapse; font-size:0.74rem; white-space:nowrap; }
.grade-table th {
  background:#eef3f8; padding:7px 5px; text-align:center;
  color:#555; font-weight:600; border:1px solid #dde4ec; font-size:0.69rem;
}
.grade-table td {
  padding:8px 5px; text-align:center;
  border:1px solid #eee; color:#333;
}
.grade-table td.asig { text-align:left; padding-left:10px; white-space:normal; min-width:140px; }
.grade-table tr:hover td { background:#fffcf5; }
.gr { color:#e53935; font-weight:600; }
.gb { color:#1565c0; font-weight:600; }

.notes-box { font-size:0.72rem; color:#e53935; margin:10px 0 16px; line-height:1.8; }

.sea-section h3 { font-size:0.83rem; font-weight:700; color:#444; margin-bottom:10px; letter-spacing:.04em; }
.sea-table { border-collapse:collapse; font-size:0.77rem; }
.sea-table th { background:#eef3f8; padding:7px 16px; border:1px solid #dde; text-align:center; font-size:0.71rem; }
.sea-table td { padding:7px 16px; border:1px solid #eee; text-align:center; color:#333; }

.btn-print {
  display:block; width:100%; padding:13px; margin-top:16px;
  background:#5b9bd5; color:#fff; border:none; border-radius:2px;
  font-size:0.9rem; cursor:pointer; text-align:center; letter-spacing:.03em;
}

.suniver-footer {
  display:flex; justify-content:space-between; align-items:center;
  margin-top:22px; padding-top:16px; border-top:1px solid #eee;
}
.footer-links { display:flex; flex-direction:column; gap:4px; align-items:flex-end; }
.footer-links a { color:#aaa; text-decoration:none; font-size:0.71rem; }
.footer-links a:hover { color:#f5a01a; }

.demo-badge {
  position:fixed; bottom:12px; right:14px;
  background:rgba(0,0,0,.46); color:#fff; font-size:0.64rem;
  padding:3px 12px; border-radius:20px; pointer-events:none; z-index:300;
}

.home-grid { display:grid; grid-template-columns:1fr 340px; gap:18px; }
.cron-item { display:flex; gap:12px; align-items:flex-start; margin-bottom:14px; }
.cron-icon {
  width:40px; height:40px; background:#e8e8e8; border-radius:3px;
  display:flex; align-items:center; justify-content:center; font-size:0.68rem;
  color:#aaa; flex-shrink:0; text-align:center; line-height:1.3;
}
.cron-title { font-size:0.82rem; font-weight:600; color:#333; }
.cron-date { font-size:0.71rem; color:#888; margin-top:3px; line-height:1.6; }
"""

# ── USFX shield SVG (inline, reusable) ──────────────────────────────────────
_SHIELD_SVG = """<svg width="44" height="44" viewBox="0 0 52 52">
  <path d="M26 4 L46 13 L46 30 C46 40 37 47 26 49 C15 47 6 40 6 30 L6 13 Z"
        fill="#003366" stroke="#c8a800" stroke-width="2.5"/>
  <text x="26" y="22" text-anchor="middle" fill="#c8a800"
        font-size="5.5" font-family="serif" font-weight="bold">U.S.F.X.</text>
  <text x="26" y="32" text-anchor="middle" fill="#fff" font-size="4.5" font-family="serif">Chuquisaca</text>
  <text x="26" y="41" text-anchor="middle" fill="#fff" font-size="4" font-family="serif">Bolivia</text>
</svg>"""

# ── Sidebar (shared) ─────────────────────────────────────────────────────────
def _sidebar(active):
    li = lambda href, label, cls="": f'<li><a href="{href}" class="sub-link {cls}">{label}</a></li>'
    libreta_cls = "active" if active == "libreta" else ""
    return f"""
<div class="sidebar">
  <div class="sidebar-profile">
    <div class="avatar">&#128100;</div>
    <div class="profile-info">
      <div class="profile-name">Estudiante Demo</div>
      <div class="profile-carrera">ING. EN CIENCIAS DE LA COMPU</div>
      <a href="/logout" class="logout-link">&#10548; Cerrar sesi&oacute;n</a>
    </div>
  </div>
  <div class="nav-label">Navegaci&oacute;n Principal</div>
  <ul class="nav-list">
    <li><a href="#" class="nav-link">&#128193; Matr&iacute;culas <span class="nav-caret">&#8249;</span></a></li>
    <li><a href="#" class="nav-link">&#128197; Programaciones <span class="nav-caret">&#8249;</span></a></li>
    <li>
      <a href="#" class="nav-link active-parent">&#9998; Calificaciones <span class="nav-caret">&#8964;</span></a>
      <ul class="nav-sub">
        {li('#', '&#9675; Mi Kardex', 'off')}
        {li('/libreta', '&#9675; Mi Libreta', libreta_cls)}
        {li('#', '&#9675; Mi Cuaderno de Trabajo', 'off')}
      </ul>
    </li>
    <li><a href="#" class="nav-link">&#127760; Campus Virtual</a></li>
    <li><a href="#" class="nav-link">&#127885; Becas <span class="nav-caret">&#8249;</span></a></li>
    <li><a href="#" class="nav-link">&#128106; Rebaja de Hermanos</a></li>
    <li><a href="#" class="nav-link">&#128203; Tr&aacute;mites</a></li>
    <li><a href="#" class="nav-link">&#128214; Formularios</a></li>
    <li><a href="#" class="nav-link">&#128270; Scopus</a></li>
    <li><a href="#" class="nav-link">&#128203; Encuesta</a></li>
  </ul>
</div>"""


# ── LOGIN ────────────────────────────────────────────────────────────────────
LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Autenticarse - Suniver</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',Tahoma,sans-serif; background:#c8cfd8; min-height:100vh;
    display:flex; flex-direction:column; align-items:center; padding-top:56px; }
  .suniver-logo { font-size:2rem; font-weight:300; color:#2c3e50; margin-bottom:22px; letter-spacing:1px; }
  .suniver-logo strong { font-weight:700; }
  .card { background:#fff; border-radius:3px; padding:28px 30px 22px; width:320px;
    box-shadow:0 2px 10px rgba(0,0,0,.12); }
  .card-sub { text-align:center; color:#666; font-size:0.88rem; margin-bottom:18px; }
  .input-wrap { position:relative; margin-bottom:10px; }
  .input-wrap input { width:100%; padding:10px 36px 10px 12px; border:1px solid #ccc;
    border-radius:2px; font-size:0.9rem; outline:none; color:#333; transition:border-color .2s; }
  .input-wrap input:focus { border-color:#2980b9; }
  .input-wrap .ico { position:absolute; right:10px; top:50%; transform:translateY(-50%);
    color:#aaa; font-size:.9rem; }
  .btn-ingresar { width:100%; padding:11px; background:#2980b9; color:#fff; border:none;
    border-radius:2px; cursor:pointer; font-size:.95rem; margin-top:6px; transition:background .2s; }
  .btn-ingresar:hover { background:#3498db; }
  .forgot { display:block; text-align:center; color:#2980b9; font-size:.8rem; text-decoration:none; margin-top:14px; }
  .nota-red { color:#e74c3c; font-size:.76rem; text-align:center; margin-top:12px; line-height:1.55; }
  .logos { display:flex; justify-content:space-between; align-items:center; width:320px; margin-top:24px; padding:0 6px; }
  .demo-tag { position:fixed; bottom:14px; left:50%; transform:translateX(-50%);
    background:rgba(0,0,0,.48); color:#fff; font-size:.7rem;
    padding:4px 16px; border-radius:20px; letter-spacing:.04em; pointer-events:none; }
</style>
</head>
<body>
  <div class="suniver-logo"><strong>SUN</strong>iver</div>
  <div class="card">
    <p class="card-sub">Aut&eacute;ntiquese para acceder</p>
    <form method="POST" action="/login">
      <div class="input-wrap">
        <input type="text" name="ci" placeholder="Carnet de Identidad" autocomplete="off" required>
        <span class="ico">&#128100;</span>
      </div>
      <div class="input-wrap">
        <input type="password" name="password" placeholder="Contrase&ntilde;a" required>
        <span class="ico">&#128274;</span>
      </div>
      <button type="submit" class="btn-ingresar">Ingresar</button>
    </form>
    <a href="#" class="forgot">&iquest;Olvi&oacute; su contrase&ntilde;a?</a>
    <p class="nota-red">
      Nota: El primer ingreso a SUNIVER, la contrase&ntilde;a es la fecha de nacimiento.<br>
      Ej. 27/03/1624
    </p>
  </div>
  <div class="logos">
    <svg width="52" height="52" viewBox="0 0 52 52">
      <path d="M26 4 L46 13 L46 30 C46 40 37 47 26 49 C15 47 6 40 6 30 L6 13 Z"
            fill="#003366" stroke="#c8a800" stroke-width="2.5"/>
      <text x="26" y="22" text-anchor="middle" fill="#c8a800" font-size="5.5" font-family="serif" font-weight="bold">U.S.F.X.</text>
      <text x="26" y="32" text-anchor="middle" fill="#fff" font-size="4.5" font-family="serif">Chuquisaca</text>
      <text x="26" y="41" text-anchor="middle" fill="#fff" font-size="4" font-family="serif">Bolivia</text>
    </svg>
    <svg width="64" height="28" viewBox="0 0 64 28">
      <text x="2" y="20" font-family="sans-serif" font-size="13" font-weight="bold" fill="#1a5276">DTIC</text>
    </svg>
  </div>
  <div class="demo-tag">DEMO &mdash; Simulaci&#243;n DS5.17 &middot; USFX</div>
</body>
</html>"""


def _page(title, breadcrumb, content, active, ci):
    sidebar = _sidebar(active)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>{title} - Suniver</title>
<style>{_CSS}</style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-left">
      <span class="hamburger">&#9776;</span>
      <span class="brand">Suniver</span>
    </div>
    <div class="topbar-right">
      <span>&#128100; CI: <strong>{ci}</strong></span>
      <span class="carreras">&#10022; Carreras</span>
    </div>
  </div>
  <div class="layout">
    {sidebar}
    <div class="main">
      <div class="breadcrumb">{breadcrumb}</div>
      {content}
    </div>
  </div>
  <div class="demo-badge">DEMO &mdash; DS5.17 &middot; USFX</div>
</body>
</html>"""


# ── DASHBOARD ────────────────────────────────────────────────────────────────
def render_dashboard(ci):
    content = f"""
<div class="page-h1">Bienvenido a Suniver, Estudiante Demo</div>
<div class="page-sub">CARRERA DE ING. EN CIENCIAS DE LA COMPUTACI&Oacute;N</div>
<div class="home-grid">
  <div>
    <div class="card">
      <div class="card-header">Mis Mensajes <span class="card-close">&#8722; &times;</span></div>
      <div class="card-body" style="min-height:60px;"></div>
    </div>
  </div>
  <div>
    <div class="card">
      <div class="card-header">Cronograma Acad&eacute;mico <span class="card-close">&#8722; &times;</span></div>
      <div class="card-body">
        <div class="cron-item">
          <div class="cron-icon">IMG</div>
          <div>
            <div class="cron-title">Matriculaci&oacute;n</div>
            <div class="cron-date">Del 2026-01-02 00:00:00<br>al 2026-03-02 23:59:00</div>
          </div>
        </div>
        <div class="cron-item">
          <div class="cron-icon">IMG</div>
          <div>
            <div class="cron-title">Programaciones</div>
            <div class="cron-date">Del 2026-02-02 00:00:00<br>al 2026-04-02 12:00:00</div>
          </div>
        </div>
        <div class="cron-item">
          <div class="cron-icon">IMG</div>
          <div>
            <div class="cron-title">Calificaciones</div>
            <div class="cron-date">
              1er Par.: 2026-04-18 23:59:00<br>
              2do. Par.: 2026-06-05 23:59:00<br>
              Ex. Final: 2026-06-20 23:59:00<br>
              2da. Instancia: 2026-06-27 23:59:00
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>"""
    bc = 'Inicio &rsaquo; <span class="bc-active">ING. EN CIENCIAS DE LA COMPUTACI&Oacute;N</span>'
    return _page("Inicio", bc, content, "home", ci)


# ── LIBRETA ──────────────────────────────────────────────────────────────────
def render_libreta(ci):
    content = f"""
<div class="page-h1">Libreta</div>
<div class="card">
  <div class="card-header">Mis Mensajes <span class="card-close">&#8722; &times;</span></div>
  <div class="card-body" style="min-height:28px;"></div>
</div>
<div class="card">
  <div class="card-header">Datos del Universitario</div>
  <div class="card-body">
    <table class="info-table">
      <tr><td>Carnet Universitario</td><td>DEM-2026</td></tr>
      <tr><td>Carnet de Identidad</td><td>{ci}</td></tr>
      <tr><td>Universitario</td><td>Estudiante Demo &mdash; USFX</td></tr>
      <tr><td>Sistema</td><td>Semestralizado</td></tr>
    </table>
  </div>
</div>
<div class="card">
  <div class="card-header">Libreta Acad&eacute;mica</div>
  <div class="card-body">
    <div class="tabs"><div class="tab active">1/2026</div></div>
    <div class="grade-wrap">
      <table class="grade-table">
        <thead>
          <tr>
            <th rowspan="2">C&oacute;digo<br>Asignatura</th>
            <th rowspan="2">Asignatura</th>
            <th rowspan="2">Curso</th>
            <th rowspan="2">Grupo</th>
            <th rowspan="2">SEA</th>
            <th colspan="3">Parciales</th>
            <th rowspan="2">Nota<br>Parciales</th>
            <th rowspan="2">Pr&aacute;cticas</th>
            <th rowspan="2">Laboratorio</th>
            <th rowspan="2">Nota<br>Semifinal</th>
            <th rowspan="2">Ex.<br>Final</th>
            <th rowspan="2">Nota<br>Final</th>
            <th rowspan="2">Segunda<br>Inst.</th>
            <th colspan="3">Examen Invierno/Verano</th>
          </tr>
          <tr>
            <th>1ro</th><th>2do</th><th>3er</th>
            <th>1er Ex</th><th>2do Ex</th><th>Nota Final</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>SIS330</td>
            <td class="asig">DESARROLLO DE APLICACIONES INTELIGENTES</td>
            <td>7</td><td>1</td><td>A</td>
            <td class="gr">18</td><td class="gr">20</td><td>-</td>
            <td class="gr">19.0</td><td class="gr">8</td><td class="gr">22</td>
            <td class="gr">49.0</td><td class="gr">35</td><td class="gr">84</td>
            <td class="gr">0</td><td>-</td><td>-</td><td>-</td>
          </tr>
          <tr>
            <td>COM600</td>
            <td class="asig">MICRO SERVICIOS</td>
            <td>7</td><td>1</td><td>D</td>
            <td class="gr">40</td><td class="gr">42</td><td>-</td>
            <td class="gr">41.0</td><td class="gr">18</td><td class="gr">0</td>
            <td class="gr">59.0</td><td class="gr">28</td><td class="gr">87</td>
            <td class="gr">0</td><td>-</td><td>-</td><td>-</td>
          </tr>
          <tr>
            <td>COM480</td>
            <td class="asig">ROB&Oacute;TICA I</td>
            <td>7</td><td>1</td><td>G</td>
            <td class="gr">25</td><td class="gr">30</td><td>-</td>
            <td class="gr">27.5</td><td class="gr">15</td><td class="gr">0</td>
            <td class="gr">42.5</td><td class="gr">32</td><td class="gr">75</td>
            <td class="gr">0</td><td>-</td><td>-</td><td>-</td>
          </tr>
          <tr>
            <td>SIS254</td>
            <td class="asig">SEGURIDAD DE LA INFORMACI&Oacute;N</td>
            <td>7</td><td>1</td><td class="gb">I</td>
            <td class="gr">22</td><td class="gr">24</td><td>-</td>
            <td class="gr">23.0</td><td class="gr">9</td><td class="gr">20</td>
            <td class="gr">52.0</td><td class="gr">30</td><td class="gr">82</td>
            <td class="gr">0</td><td>-</td><td>-</td><td>-</td>
          </tr>
          <tr>
            <td>SIS325</td>
            <td class="asig">ADMINISTRACI&Oacute;N DE PROYECTOS DE SOFTWARE</td>
            <td>8</td><td>1</td><td>G</td>
            <td class="gr">30</td><td class="gr">28</td><td>-</td>
            <td class="gr">29.0</td><td class="gr">14</td><td class="gr">0</td>
            <td class="gr">43.0</td><td class="gr">34</td><td class="gr">77</td>
            <td class="gr">0</td><td>-</td><td>-</td><td>-</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="notes-box">
      *Las Calificaciones en ROJO estan pendientes de validaci&oacute;n por parte del docente y estan sujetas a modificaci&oacute;n<br>
      ** Las casillas con &ldquo;-&rdquo; no son tomadas en cuenta para las ponderaciones
    </div>
    <div class="sea-section">
      <h3>CODIGOS DEL SISTEMA DE EVALUACI&Oacute;N ACAD&Eacute;MICA (SEA)</h3>
      <table class="sea-table">
        <thead>
          <tr>
            <th>C&oacute;digo</th>
            <th>Prueba Parciales</th>
            <th>Prueba Pr&aacute;cticas</th>
            <th>Laboratorios</th>
            <th>Prueba Final</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>A</td><td>25</td><td>10</td><td>25</td><td>40</td></tr>
          <tr><td>D</td><td>50</td><td>20</td><td>0</td><td>30</td></tr>
          <tr><td>G</td><td>40</td><td>20</td><td>0</td><td>40</td></tr>
          <tr><td>I</td><td>30</td><td>10</td><td>25</td><td>35</td></tr>
        </tbody>
      </table>
    </div>
    <button class="btn-print">&#128424; Imprimir</button>
    <div class="suniver-footer">
      <div style="display:flex;gap:14px;align-items:center;">
        <svg width="40" height="40" viewBox="0 0 52 52">
          <path d="M26 4 L46 13 L46 30 C46 40 37 47 26 49 C15 47 6 40 6 30 L6 13 Z"
                fill="#003366" stroke="#c8a800" stroke-width="2.5"/>
          <text x="26" y="22" text-anchor="middle" fill="#c8a800" font-size="5.5" font-family="serif" font-weight="bold">U.S.F.X.</text>
          <text x="26" y="31" text-anchor="middle" fill="#fff" font-size="4" font-family="serif">Chuquisaca</text>
          <text x="26" y="40" text-anchor="middle" fill="#fff" font-size="3.8" font-family="serif">Bolivia</text>
        </svg>
        <svg width="80" height="32" viewBox="0 0 120 40">
          <text x="4" y="28" font-family="cursive" font-size="22" fill="#1a5276" font-style="italic">dtic</text>
          <text x="44" y="28" font-family="cursive" font-size="10" fill="#888">.usfx.info</text>
        </svg>
      </div>
      <div class="footer-links">
        <a href="#">&#9993; dtic.soporte@usfx.bo</a>
        <a href="#">&#128172; Canal de Telegram</a>
        <a href="#">&#128172; Grupo de Telegram</a>
      </div>
    </div>
  </div>
</div>"""
    bc = 'Inicio &rsaquo; ING. EN CIENCIAS DE LA COMPUTACI&Oacute;N &rsaquo; <span class="bc-active">Libreta</span>'
    return _page("Libreta", bc, content, "libreta", ci)


# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ci = request.form.get("ci", "").strip()
        if ci:
            session["ci"] = ci
            return redirect(url_for("dashboard"))
    return LOGIN_HTML


@app.route("/dashboard")
def dashboard():
    if "ci" not in session:
        return redirect(url_for("login"))
    return render_dashboard(session["ci"])


@app.route("/libreta")
def libreta():
    if "ci" not in session:
        return redirect(url_for("login"))
    return render_libreta(session["ci"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    print("[SUNIVER] Portal académico iniciando en puerto 7000...", flush=True)
    app.run(host="0.0.0.0", port=7000)
