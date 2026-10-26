import sys, os, re, ast, json, time, importlib, importlib.util, collections, traceback
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
SKIP = {".venv", "venv", "env", ".git", "node_modules", "__pycache__", "dist", "build",
        ".idea", ".vscode", "site-packages", ".mypy_cache", ".pytest_cache"}
STD = set(getattr(sys, "stdlib_module_names", ()))
TEXT_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json", ".md", ".txt",
            ".bat", ".ps1", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".spec"}
IGNORE_FILES = {"scan_all.py", "run_full_audit.py", "check_garuda.py", "audit_project.py",
                "fix_all.py"}
DYNAMIC_DIRS = {"actions", "plugins", "tests"}

FINDINGS, PASSES = [], []
T0 = time.time()


def F(sev, area, where, msg):
    FINDINGS.append((sev, area, where, msg))


def P(area, msg):
    PASSES.append((area, msg))


def ok(cond, area, label, detail="", sev="ERROR"):
    if cond:
        P(area, label)
    else:
        F(sev, area, label, detail or "check failed")
    return bool(cond)


def rd(p):
    try:
        return Path(p).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


# =============================================================== 1. STATIC
LOCAL_TOP = set()
for c in ROOT.iterdir():
    if c.name in SKIP:
        continue
    if c.is_dir():
        LOCAL_TOP.add(c.name)
    elif c.suffix == ".py":
        LOCAL_TOP.add(c.stem)

IMPORTED, THIRD = set(), set()
_top = {}


def resolve(parts, base):
    if not parts:
        return base
    b = base.joinpath(*parts)
    if b.with_name(b.name + ".py").is_file():
        return b.with_name(b.name + ".py")
    if (b / "__init__.py").is_file():
        return b / "__init__.py"
    if b.is_dir():
        return b
    return None


