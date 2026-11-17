"""Inline the MVP into one HTML body for a claude.ai Artifact preview.

Usage: python3 tools/build_preview.py <out_dir>
The preview runs with an empty config (no backend): progress is kept in the
browser and nothing is sent anywhere.
"""
import pathlib, sys

mvp = pathlib.Path(__file__).resolve().parent.parent / "mvp"
out = pathlib.Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)

css = (mvp / "styles.css").read_text()
questions = (mvp / "questions.js").read_text() + "\n" + (mvp / "tags.js").read_text() + "\n" + (mvp / "esquemas.js").read_text()
app = (mvp / "app.js").read_text()
config = 'window.TESON_CONFIG = { supabaseUrl: "", supabaseAnonKey: "", contactEmail: "hola@tesonopos.es", demoAuth: true };'

page = f"""<title>Tesón MVP</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Inter:wght@400;500;600&display=swap">
<style>
{css}
</style>
<div id="app"></div>
<script>{config}</script>
<script>
{questions}
</script>
<script>
{app}
</script>
"""
(out / "teson-mvp.html").write_text(page)
for name in ["privacidad.html", "aviso-legal.html", "legal.css"]:
    (out / name).write_text((mvp / name).read_text())
print(out / "teson-mvp.html")
