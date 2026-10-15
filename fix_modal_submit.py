import re, os

paths = [r"templates\landing.html", r"server\templates\landing.html"]

for p in paths:
    if not os.path.exists(p):
        continue
    with open(p, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Textarea par safe ID ensure karna
    html = re.sub(
        r'<textarea([^>]*)>',
        r'<textarea id="feedbackCommentInput"\1>',
        html,
        count=1
    )

    # 2. submitRealFeedback function ko direct wire karna
    live_engine = """
<script id="SUBMIT_REAL_FEEDBACK_FIX">
let selectedFeedbackRating = 5;

function setRating(val) {
    selectedFeedbackRating = val;
    document.querySelectorAll('.star-btn, [onclick*="setRating"]').forEach((el, idx) => {
        el.style.color = (idx < val) ? '#fbbf24' : '#475569';
    });
}

async function fetchAndRenderFeedbacks() {
    try {
        const res = await fetch('/api/feedback/list');
        const data = await res.json();
        if (!data || !data.success) return;

        // Count badges sync
        document.querySelectorAll('#totalFeedbackCount, [id*="feedbackCount"]').forEach(el => {
            el.innerText = data.count || (data.feedbacks ? data.feedbacks.length : 0);
        });

        // Review list render
        const box = document.getElementById('liveFeedbackCardsGrid') || 
                    document.querySelector('#REAL_FEEDBACK_SECTION .grid') || 
                    document.querySelector('#reviewsContainer');
                    
        if (box) {
            const list = data.feedbacks || [];
            if (list.length === 0) {
                box.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:24px; color:#94a3b8; font-family:monospace; font-size:12px;">NO REVIEWS YET // BE THE FIRST OPERATOR TO SUBMIT</div>';
            } else {
                box.innerHTML = list.map(f => `
                    <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(168,85,247,0.3); border-radius:14px; padding:16px; display:flex; flex-direction:column; gap:6px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="color:#c084fc; font-weight:bold; font-size:12px; font-family:monospace;">${f.name || 'Verified Operator'}</span>
                            <span style="color:#eab308; font-size:11px;">${'★'.repeat(f.rating || 5)}${'☆'.repeat(5 - (f.rating || 5))}</span>
                        </div>
                        <p style="color:#e2e8f0; font-size:12px; line-height:1.5; margin:0;">${f.comment}</p>
                        <span style="color:#64748b; font-size:10px; font-family:monospace; margin-top:4px;">${(f.date || '').split(' ')[0]}</span>
                    </div>
                `).join('');
            }
        }
    } catch(err) {
        console.error("Fetch error:", err);
    }
}

async function submitRealFeedback() {
    const modal = document.getElementById('realFeedbackModal');
    const txt = modal ? (modal.querySelector('textarea') || document.getElementById('feedbackCommentInput')) : null;
    const nameInput = modal ? modal.querySelector('input[type="text"]') : null;

    const comment = txt ? txt.value.trim() : '';
    const name = nameInput && nameInput.value.trim() ? nameInput.value.trim() : 'Verified Operator';

    if (!comment) {
        alert("Please write your feedback message first.");
        return;
    }

    try {
        const res = await fetch('/api/feedback/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                comment: comment,
                rating: selectedFeedbackRating
            })
        });

        const result = await res.json();
        if (result.success) {
            if (txt) txt.value = '';
            if (modal) modal.style.display = 'none';
            await fetchAndRenderFeedbacks();
        } else {
            alert("Error: " + (result.error || "Submission failed"));
        }
    } catch(e) {
        alert("Server connection failed. Make sure the server is running.");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    fetchAndRenderFeedbacks();
});
</script>
"""

    html = re.sub(r'<script id="SUBMIT_REAL_FEEDBACK_FIX">[\s\S]*?</script>', '', html)
    if "</body>" in html:
        html = html.replace("</body>", live_engine + "\n</body>")
        with open(p, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Patched: {p}")

print("SUCCESS: submitRealFeedback function hooked directly.")