def top_names(path):
    if path in _top:
        return _top[path]
    names, star = set(), False
    try:
        tree = ast.parse(rd(path))
    except Exception:
        _top[path] = (None, True)
        return _top[path]

    def visit(stmts):
        nonlocal star
        for s in stmts:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(s.name)
            elif isinstance(s, ast.Assign):
                for t in s.targets:
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name):
                            names.add(n.id)
            elif isinstance(s, (ast.AnnAssign, ast.AugAssign)):
                if isinstance(s.target, ast.Name):
                    names.add(s.target.id)
            elif isinstance(s, ast.Import):
                for a in s.names:
                    names.add((a.asname or a.name).split(".")[0])
            elif isinstance(s, ast.ImportFrom):
                for a in s.names:
                    if a.name == "*":
                        star = True
                    else:
                        names.add(a.asname or a.name)
            elif isinstance(s, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                for fld in ("body", "orelse", "finalbody"):
                    visit(getattr(s, fld, []))
                for h in getattr(s, "handlers", []):
                    visit(h.body)

    visit(tree.body)
    if "__getattr__" in names:
        star = True
    _top[path] = (names, star)
    return _top[path]


def where(rel, line):
    return "%s:%s" % (rel, line) if line else rel


def check_names(target, names, rel, line, mod):
    if not names:
        return
    if target.is_file():
        tn, star = top_names(target)
        for n in names:
            if n == "*":
                continue
            sub = target.parent / (n + ".py")
            if target.name == "__init__.py" and (sub.is_file() or (target.parent / n).is_dir()):
                if sub.is_file():
                    IMPORTED.add(sub)
                continue
            if tn is None or star or n in tn:
                continue
            F("ERROR", "imports", where(rel, line),
              "cannot import '%s' from '%s' (not defined there)" % (n, mod))
    else:
        for n in names:
            sub = target / (n + ".py")
            if sub.is_file():
                IMPORTED.add(sub)
            elif not (target / n).is_dir():
                F("ERROR", "imports", where(rel, line), "'%s' not found in package '%s'" % (n, mod))


def check_import(p, rel, mod, names, level, line, seen):
    parts = [x for x in (mod or "").split(".") if x]
    if level:
        base = p.parent
        for _ in range(level - 1):
            base = base.parent
        t = resolve(parts, base)
        if t is None:
            F("ERROR", "imports", where(rel, line), "relative import '%s%s' not found" % ("." * level, mod or ""))
        else:
            IMPORTED.add(t)
            check_names(t, names, rel, line, mod or ".")
        return
    if not parts:
        return
    top = parts[0]
    if top in LOCAL_TOP:
        t = resolve(parts, ROOT)
        if t is None:
            F("ERROR", "imports", where(rel, line), "local module '%s' not found" % mod)
        else:
            IMPORTED.add(t)
            check_names(t, names, rel, line, mod)
    elif top in STD:
        return
    else:
        THIRD.add(top)
        nm = ".".join(parts[:2]) if top == "google" else top
        try:
            spec = importlib.util.find_spec(nm)
        except Exception:
            spec = None
        if spec is None and nm not in seen:
            seen.add(nm)
            F("WARN", "packages", where(rel, line), "package '%s' not installed" % nm)


def check_classes(tree, rel):
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}

    def defined(cls, seen=None):
        seen = seen if seen is not None else set()
        if cls.name in seen:
            return set()
        seen.add(cls.name)
        d = set()
        for s in cls.body:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                d.add(s.name)
            elif isinstance(s, ast.Assign):
                for t in s.targets:
                    if isinstance(t, ast.Name):
                        d.add(t.id)
        for n in ast.walk(cls):
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id == "self" and isinstance(n.ctx, (ast.Store, ast.Del))):
                d.add(n.attr)
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id in ("hasattr", "getattr", "setattr") and len(n.args) >= 2
                    and isinstance(n.args[0], ast.Name) and n.args[0].id == "self"
                    and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str)):
                d.add(n.args[1].value)
        for b in cls.bases:
            if isinstance(b, ast.Name) and b.id in classes:
                d |= defined(classes[b.id], seen)
        return d

    for cls in classes.values():
        d, rep = defined(cls), set()
        for n in ast.walk(cls):
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                    and n.value.id == "self" and isinstance(n.ctx, ast.Load)
                    and n.attr.startswith("_") and not n.attr.startswith("__")
                    and n.attr not in d and n.attr not in rep):
                rep.add(n.attr)
                F("WARN", "attribute-bugs", where(rel, n.lineno),
                  "%s reads self.%s but never sets it (AttributeError risk)" % (cls.name, n.attr))
        cnt = collections.Counter(s.name for s in cls.body
                                  if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)))
        for name, c in cnt.items():
            if c > 1:
                F("WARN", "duplicates", where(rel, cls.lineno),
                  "method %s.%s defined %d times" % (cls.name, name, c))
    top = collections.Counter(n.name for n in tree.body
                              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    for name, c in top.items():
        if c > 1:
            F("WARN", "duplicates", rel, "'%s' defined %d times at top level" % (name, c))


try:
    from pyflakes.checker import Checker as _Flakes
except Exception:
    _Flakes = None


def analyze_py(p, rel, src):
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        F("ERROR", "syntax", where(rel, e.lineno), "SyntaxError: %s" % e.msg)
        return
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                check_import(p, rel, a.name, None, 0, node.lineno, seen)
        elif isinstance(node, ast.ImportFrom):
            check_import(p, rel, node.module or "", [a.name for a in node.names],
                         node.level, node.lineno, seen)
    check_classes(tree, rel)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = [s for s in n.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
            decos = " ".join(ast.dump(d) for d in n.decorator_list)
            if (len(body) == 1 and isinstance(body[0], ast.Pass) and not n.name.startswith("__")
                    and "abstract" not in decos and "overload" not in decos):
                rets = n.returns is not None and not (
                    isinstance(n.returns, ast.Constant) and n.returns.value is None)
                if rets:
                    F("ERROR", "stubs", where(rel, n.lineno),
                      "%s() should return a value but its body is only 'pass'" % n.name)
    if _Flakes is not None:
        try:
            for m in _Flakes(tree, filename=rel).messages:
                if type(m).__name__ in ("UndefinedName", "UndefinedLocal"):
                    F("ERROR", "undefined-names", where(rel, m.lineno), m.message % m.message_args)
        except Exception:
            pass


SEC_RE = [
    re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"""(?i)\b(api[_-]?key|secret|passwd|password|token)\b\s*[:=]\s*["'][^"'\s]{8,}["']"""),
]
JARVIS = re.compile(r"j\.?a\.?r\.?v\.?i\.?s", re.I)


def json_secret_paths(obj, path=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            kp = path + "/" + str(k)
            if isinstance(v, str) and len(v.strip()) >= 8 and re.search(r"(?i)key|token|secret|passw", str(k)):
                out.append(kp)
            else:
                out += json_secret_paths(v, kp)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:50]):
            out += json_secret_paths(v, path + "[%d]" % i)
    return out


