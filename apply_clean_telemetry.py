import os, re, glob, sqlite3

# 1. DATABASE ENSURE
conn = sqlite3.connect("portal.db")
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS feedbacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operator_name TEXT,
        rating INTEGER DEFAULT 5,
        comment TEXT,
        reward_days INTEGER DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active'
    )
""")
conn.commit()
conn.close()

# 2. BACKEND API SYNC (server/app.py)
app_path = r"server\app.py"
if os.path.exists(app_path):
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    code = re.sub(r'@app\.(?:get|post)\(["\']/api/feedback(?:/list|/submit)?[\s\S]*?(?=(@app|\Z))', '', code)

    clean_api = """
@app.get("/api/feedback/list")
async def get_feedback_live_list():
    try:
        conn = sqlite3.connect("portal.db")
        cur = conn.cursor()
        cur.execute("SELECT id, operator_name, rating, comment, reward_days, created_at FROM feedbacks ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        items = []
        for r in rows:
            items.append({
                "id": r[0],
                "name": r[1] or "Verified Operator",
                "rating": int(r[2] or 5),
                "comment": r[3] or "",
                "reward_days": int(r[4] or (r[2] or 5)),
                "date": str(r[5])
            })
        return {"success": True, "feedbacks": items, "count": len(items)}
    except Exception as e:
        return {"success": False, "feedbacks": [], "count": 0, "error": str(e)}

@app.post("/api/feedback/submit")
@app.post("/api/feedback")
async def store_feedback_live(request: Request):
    try:
        data = await request.json()
        name = (data.get("name") or data.get("operator_name") or "Verified Operator").strip()
        comment = (data.get("comment") or "").strip()
        rating = int(data.get("rating") or 5)
        rating = max(1, min(5, rating))
        reward_days = rating

        if not comment:
            return {"success": False, "error": "Feedback description required"}

        conn = sqlite3.connect("portal.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO feedbacks (operator_name, rating, comment, reward_days, status) VALUES (?, ?, ?, ?, 'active')",
            (name, rating, comment, reward_days)
        )
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM feedbacks")
        total = cur.fetchone()[0]
        conn.close()

        return {
            "success": True,
            "new_count": total,
            "reward_days": reward_days,
            "message": f"Verified! +{reward_days} extra access days awarded."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
"""
    code = code.strip() + "\n" + clean_api
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(code)

# 3. REAL TELEMETRY PLOT & FEEDBACK ENGINE (No fake elements)
clean_plot_engine = """
<!-- ================= COMPLETE REAL TELEMETRY & FEEDBACK MATRIX ================= -->
<div id="GARUDA_VERIFIED_TELEMETRY_SUITE" style="max-width: 960px; margin: 50px auto 30px; padding: 0 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; position: relative; z-index: 50;">
  <div style="background: rgba(13, 17, 28, 0.94); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.8), 0 0 25px rgba(56, 189, 248, 0.08); padding: 30px 24px; backdrop-filter: blur(16px);">

    <!-- TOP HEADER -->
    <div style="display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 20px; margin-bottom: 24px;">
      <div>
        <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
          Live Telemetry Matrix
        </div>
        <h2 style="font-size: 24px; font-weight: 800; color: #f8fafc; margin: 0 0 4px 0;">Operator Ratings & Telemetry Plot</h2>
        <p style="font-size: 13px; color: #94a3b8; margin: 0;">Verified community impressions. Each review unlocks +1 to +5 days extra access keys.</p>
      </div>

      <button type="button" onclick="toggleSubmitDrawer()" style="background: linear-gradient(135deg, #0284c7, #2563eb); color: #fff; border: none; padding: 11px 20px; border-radius: 12px; font-size: 13px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 16px rgba(2, 132, 199, 0.35);">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        Rate & Review System
      </button>
    </div>

    <!-- MAIN TELEMETRY STATS & LIVE PERCENTAGE PLOT -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; background: rgba(18, 24, 38, 0.65); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 22px; margin-bottom: 24px;">
      
      <!-- SCORE & TOTAL -->
      <div style="display: flex; flex-direction: column; justify-content: center; border-right: 1px solid rgba(255, 255, 255, 0.06); padding-right: 20px;">
        <span style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase;">Average Platform Score</span>
        <div style="display: flex; align-items: baseline; gap: 10px; margin: 6px 0;">
          <span id="plotAverageScore" style="font-size: 46px; font-weight: 900; color: #38bdf8; line-height: 1;">0.0</span>
          <div style="display: flex; flex-direction: column;">
            <span style="color: #fbbf24; font-size: 15px; letter-spacing: 1px;">★★★★★</span>
            <span style="font-size: 11px; color: #64748b; font-weight: 600;">MAX 5.0 RATING</span>
          </div>
        </div>
        <div style="font-size: 13px; color: #e2e8f0; font-weight: 600;">
          Total Operators: <strong id="plotTotalOperatorsCount" style="color: #38bdf8; font-size: 15px;">0</strong>
        </div>
      </div>

      <!-- LIVE PLOT BARS -->
      <div style="display: flex; flex-direction: column; gap: 8px; justify-content: center;">
        <div style="display: flex; align-items: center; gap: 10px; font-size: 12px; color: #cbd5e1;">
          <span style="width: 25px; color: #fbbf24; font-weight: bold;">5★</span>
          <div style="flex: 1; height: 8px; background: rgba(255, 255, 255, 0.08); border-radius: 4px; overflow: hidden;">
            <div id="plotBar-5" style="width: 0%; height: 100%; background: #22c55e; transition: width 0.5s ease;"></div>
          </div>
          <span id="plotPct-5" style="width: 42px; text-align: right; color: #94a3b8; font-family: monospace; font-size: 11px;">0%</span>
        </div>

        <div style="display: flex; align-items: center; gap: 10px; font-size: 12px; color: #cbd5e1;">
          <span style="width: 25px; color: #fbbf24; font-weight: bold;">4★</span>
          <div style="flex: 1; height: 8px; background: rgba(255, 255, 255, 0.08); border-radius: 4px; overflow: hidden;">
            <div id="plotBar-4" style="width: 0%; height: 100%; background: #38bdf8; transition: width 0.5s ease;"></div>
          </div>
          <span id="plotPct-4" style="width: 42px; text-align: right; color: #94a3b8; font-family: monospace; font-size: 11px;">0%</span>
        </div>

        <div style="display: flex; align-items: center; gap: 10px; font-size: 12px; color: #cbd5e1;">
          <span style="width: 25px; color: #fbbf24; font-weight: bold;">3★</span>
          <div style="flex: 1; height: 8px; background: rgba(255, 255, 255, 0.08); border-radius: 4px; overflow: hidden;">
            <div id="plotBar-3" style="width: 0%; height: 100%; background: #facc15; transition: width 0.5s ease;"></div>
          </div>
          <span id="plotPct-3" style="width: 42px; text-align: right; color: #94a3b8; font-family: monospace; font-size: 11px;">0%</span>
        </div>

        <div style="display: flex; align-items: center; gap: 10px; font-size: 12px; color: #cbd5e1;">
          <span style="width: 25px; color: #fbbf24; font-weight: bold;">2★</span>
          <div style="flex: 1; height: 8px; background: rgba(255, 255, 255, 0.08); border-radius: 4px; overflow: hidden;">
            <div id="plotBar-2" style="width: 0%; height: 100%; background: #fb923c; transition: width 0.5s ease;"></div>
          </div>
          <span id="plotPct-2" style="width: 42px; text-align: right; color: #94a3b8; font-family: monospace; font-size: 11px;">0%</span>
        </div>

        <div style="display: flex; align-items: center; gap: 10px; font-size: 12px; color: #cbd5e1;">
          <span style="width: 25px; color: #fbbf24; font-weight: bold;">1★</span>
          <div style="flex: 1; height: 8px; background: rgba(255, 255, 255, 0.08); border-radius: 4px; overflow: hidden;">
            <div id="plotBar-1" style="width: 0%; height: 100%; background: #ef4444; transition: width 0.5s ease;"></div>
          </div>
          <span id="plotPct-1" style="width: 42px; text-align: right; color: #94a3b8; font-family: monospace; font-size: 11px;">0%</span>
        </div>
      </div>
    </div>

    <!-- SUBMISSION DRAWER -->
    <div id="plotSubmitBoxDrawer" style="display: none; background: rgba(18, 24, 38, 0.95); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 14px; padding: 20px; margin-bottom: 24px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <span style="color: #f8fafc; font-weight: 700; font-size: 14px;">Operator Telemetry Transmission</span>
        <span id="plotRewardBonusBadge" style="background: rgba(234, 179, 8, 0.15); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.35); padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">
          +5 DAYS BONUS
        </span>
      </div>

      <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
        <span style="font-size: 12px; color: #94a3b8;">Rating:</span>
        <div id="plotStarPicker" style="display: flex; gap: 6px; cursor: pointer; font-size: 24px; color: #facc15;">
          <span onclick="setPlotRating(1)">★</span>
          <span onclick="setPlotRating(2)">★</span>
          <span onclick="setPlotRating(3)">★</span>
          <span onclick="setPlotRating(4)">★</span>
          <span onclick="setPlotRating(5)">★</span>
        </div>
      </div>

      <input type="text" id="plotInputName" placeholder="Operator Name / Handle (Optional: Verified User)" style="width: 100%; box-sizing: border-box; background: rgba(10, 14, 23, 0.85); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 10px 12px; color: #fff; font-size: 13px; margin-bottom: 10px; outline: none;" />
      <textarea id="plotInputComment" rows="3" placeholder="Provide system performance feedback or experience..." style="width: 100%; box-sizing: border-box; background: rgba(10, 14, 23, 0.85); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 10px 12px; color: #fff; font-size: 13px; margin-bottom: 14px; outline: none; resize: vertical;"></textarea>

      <div style="display: flex; justify-content: flex-end; gap: 8px;">
        <button type="button" onclick="toggleSubmitDrawer()" style="background: rgba(255, 255, 255, 0.05); color: #94a3b8; border: 1px solid rgba(255, 255, 255, 0.1); padding: 8px 14px; border-radius: 8px; font-size: 12px; cursor: pointer;">Cancel</button>
        <button type="button" onclick="transmitVerifiedReview()" style="background: #16a34a; color: #fff; border: none; padding: 8px 20px; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer;">Submit & Claim Days</button>
      </div>
    </div>

    <!-- RECENT REVIEWS STREAM -->
    <div style="margin-bottom: 12px; color: #94a3b8; font-size: 12px; font-weight: 700; text-transform: uppercase;">Verified Operational Logs</div>
    <div id="plotCardsStreamContainer" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px;">
      <div style="grid-column: 1/-1; text-align: center; color: #64748b; font-size: 13px; padding: 20px;">Synchronizing telemetry...</div>
    </div>

  </div>
</div>

<script>
let currentActiveRating = 5;

function toggleSubmitDrawer() {
  const d = document.getElementById('plotSubmitBoxDrawer');
  if (d) d.style.display = (d.style.display === 'none' || d.style.display === '') ? 'block' : 'none';
}

function setPlotRating(val) {
  currentActiveRating = val;
  const stars = document.querySelectorAll('#plotStarPicker span');
  stars.forEach((s, idx) => {
    s.style.color = (idx < val) ? '#facc15' : '#334155';
  });
  const b = document.getElementById('plotRewardBonusBadge');
  if (b) b.innerText = `+${val} DAYS BONUS`;
}

async function transmitVerifiedReview() {
  const name = (document.getElementById('plotInputName').value || '').trim() || 'Verified Operator';
  const comment = (document.getElementById('plotInputComment').value || '').trim();

  if (!comment) {
    alert("Please write your feedback details.");
    return;
  }

  try {
    const res = await fetch('/api/feedback/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, comment: comment, rating: currentActiveRating })
    });
    const d = await res.json();
    if (d.success) {
      document.getElementById('plotInputComment').value = '';
      toggleSubmitDrawer();
      alert(`✅ Verified! +${currentActiveRating} access days awarded.`);
      await fetchAndRenderPlotMatrix();
    } else {
      alert(d.error || "Submission failed");
    }
  } catch(e) {
    alert("Network error. Make sure server is running.");
  }
}

async function fetchAndRenderPlotMatrix() {
  try {
    const res = await fetch('/api/feedback/list?t=' + Date.now());
    const data = await res.json();
    if (!data || !data.success) return;

    const list = data.feedbacks || [];
    const count = list.length;

    // Update Counter everywhere
    const counterEl = document.getElementById('plotTotalOperatorsCount');
    if (counterEl) counterEl.innerText = count;

    document.querySelectorAll('#masterFeedbackCountBadge, #humanFeedbackCounter, #fbTotalCount, [id*="feedbackCount"]').forEach(el => {
      el.innerText = count;
    });

    // Calculate Real Distribution & Average
    let counts = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
    let scoreSum = 0;

    list.forEach(item => {
      const r = Math.max(1, Math.min(5, parseInt(item.rating) || 5));
      counts[r] = (counts[r] || 0) + 1;
      scoreSum += r;
    });

    const avg = count > 0 ? (scoreSum / count).toFixed(1) : "0.0";
    const avgEl = document.getElementById('plotAverageScore');
    if (avgEl) avgEl.innerText = avg;

    for (let s = 1; s <= 5; s++) {
      const pct = count > 0 ? Math.round((counts[s] / count) * 100) : 0;
      const bar = document.getElementById(`plotBar-${s}`);
      const txt = document.getElementById(`plotPct-${s}`);
      if (bar) bar.style.width = pct + '%';
      if (txt) txt.innerText = pct + '%';
    }

    // Render Review Cards
    const container = document.getElementById('plotCardsStreamContainer');
    if (!container) return;

    if (list.length === 0) {
      container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: #64748b; font-size: 13px; padding: 24px; border: 1px dashed rgba(255,255,255,0.08); border-radius: 12px;">No operational logs recorded. Be the first to submit a review!</div>';
      return;
    }

    container.innerHTML = list.map(item => `
      <div style="background: rgba(18, 24, 38, 0.6); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <strong style="color: #38bdf8; font-size: 13px;">${item.name}</strong>
            <span style="color: #22c55e; font-size: 11px; font-weight: 700;">+${item.reward_days || item.rating}d</span>
          </div>
          <div style="color: #facc15; font-size: 11px; margin-bottom: 6px;">${'★'.repeat(item.rating)}${'☆'.repeat(5 - item.rating)}</div>
          <p style="color: #cbd5e1; font-size: 12px; line-height: 1.45; margin: 0 0 10px 0;">${item.comment}</p>
        </div>
        <div style="color: #64748b; font-size: 10px; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 6px;">
          ${(item.date || '').split(' ')[0]}
        </div>
      </div>
    `).join('');
  } catch(e) {
    console.error("Telemetry matrix fetch error:", e);
  }
}

document.addEventListener("DOMContentLoaded", fetchAndRenderPlotMatrix);
setTimeout(fetchAndRenderPlotMatrix, 300);
</script>
<!-- ================= END COMPLETE REAL TELEMETRY & FEEDBACK MATRIX ================= -->
"""

# 4. PURGE ALL FAKE TEXT AND INJECT CLEAN MATRIX
for path in glob.glob("**/*.html", recursive=True):
    if ".venv" in path or ".git" in path or "node_modules" in path:
        continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    # Step A: Delete exact fake floating 5* to 1* lines
    fake_patterns = [
        r'5\s*★\s*0%[\s\S]*?1\s*★\s*0%',
        r'<div[^>]*>[\s\S]*?5\s*★[\s\S]*?1\s*★[\s\S]*?</div>',
        r'<!-- ================= PREMIUM VERIFIED FEEDBACK SECTION ================= -->[\s\S]*?<!-- ================= END PREMIUM VERIFIED FEEDBACK SECTION ================= -->',
        r'<!-- REAL DYNAMIC RATING & PROGRESS BREAKDOWN HUD -->[\s\S]*?</script>',
        r'<!-- CLEAN COMMUNITY FEEDBACK SECTION -->[\s\S]*?</script>',
        r'<!-- ================= AUTHENTIC FEEDBACK SECTION ================= -->[\s\S]*?<!-- ================= END AUTHENTIC FEEDBACK SECTION ================= -->',
        r'<!-- ================= COMPLETE REAL TELEMETRY & FEEDBACK MATRIX ================= -->[\s\S]*?<!-- ================= END COMPLETE REAL TELEMETRY & FEEDBACK MATRIX ================= -->'
    ]

    for p in fake_patterns:
        html = re.sub(p, '', html)

    # Step B: Insert clean matrix neatly right before footer or body
    if "feedback" in html.lower() or "landing" in path.lower() or "dashboard" in path.lower():
        if "<footer" in html:
            html = html.replace("<footer", clean_plot_engine + "\n<footer", 1)
        elif "</body>" in html:
            html = html.replace("</body>", clean_plot_engine + "\n</body>", 1)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print("Telemetry & Plot matrix wired cleanly into:", path)

print("SYSTEM CLEANUP & LIVE TELEMETRY COMPLETE.")
