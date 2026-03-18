# utils/notifier.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger("notifier")


def send_notification(session_id: str, state: dict):
    """
    Sends an email notification when someone downloads their report.
    Uses Gmail SMTP with App Password.
    """

    # ── Read config from .env ────────────────────────────────────
    sender_email    = os.getenv("NOTIFY_EMAIL")
    sender_password = os.getenv("NOTIFY_PASSWORD")
    receiver_email  = os.getenv("NOTIFY_TO", sender_email)

    if not sender_email or not sender_password:
        logger.warning("Email notifications not configured — skipping")
        return

    # ── Build email content ──────────────────────────────────────
    scores      = state.get("scores", [])
    company     = state.get("company_name", "Unknown")
    total_q     = len(scores)
    avg         = round(sum(s.get("overall", 0) for s in scores) / total_q, 1) if total_q else 0
    pct         = round(avg * 10)
    avg_s       = round(sum(s.get("S", 0) for s in scores) / total_q, 1) if total_q else 0
    avg_t       = round(sum(s.get("T", 0) for s in scores) / total_q, 1) if total_q else 0
    avg_a       = round(sum(s.get("A", 0) for s in scores) / total_q, 1) if total_q else 0
    avg_r       = round(sum(s.get("R", 0) for s in scores) / total_q, 1) if total_q else 0
    timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    verdict = (
        "🟢 Strong — Ready to interview" if pct >= 80 else
        "🟡 Good — Minor gaps to address" if pct >= 65 else
        "🟠 Fair — Needs more preparation" if pct >= 50 else
        "🔴 Needs work — Focused study required"
    )

    # ── Plain text body ──────────────────────────────────────────
    text_body = f"""
InterviewCopilot AI — Report Downloaded
========================================

Session ID  : {session_id}
Company     : {company}
Timestamp   : {timestamp}
Questions   : {total_q}

Overall Score : {avg}/10  ({pct}%)
Readiness     : {verdict}

STAR Breakdown:
  Situation  : {avg_s}/10
  Task       : {avg_t}/10
  Action     : {avg_a}/10
  Result     : {avg_r}/10

Question Scores:
{chr(10).join(f'  Q{i+1}: {s.get("overall",0)}/10  ({s.get("question_type","").replace("_"," ")})' for i,s in enumerate(scores))}

========================================
InterviewCopilot AI Notification System
"""

    # ── HTML body ────────────────────────────────────────────────
    score_rows = "".join(
        f"""<tr>
            <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;color:#374151;">
                Q{i+1} <span style="font-size:11px;color:#9ca3af;text-transform:uppercase">
                {s.get('question_type','').replace('_',' ')}</span>
            </td>
            <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;
                font-weight:700;color:{'#10b981' if s.get('overall',0)>=7 else '#f59e0b' if s.get('overall',0)>=5 else '#ef4444'}">
                {s.get('overall',0)}/10
            </td>
        </tr>"""
        for i, s in enumerate(scores)
    )

    bar_color = "#10b981" if pct >= 80 else "#f59e0b" if pct >= 65 else "#f97316" if pct >= 50 else "#ef4444"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#f9fafb; margin:0; padding:0; }}
  .wrap {{ max-width:560px; margin:32px auto; background:#fff; border-radius:16px;
           overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.08); }}
  .header {{ background:linear-gradient(135deg,#667eea,#764ba2); padding:32px 36px; text-align:center; }}
  .header h1 {{ color:#fff; font-size:22px; margin:0 0 4px; font-weight:800; }}
  .header p {{ color:rgba(255,255,255,0.75); font-size:14px; margin:0; }}
  .body {{ padding:28px 36px; }}
  .score-big {{ text-align:center; padding:24px; background:#f5f3ff;
                border-radius:12px; margin-bottom:24px; }}
  .score-big .pct {{ font-size:56px; font-weight:800; color:#667eea; line-height:1; }}
  .score-big .label {{ font-size:12px; text-transform:uppercase; letter-spacing:0.08em;
                       color:#9ca3af; margin-top:4px; }}
  .score-big .verdict {{ font-size:15px; color:#374151; margin-top:8px; font-weight:500; }}
  .meta-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:24px; }}
  .meta-box {{ background:#fafafa; border:1px solid #e5e7eb; border-radius:10px; padding:14px 16px; }}
  .meta-box .val {{ font-size:18px; font-weight:800; color:#1f2937; }}
  .meta-box .lbl {{ font-size:11px; text-transform:uppercase; letter-spacing:0.07em; color:#9ca3af; margin-top:2px; }}
  .star-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:24px; }}
  .star-box {{ background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px;
               padding:12px 8px; text-align:center; }}
  .star-box .val {{ font-size:20px; font-weight:800; color:#059669; }}
  .star-box .lbl {{ font-size:10px; text-transform:uppercase; letter-spacing:0.06em; color:#6b7280; }}
  .prog-bar {{ background:#e5e7eb; border-radius:100px; height:8px; margin:8px 0 20px; overflow:hidden; }}
  .prog-fill {{ height:100%; border-radius:100px; background:{bar_color}; width:{pct}%; }}
  table {{ width:100%; border-collapse:collapse; }}
  .footer {{ background:#f9fafb; border-top:1px solid #e5e7eb; padding:16px 36px;
             text-align:center; font-size:12px; color:#9ca3af; }}
  .section-title {{ font-size:11px; font-weight:700; text-transform:uppercase;
                    letter-spacing:0.1em; color:#9ca3af; margin-bottom:12px; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>🎯 InterviewCopilot AI</h1>
    <p>A user just downloaded their report</p>
  </div>
  <div class="body">
    <div class="score-big">
      <div class="pct">{pct}%</div>
      <div class="label">Overall Readiness Score</div>
      <div class="prog-bar"><div class="prog-fill"></div></div>
      <div class="verdict">{verdict}</div>
    </div>

    <div class="meta-grid">
      <div class="meta-box">
        <div class="val">{company}</div>
        <div class="lbl">Target Company</div>
      </div>
      <div class="meta-box">
        <div class="val">{session_id}</div>
        <div class="lbl">Session ID</div>
      </div>
      <div class="meta-box">
        <div class="val">{avg}/10</div>
        <div class="lbl">Average Score</div>
      </div>
      <div class="meta-box">
        <div class="val">{total_q}</div>
        <div class="lbl">Questions Answered</div>
      </div>
    </div>

    <div class="section-title">STAR Breakdown</div>
    <div class="star-grid">
      <div class="star-box"><div class="val">{avg_s}</div><div class="lbl">Situation</div></div>
      <div class="star-box"><div class="val">{avg_t}</div><div class="lbl">Task</div></div>
      <div class="star-box"><div class="val">{avg_a}</div><div class="lbl">Action</div></div>
      <div class="star-box"><div class="val">{avg_r}</div><div class="lbl">Result</div></div>
    </div>

    <div class="section-title">Question Breakdown</div>
    <table>
      <tbody>{score_rows}</tbody>
    </table>

    <p style="font-size:12px;color:#9ca3af;margin-top:20px">
      📅 {timestamp}
    </p>
  </div>
  <div class="footer">InterviewCopilot AI — Notification System</div>
</div>
</body>
</html>
"""

    # ── Send via Gmail SMTP ──────────────────────────────────────
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎯 InterviewCopilot — Report Downloaded | {company} | {pct}%"
        msg["From"]    = sender_email
        msg["To"]      = receiver_email

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())

        logger.info(f"Notification sent → {receiver_email} | Session: {session_id} | Score: {pct}%")

    except smtplib.SMTPAuthenticationError:
        logger.error("Gmail authentication failed — check NOTIFY_EMAIL and NOTIFY_PASSWORD in .env")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
    except Exception as e:
        logger.error(f"Notification failed: {type(e).__name__}: {e}")