def static_scan():
    files = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = sorted(d for d in dn if d not in SKIP)
        for f in sorted(fn):
            files.append(Path(dp) / f)
    py = []
    jv_files, name_hits, sec_files = collections.OrderedDict(), [], []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        if JARVIS.search(p.name):
            name_hits.append(rel)
        ext = p.suffix.lower()
        if ext not in TEXT_EXT or p.name in IGNORE_FILES or p.stat().st_size > 2000000:
            continue
        src = rd(p)
        if ext == ".py":
            py.append((p, rel, src))
        n = 0
        for i, line in enumerate(src.splitlines(), 1):
            if JARVIS.search(line) and "http" not in line and "onrender" not in line:
                n += 1
            if ext != ".json" and any(rx.search(line) for rx in SEC_RE):
                sec_files.append("%s:%d" % (rel, i))
            if re.search(r"LicenseDecision\(\s*True", line):
                F("WARN", "licence", where(rel, i), "licence check hard-coded to allowed (bypass)")
        if n:
            jv_files[rel] = n
        if ext == ".json":
            try:
                hits = json_secret_paths(json.loads(src))
                if hits:
                    sec_files.append(rel + " (" + ", ".join(hits[:3]) + ")")
            except Exception as e:
                F("ERROR", "json", rel, "invalid JSON: %s" % str(e)[:70])
    for p, rel, src in py:
        analyze_py(p, rel, src)
    for p, rel, src in py:
        if (p not in IMPORTED and p.name not in ("main.py", "ui.py", "setup.py", "__init__.py")
                and not (set(p.relative_to(ROOT).parts[:-1]) & DYNAMIC_DIRS)
                and not p.name.startswith(("fix_", "package_", "apply_"))):
            F("INFO", "unused", rel, "never imported by another file")
    if jv_files:
        F("WARN", "branding", "%d files" % len(jv_files),
          "'Jarvis' still in %d lines: %s" % (sum(jv_files.values()),
                                               ", ".join("%s(%d)" % kv for kv in list(jv_files.items())[:25])))
    if name_hits:
        F("WARN", "branding", "file names", "names still contain jarvis: " + ", ".join(name_hits[:15]))
    else:
        P("branding", "no file names contain jarvis")
    if sec_files:
        F("WARN", "secrets", "%d places" % len(sec_files),
          "secrets stored in plain files (values hidden): " + "; ".join(sec_files[:10]))
    return files, py


print("[scan] static analysis ...")
FILES, PYFILES = static_scan()
ok(not any(f[1] == "syntax" for f in FINDINGS), "syntax", "every .py file parses (%d files)" % len(PYFILES))
if _Flakes is None:
    F("INFO", "tools", "pyflakes", "not installed - run: pip install pyflakes  (adds undefined-name checks)")

