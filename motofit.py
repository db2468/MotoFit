const express = require("express");
const basicAuth = require("express-basic-auth");
const fs = require("fs");
const path = require("path");

const app = express();
app.use(express.urlencoded({ extended: true }));

const DATA_FILE = path.join(__dirname, "ideas.json");

// Passwort: 1243
const ADMIN_USER = "admin";
const ADMIN_PASS = "1243";

function loadIdeas() {
  try {
    const raw = fs.readFileSync(DATA_FILE, "utf8");
    const data = JSON.parse(raw);
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

function saveIdeas(ideas) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(ideas, null, 2), "utf8");
}

// ===== Public page: form =====
app.get("/", (req, res) => {
  res.type("html").send(`
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>3D-Druck Ideen</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; }
    h1 { margin: 0 0 12px; }
    p { margin: 0 0 20px; color: #444; }
    textarea { width: 100%; min-height: 120px; padding: 12px; font-size: 16px; }
    button { margin-top: 12px; padding: 10px 14px; font-size: 16px; cursor: pointer; }
    .note { margin-top: 18px; color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <h1>3D-Druck Idee eintragen</h1>
  <p>Schreib deine Idee rein und sende ab.</p>

  <form method="POST" action="/submit">
    <textarea name="idea" placeholder="z.B. Halterung für ... / Werkzeugbox ... / Scooter-Teil ..."></textarea>
    <br />
    <button type="submit">Absenden</button>
  </form>

  <div class="note">
    Admin-Ansicht: <code>/admin</code>
  </div>
</body>
</html>
  `);
});

app.post("/submit", (req, res) => {
  const idea = (req.body.idea || "").trim();
  if (!idea) {
    return res.status(400).type("html").send("Leeres Feld. Geh zurück und schreib was rein.");
  }

  const ideas = loadIdeas();
  ideas.unshift({
    idea,
    createdAt: new Date().toISOString(),
    ip: req.headers["x-forwarded-for"]?.toString().split(",")[0]?.trim() || req.socket.remoteAddress
  });
  saveIdeas(ideas);

  res.type("html").send(`
<!doctype html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gespeichert</title></head>
<body style="font-family:system-ui;max-width:720px;margin:40px auto;padding:0 16px;">
  <h2>Gespeichert.</h2>
  <p><a href="/">Zurück</a></p>
</body>
</html>
  `);
});

// ===== Admin page: protected list =====
app.use(
  "/admin",
  basicAuth({
    users: { [ADMIN_USER]: ADMIN_PASS },
    challenge: true, // Browser zeigt Login-Popup
    realm: "Admin",
  })
);

app.get("/admin", (req, res) => {
  const ideas = loadIdeas();

  const items = ideas
    .map((x, i) => {
      const dt = new Date(x.createdAt);
      const dateStr = isNaN(dt.getTime()) ? x.createdAt : dt.toLocaleString("de-DE");
      return `
        <li style="margin:14px 0; padding:12px; border:1px solid #ddd; border-radius:10px;">
          <div style="color:#666;font-size:13px;margin-bottom:8px;">
            #${ideas.length - i} • ${dateStr}
          </div>
          <div style="white-space:pre-wrap;">${escapeHtml(x.idea)}</div>
        </li>
      `;
    })
    .join("");

  res.type("html").send(`
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Admin – Ideen</title>
</head>
<body style="font-family:system-ui;max-width:900px;margin:40px auto;padding:0 16px;">
  <h1>Ideen (${ideas.length})</h1>
  <p style="color:#444;">Passwortgeschützt. Hier siehst du alle Einträge.</p>

  ${ideas.length ? `<ol style="padding-left:18px;">${items}</ol>` : `<p>Noch keine Ideen.</p>`}

  <hr style="margin:24px 0;" />
  <p><a href="/">Zur öffentlichen Seite</a></p>
</body>
</html>
  `);
});

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Running: http://localhost:${PORT}`);
  console.log(`Admin:   http://localhost:${PORT}/admin (user: admin, pass: ${ADMIN_PASS})`);
});
