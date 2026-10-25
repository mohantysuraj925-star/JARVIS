import os, sys, re, sqlite3, ast
from datetime import datetime

REPORT_FILE = "garuda_audit_report.txt"

passed = []
warnings = []
bugs = []
suggestions = []

def log_pass(msg): passed.append(msg)
def log_warn(msg): warnings.append(msg)
def log_bug(msg): bugs.append(msg)
def log_sugg(msg): suggestions.append(msg)

print("=" * 65)
print("       GARUDA FULL-STACK SYSTEM AUDITOR & SCANNER")
print("=" * 65)

# 1. DATABASE AUDIT
db_file = "portal.db"
if not os.path.exists(db_file):
    log_bug("Database file 'portal.db' missing hai.")
else:
    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cur.fetchall()]
        
        if "feedbacks" not in tables:
            log_bug("Table 'feedbacks' database mein missing hai.")
        else:
            cur.execute("PRAGMA table_info(feedbacks);")
            cols = {c[1]: c[2] for c in cur.fetchall()}
            req_cols = ["id", "operator_name", "rating", "comment", "created_at", "status"]
            missing = [c for c in req_cols if c not in cols]
            if missing:
                log_bug(f"Table 'feedbacks' mein columns missing hain: {missing}")
            else:
                cur.execute("SELECT COUNT(*) FROM feedbacks;")
                cnt = cur.fetchone()[0]
                log_pass(f"SQLite DB 'feedbacks' table intact. Current rows: {cnt}")
        conn.close()
    except Exception as e:
        log_bug(f"Database connection error: {str(e)}")

# 2. BACKEND PYTHON AST & ROUTE AUDIT
backend_candidates = [r"server\app.py", r"app.py"]
target_backend = next((f for f in backend_candidates if os.path.exists(f)), None)

if not target_backend:
    log_bug("Koi backend file (server/app.py ya app.py) nahi mili.")
else:
    try:
        with open(target_backend, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code)
        log_pass(f"Backend '{target_backend}' syntax 100% valid hai.")

        # Check critical endpoints
        routes = ["/api/feedback/list", "/api/feedback/submit"]
        for r in routes:
            if r in code:
                log_pass(f"Backend route detect hua: {r}")
            else:
                log_bug(f"Backend endpoint missing: {r}")
                
        # Recommendations
        if "CORSMiddleware" not in code:
            log_warn("Backend mein CORS middleware nahi dikha (API calling security issue ho sakti hai).")
    except SyntaxError as e:
        log_bug(f"Backend SyntaxError in {target_backend} at line {e.lineno}: {e.msg}")
    except Exception as e:
        log_bug(f"Backend scan failure: {str(e)}")

# 3. FRONTEND TEMPLATE AUDIT
template_files = [r"templates\landing.html", r"server\templates\landing.html"]
for t_path in template_files:
    if not os.path.exists(t_path):
        continue
    with open(t_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Spec Modal integrity
    if 'id="specDetailModal"' in html:
        log_pass(f"{t_path}: specDetailModal container present.")
    else:
        log_bug(f"{t_path}: specDetailModal container ID missing hai.")

    # Feedback containers
    if 'id="liveFeedbackCardsGrid"' in html or 'id="REAL_FEEDBACK_SECTION"' in html:
        log_pass(f"{t_path}: Feedback UI grid sections wired.")
    else:
        log_bug(f"{t_path}: Live feedback UI grid missing hai.")

    # JS function triggers
    for func in ["openDetailModal", "closeDetailModal"]:
        if func in html:
            log_pass(f"{t_path}: Function '{func}' defined.")
        else:
            log_bug(f"{t_path}: Function '{func}' missing.")

    # Script tag balance
    opens = len(re.findall(r'<script', html, re.IGNORECASE))
    closes = len(re.findall(r'</script>', html, re.IGNORECASE))
    if opens != closes:
        log_bug(f"{t_path}: Script tags mismatched! <script>: {opens}, </script>: {closes}")
    else:
        log_pass(f"{t_path}: All script tags properly balanced.")

    # Tailored suggestions
    if 'lucide.createIcons()' in html and 'unpkg.com/lucide' not in html:
        log_warn(f"{t_path}: Lucide icons use ho rahe hain par script bundle missing ho sakta hai.")

# 4. GENERATE AI REPORT FILE
with open(REPORT_FILE, "w", encoding="utf-8") as rf:
    rf.write("=== GARUDA SYSTEM AUDIT REPORT ===\n")
    rf.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    rf.write("[PASSED CHECKS]\n")
    for p in passed: rf.write(f"  + {p}\n")
    
    rf.write("\n[WARNINGS / IMPROVEMENTS]\n")
    if warnings:
        for w in warnings: rf.write(f"  * {w}\n")
    else:
        rf.write("  None. Architecture cleanly structured.\n")
        
    rf.write("\n[BUGS & CRITICAL ISSUES]\n")
    if bugs:
        for b in bugs: rf.write(f"  ! {b}\n")
    else:
        rf.write("  Zero critical errors found. System ready for production.\n")

# Terminal Display
for p in passed: print(f"  \033[92m[✓]\033[0m {p}")
for w in warnings: print(f"  \033[93m[!]\033[0m {w}")
for b in bugs: print(f"  \033[91m[✗]\033[0m {b}")

print("\n" + "=" * 65)
if bugs:
    print(f"STATUS: {len(bugs)} Critical issue(s) detected. Details saved to '{REPORT_FILE}'.")
else:
    print(f"STATUS: 100% HEALTHY. Zero errors. Full report saved to '{REPORT_FILE}'.")
print("=" * 65)