# =============================================================== 2. FEATURES
print("[scan] feature checklist ...")
ui_s, main_s = rd(ROOT / "ui.py"), rd(ROOT / "main.py")
for need, sev in (("main.py", "ERROR"), ("ui.py", "ERROR"), ("core/prompt.txt", "WARN"),
                  ("face.png", "WARN"), ("requirements.txt", "WARN"), ("server/app.py", "WARN")):
    ok((ROOT / need).exists(), "files", "exists: " + need, "missing: " + need, sev)
ok(sys.version_info >= (3, 11), "python", "Python 3.11+", "Python %d.%d is too old for main.py" % sys.version_info[:2])
m = re.search(r"def _build_quick_drawer\(self\)[^\n]*\n(.*?)(?=\n    def )", ui_s, re.S)
ok(bool(m) and len(m.group(1)) > 200, "ui", "gear drawer is built (not 'pass')",
   "_build_quick_drawer is empty: gear button will crash")
ok(len(re.findall(r"^class SelectableBox\(", ui_s, re.M)) == 1, "ui", "SelectableBox defined once", "", "WARN")
ok("ov.done" not in ui_s and "setup_completed.connect" in ui_s, "ui", "setup form signal wired",
   "setup overlay signal 'done' does not exist")
ok("user_profile.json" in ui_s or "api_keys.json" in ui_s, "ui", "setup form saves config files",
   "setup save may not write the config main.py reads", "WARN")
ok("FIRST-RUN SETUP TRIGGER" not in ui_s, "ui", "no duplicate first-run overlay", "duplicate setup overlay still present", "WARN")
ok("BY SURAJ" in ui_s, "ui", "title keeps 'BY SURAJ'", "", "WARN")
ok("verify_developer_access(text)" in main_s and "_DEV_PROMPT" in main_s, "identity",
   "developer protocol wired in main.py", "Mahadev / who-are-you protocol not hooked in")
ok("_send_first_welcome" in main_s, "identity", "welcome-after-setup present", "", "WARN")
ok("@app.post" not in main_s and "@app.get" not in main_s, "main", "no stray FastAPI routes in main.py",
   "main.py still has @app routes (NameError)")
mm = re.search(r"^LIVE_MODEL\s*=\s*(.+)$", main_s, re.M)
P("model", "LIVE_MODEL line: " + (mm.group(1)[:60] if mm else "not found"))
app_s = rd(ROOT / "server" / "app.py")
if app_s:
    ok("portal_routes" in app_s, "server", "server/app.py includes portal_routes",
       "add: from server.portal_routes import router as portal_router ; app.include_router(portal_router)", "WARN")
for fname, field in (("api_keys.json", "gemini_api_key"), ("user_config.json", "api_key"),
                     ("user_profile.json", "gemini_api_key")):
    f = ROOT / "config" / fname
    if not f.exists():
        F("INFO", "config", "config/" + fname, "missing (normal before first setup)")
        continue
    try:
        d = json.loads(rd(f))
        P("config", "config/%s valid; keys=%s; %s=%s" % (fname, sorted(d)[:6], field,
                                                         "set" if str(d.get(field, "")).strip() else "EMPTY"))
    except Exception as e:
        F("ERROR", "config", "config/" + fname, "invalid JSON: %s" % e)
req = ROOT / "requirements.txt"
if req.exists():
    have = set()
    for ln in rd(req).splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            have.add(re.split(r"[=<>~\[; ]", ln)[0].lower().replace("-", "_"))
    alias = {"cv2": "opencv_python", "PIL": "pillow", "google": "google_genai", "yaml": "pyyaml",
             "dotenv": "python_dotenv", "win32com": "pywin32", "pynvml": "nvidia_ml_py"}
    miss = [t for t in sorted(THIRD)
            if not any(c in have or any(h.startswith(c) for h in have)
                       for c in (t.lower(), alias.get(t, t).lower()))]
    if miss:
        F("WARN", "requirements", "requirements.txt", "imported but not listed: " + ", ".join(miss))
    else:
        P("requirements", "requirements.txt covers all imports")

# =============================================================== 3. RUNTIME
print("[scan] runtime tests (packages, modules, identity, window) ...")
for mod, need in (("PyQt6", 1), ("psutil", 1), ("sounddevice", 1), ("numpy", 1), ("google.genai", 1),
                  ("qrcode", 0), ("fastapi", 0), ("uvicorn", 0), ("cryptography", 0), ("cv2", 0), ("PIL", 0)):
    try:
        importlib.import_module(mod)
        P("packages", mod)
    except Exception as e:
        F("ERROR" if need else "WARN", "packages", mod, "cannot import (%s) -> pip install" % type(e).__name__)
for mod, need in (("core.avatar", 1), ("core.audio_devices", 1), ("core.hotkey", 0), ("core.viseme", 1),
                  ("core.echo", 1), ("core.wake_word", 0), ("core.confirm", 1), ("core.license", 0),
                  ("core.gemini", 1), ("core.plugin_loader", 1), ("core.action_loader", 1),
                  ("memory.config_manager", 1), ("memory.memory_manager", 1), ("dashboard.server", 0)):
    try:
        importlib.import_module(mod)
        P("modules", mod)
    except Exception as e:
        F("ERROR" if need else "WARN", "modules", mod, "%s: %s" % (type(e).__name__, str(e)[:110]))
try:
    from core.action_loader import discover_actions
    from core.plugin_loader import discover_plugins
    reg = discover_actions(actions_dir=ROOT / "actions", reserved_names=set(), logger=lambda x: None)
    P("tools", "%d action tools discovered" % len(reg.names()))
    preg = discover_plugins(plugins_dir=ROOT / "plugins", core_tool_names=set(),
                            logger=lambda x: None, notify=lambda x: None)
    for pl in preg.list_for_ui():
        if not pl.get("valid", True):
            F("WARN", "plugins", str(pl.get("file")), "broken plugin: %s" % str(pl.get("error"))[:100])
        else:
            P("plugins", str(pl.get("name")))
except Exception as e:
    F("WARN", "tools", "discovery", "%s: %s" % (type(e).__name__, str(e)[:120]))

try:
    import main as gmain

    class _UI:
        muted = False

        def write_log(self, m):
            pass

        def __getattr__(self, n):
            return lambda *a, **k: None

    g = gmain.GARUDALive.__new__(gmain.GARUDALive)
    g.ui, g._asst_name, g.is_developer_mode = _UI(), "GARUDA", False
    cases = [("tum kaun ho", "Main GARUDA hoon"), ("developer kaun hai", "Suraj Kumar Mohanty"),
             ("main tumhara developer hoon", "Pranam Sir"), ("galat123", "Access Denied"),
             ("main tumhara developer hoon", "Pranam Sir"), ("mahadev", "Har Har Mahadev"),
             ("\u092e\u0939\u093e\u0926\u0947\u0935", "Har Har Mahadev"), ("mausam kaisa hai", None)]
    for q, expect in cases:
        r = g.verify_developer_access(q)
        good = (r is None) if expect is None else (r is not None and expect in r)
        ok(good, "identity", "reply for '%s'" % q.encode("unicode_escape").decode(), "got: %s" % str(r)[:60])
    ok(g.is_developer_mode is True, "identity", "password unlocks developer mode", "is_developer_mode stayed False")
    if mm:
        P("model", "main.LIVE_MODEL = " + str(gmain.LIVE_MODEL))
except Exception as e:
    F("ERROR", "identity", "main.py import", "%s: %s" % (type(e).__name__, str(e)[:150]))

try:
    from PyQt6.QtWidgets import QApplication, QPushButton
    import ui as gui
    app = QApplication.instance() or QApplication([])
    w = gui.MainWindow("face.png")
    app.processEvents()
    P("window", "main window builds")
    ok(getattr(w, "_quick_drawer", None) is not None, "window", "gear drawer object exists",
       "_quick_drawer is None -> gear click crashes")
    w._toggle_drawer(True)
    app.processEvents()
    btns = [b.text() for b in w._quick_drawer.findChildren(QPushButton)]
    ok(len(btns) >= 8, "window", "gear opens drawer with %d buttons" % len(btns), "drawer has %d buttons" % len(btns))
    for meth in ("_open_customize", "_open_operator_profile", "_open_audio_devices", "_open_memory_panel",
                 "_open_plugin_manager", "_open_plugin_settings", "_open_remote", "_toggle_autostart",
                 "_toggle_brief", "_toggle_wake_word", "_toggle_ptt", "_toggle_hud_style",
                 "_create_desktop_shortcut"):
        ok(hasattr(w, meth), "window", "button handler " + meth, "handler missing")
    ov = gui.SetupOverlay(w.centralWidget())
    ov._on_submit()
    ok("API" in ov.err_lbl.text(), "window", "setup form rejects empty input", ov.err_lbl.text()[:50])
except Exception as e:
    F("ERROR", "window", "gui test", "%s: %s" % (type(e).__name__, str(e)[:160]))
    FINDINGS.append(("INFO", "window", "traceback", traceback.format_exc()[-300:].replace("\n", " | ")))

# live model name check against the real API (key never printed)
try:
    key = ""
    for fname, field in (("api_keys.json", "gemini_api_key"), ("user_config.json", "api_key")):
        try:
            key = json.loads(rd(ROOT / "config" / fname)).get(field, "") or key
        except Exception:
            pass
    key = key or os.getenv("GEMINI_API_KEY", "")
    if key:
        from google import genai
        client = genai.Client(api_key=key)
        names = [mo.name for mo in client.models.list()]
        live = [n for n in names if "live" in n or "native-audio" in n]
        cur = str(getattr(gmain, "LIVE_MODEL", "")) if "gmain" in globals() else ""
        ok(cur in names or cur.replace("models/", "") in [n.replace("models/", "") for n in names],
           "model", "configured live model exists on Google", "'%s' not in your model list" % cur)
        P("model", "live-capable models: " + ", ".join(live[:8]))
    else:
        F("INFO", "model", "api key", "no key found, model name not verified")
except Exception as e:
    F("WARN", "model", "api check", "%s: %s" % (type(e).__name__, str(e)[:110]))

# =============================================================== REPORT
order = {"ERROR": 0, "WARN": 1, "INFO": 2}
cnt = collections.Counter(f[0] for f in FINDINGS)
lines = ["GARUDA FULL SCAN  %s  python %s  files %d  (%.1fs)" % (
    time.strftime("%Y-%m-%d %H:%M"), sys.version.split()[0], len(FILES), time.time() - T0),
    "RESULT: %d passed | ERROR %d | WARN %d | INFO %d" % (len(PASSES), cnt["ERROR"], cnt["WARN"], cnt["INFO"]), ""]
for sev in ("ERROR", "WARN", "INFO"):
    group = [f for f in FINDINGS if f[0] == sev]
    if not group:
        continue
    lines.append("--- %s (%d) ---" % (sev, len(group)))
    for _, area, wh, msg in sorted(group, key=lambda x: (x[1], x[2]))[:120]:
        lines.append("[%s] %s - %s" % (area, wh, msg))
    lines.append("")
lines.append("--- PASSED (%d) ---" % len(PASSES))
by = collections.OrderedDict()
for area, msg in PASSES:
    by.setdefault(area, []).append(msg)
for area, msgs in by.items():
    lines.append("[%s] %s" % (area, "; ".join(msgs)[:300]))
text = "\n".join(lines)
for pth in (ROOT / "GARUDA_SCAN_REPORT.txt", ROOT.parent / (ROOT.name + "_SCAN_REPORT.txt")):
    try:
        pth.write_text(text, encoding="utf-8")
    except Exception:
        pass
print("\n" + "=" * 70 + "\nCOPY EVERYTHING BELOW THIS LINE AND SHARE IT\n" + "=" * 70)
print(text)
print("=" * 70)
print("full report saved: GARUDA_SCAN_REPORT.txt (and one copy outside the project folder)")
sys.stdout.flush()
os._exit(0)
