# app/streamlit_app.py
import streamlit as st
import requests
import os

st.set_page_config(
    page_title="InterviewCopilot AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background: #0a0a0f !important;
    font-family: 'Inter', sans-serif;
    color: #ffffff;
}

.stApp > header { display: none !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* ══════════════════════════════════════
   HERO
══════════════════════════════════════ */
.hero {
    width: 100%;
    min-height: 300px;
    background: #0a0a0f;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 70px 24px 60px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute; inset: 0;
    background:
        radial-gradient(ellipse 80% 70% at 20% 60%, rgba(102,126,234,0.2) 0%, transparent 55%),
        radial-gradient(ellipse 60% 80% at 80% 30%, rgba(118,75,162,0.16) 0%, transparent 55%),
        radial-gradient(ellipse 50% 50% at 50% 90%, rgba(240,147,251,0.1) 0%, transparent 50%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(102,126,234,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(102,126,234,0.04) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
}
.hero-content { position: relative; z-index: 2; }
.hero-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(102,126,234,0.12);
    border: 1px solid rgba(102,126,234,0.35);
    border-radius: 50px; padding: 8px 22px;
    font-size: 11px; font-weight: 700;
    color: #a5b4fc; letter-spacing: 0.1em;
    text-transform: uppercase; margin-bottom: 28px;
}
.hero-badge-dot {
    width: 7px; height: 7px; background: #667eea;
    border-radius: 50%; animation: pulse 2s ease-in-out infinite;
    box-shadow: 0 0 8px rgba(102,126,234,0.8);
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.75)} }
@keyframes fadeUp { from{opacity:0;transform:translateY(28px)} to{opacity:1;transform:translateY(0)} }

.hero h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(40px, 6vw, 72px);
    font-weight: 800; line-height: 1.05; letter-spacing: -0.04em;
    background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 45%, #f0abfc 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 18px;
    animation: fadeUp 0.8s ease 0.15s both;
}
.hero-sub {
    font-size: 17px; font-weight: 400;
    color: rgba(255,255,255,0.5); -webkit-text-fill-color: rgba(255,255,255,0.5);
    max-width: 500px; margin: 0 auto 28px; line-height: 1.75;
    animation: fadeUp 0.8s ease 0.3s both;
}
.hero-tags {
    display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;
    animation: fadeUp 0.8s ease 0.45s both;
}
.hero-tag {
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 50px; padding: 5px 14px; font-size: 12px; font-weight: 500;
    color: rgba(255,255,255,0.5); -webkit-text-fill-color: rgba(255,255,255,0.5);
}

/* ══════════════════════════════════════
   LAYOUT
══════════════════════════════════════ */
.main-wrap { max-width: 1120px; margin: 0 auto; padding: 40px 28px 100px; }

/* ══════════════════════════════════════
   TABS
══════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 18px !important; padding: 6px !important;
    gap: 4px !important; margin-bottom: 36px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border: none !important;
    border-radius: 13px !important; color: rgba(255,255,255,0.38) !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important;
    font-weight: 600 !important; padding: 12px 28px !important;
    transition: all 0.25s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(102,126,234,0.07) !important;
    color: rgba(255,255,255,0.65) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: #fff !important; box-shadow: 0 4px 20px rgba(102,126,234,0.45) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; background: transparent !important; }

/* ══════════════════════════════════════
   GLASS CARDS
══════════════════════════════════════ */
.card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 22px; padding: 30px; margin-bottom: 16px;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
    position: relative; overflow: hidden;
}
.card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(102,126,234,0.4), transparent);
}
.card:hover {
    border-color: rgba(102,126,234,0.3);
    box-shadow: 0 8px 40px rgba(102,126,234,0.1);
}
.card-title {
    font-family: 'Space Grotesk', sans-serif; font-size: 10px; font-weight: 700;
    letter-spacing: 0.15em; text-transform: uppercase;
    color: rgba(255,255,255,0.25); -webkit-text-fill-color: rgba(255,255,255,0.25);
    margin-bottom: 20px; display: flex; align-items: center; gap: 8px;
}
.card-title::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.06); }

/* ══════════════════════════════════════
   TEXT INPUTS
══════════════════════════════════════ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #0f1020 !important;
    border: 1px solid rgba(102,126,234,0.25) !important;
    border-radius: 12px !important;
    color: #e8e6f8 !important; caret-color: #667eea !important;
    font-family: 'Inter', sans-serif !important; font-size: 15px !important;
    -webkit-text-fill-color: #e8e6f8 !important; line-height: 1.6 !important;
    transition: all 0.25s ease !important;
}
.stTextInput > div > div > input:hover,
.stTextArea > div > div > textarea:hover {
    border-color: rgba(102,126,234,0.45) !important;
    background: #111228 !important; -webkit-text-fill-color: #e8e6f8 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(102,126,234,0.75) !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.15) !important;
    background: #111228 !important;
    color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: rgba(165,180,252,0.3) !important;
    -webkit-text-fill-color: rgba(165,180,252,0.3) !important;
    font-style: italic !important;
}
.stTextInput label, .stTextArea label {
    font-family: 'Inter', sans-serif !important; font-size: 11px !important;
    font-weight: 700 !important; letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: rgba(165,180,252,0.5) !important;
    -webkit-text-fill-color: rgba(165,180,252,0.5) !important;
}

/* ══════════════════════════════════════
   FILE UPLOADER — COMPLETE DARK FIX
══════════════════════════════════════ */
[data-testid="stFileUploader"] {
    background: transparent !important;
}
[data-testid="stFileUploader"] label {
    font-family: 'Inter', sans-serif !important; font-size: 11px !important;
    font-weight: 700 !important; letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: rgba(165,180,252,0.5) !important;
    -webkit-text-fill-color: rgba(165,180,252,0.5) !important;
}
[data-testid="stFileUploader"] > div {
    background: #0f1020 !important;
    border-radius: 16px !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: #0f1020 !important;
    border: 1.5px dashed rgba(102,126,234,0.4) !important;
    border-radius: 16px !important;
    transition: all 0.25s ease !important;
    padding: 32px 24px !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: rgba(102,126,234,0.7) !important;
    background: rgba(15,16,32,0.95) !important;
    box-shadow: 0 0 30px rgba(102,126,234,0.1) !important;
}
[data-testid="stFileUploaderDropzone"] * {
    background: transparent !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    background: transparent !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] div {
    background: transparent !important;
    color: rgba(255,255,255,0.75) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.75) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span {
    background: transparent !important;
    color: rgba(255,255,255,0.75) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.75) !important;
    font-size: 14px !important; font-weight: 500 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small {
    background: transparent !important;
    color: rgba(165,180,252,0.4) !important;
    -webkit-text-fill-color: rgba(165,180,252,0.4) !important;
    font-size: 12px !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: rgba(102,126,234,0.15) !important;
    border: 1px solid rgba(102,126,234,0.45) !important;
    border-radius: 50px !important;
    color: #a5b4fc !important; -webkit-text-fill-color: #a5b4fc !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important; font-weight: 600 !important;
    padding: 8px 22px !important; cursor: pointer !important;
    box-shadow: none !important; transform: none !important;
    transition: all 0.25s ease !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    border-color: transparent !important;
    color: #ffffff !important; -webkit-text-fill-color: #ffffff !important;
    box-shadow: 0 4px 16px rgba(102,126,234,0.4) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] p {
    color: rgba(255,255,255,0.7) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.7) !important;
    font-size: 13px !important;
}

/* ══════════════════════════════════════
   BUTTONS
══════════════════════════════════════ */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important; border-radius: 50px !important;
    color: #fff !important; -webkit-text-fill-color: #fff !important;
    font-family: 'Inter', sans-serif !important; font-size: 15px !important;
    font-weight: 700 !important; letter-spacing: 0.02em !important;
    padding: 15px 36px !important; transition: all 0.3s ease !important;
    box-shadow: 0 5px 25px rgba(102,126,234,0.4) !important;
}
.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 35px rgba(102,126,234,0.55) !important;
}
.stButton > button:active { transform: translateY(-1px) !important; }
.stButton > button:disabled {
    background: rgba(255,255,255,0.06) !important;
    color: rgba(255,255,255,0.2) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.2) !important;
    box-shadow: none !important; transform: none !important;
}

/* ══════════════════════════════════════
   DOWNLOAD BUTTON
══════════════════════════════════════ */
.stDownloadButton > button {
    background: rgba(102,126,234,0.08) !important;
    border: 1px solid rgba(102,126,234,0.35) !important;
    border-radius: 50px !important;
    color: #a5b4fc !important; -webkit-text-fill-color: #a5b4fc !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important; font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    border-color: transparent !important;
    color: #fff !important; -webkit-text-fill-color: #fff !important;
    box-shadow: 0 6px 24px rgba(102,126,234,0.45) !important;
    transform: translateY(-2px) !important;
}

/* ══════════════════════════════════════
   QUESTION CARD
══════════════════════════════════════ */
.q-card {
    background: linear-gradient(135deg, rgba(102,126,234,0.07), rgba(118,75,162,0.04));
    border: 1px solid rgba(102,126,234,0.22);
    border-left: 3px solid #667eea;
    border-radius: 0 16px 16px 0;
    padding: 24px 26px; margin-bottom: 16px;
    animation: fadeUp 0.4s ease; position: relative; overflow: hidden;
}
.q-card::after {
    content: ''; position: absolute; top: 0; right: 0;
    width: 120px; height: 120px;
    background: radial-gradient(circle, rgba(102,126,234,0.08), transparent 70%);
    pointer-events: none;
}
.q-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 12px; border-radius: 50px;
    font-size: 10px; font-weight: 700; letter-spacing: 0.09em;
    text-transform: uppercase; margin-bottom: 13px;
}
.badge-technical { background: rgba(102,126,234,0.15); color: #a5b4fc !important; -webkit-text-fill-color: #a5b4fc !important; border: 1px solid rgba(102,126,234,0.3); }
.badge-behavioural { background: rgba(118,75,162,0.15); color: #c4b5fd !important; -webkit-text-fill-color: #c4b5fd !important; border: 1px solid rgba(118,75,162,0.3); }
.badge-company_specific { background: rgba(240,147,251,0.1); color: #f0abfc !important; -webkit-text-fill-color: #f0abfc !important; border: 1px solid rgba(240,147,251,0.25); }
.q-num { font-family: 'Space Grotesk', sans-serif; font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.2) !important; -webkit-text-fill-color: rgba(255,255,255,0.2) !important; float: right; }
.q-text { font-size: 16px; font-weight: 400; line-height: 1.75; color: rgba(255,255,255,0.9) !important; -webkit-text-fill-color: rgba(255,255,255,0.9) !important; }

/* ══════════════════════════════════════
   CANDIDATE MESSAGE
══════════════════════════════════════ */
.c-msg {
    background: linear-gradient(135deg, rgba(16,185,129,0.06), rgba(6,78,59,0.04));
    border: 1px solid rgba(16,185,129,0.2); border-left: 3px solid #10b981;
    border-radius: 0 16px 16px 0; padding: 20px 24px; margin-bottom: 16px;
    animation: fadeUp 0.4s ease;
}
.c-msg-label {
    font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
    color: #34d399 !important; -webkit-text-fill-color: #34d399 !important;
    margin-bottom: 8px; display: flex; align-items: center; gap: 6px;
}
.c-msg-label::before { content: ''; width: 6px; height: 6px; background: #34d399; border-radius: 50%; }
.c-msg-text { font-size: 15px; line-height: 1.7; color: rgba(255,255,255,0.72) !important; -webkit-text-fill-color: rgba(255,255,255,0.72) !important; }

/* ══════════════════════════════════════
   STAR CARD
══════════════════════════════════════ */
.star-card {
    background: rgba(8,6,20,0.85);
    border: 1px solid rgba(102,126,234,0.22);
    border-radius: 18px; padding: 22px 24px; margin-bottom: 18px;
    animation: fadeUp 0.4s ease; position: relative; overflow: hidden;
}
.star-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(102,126,234,0.5), rgba(240,147,251,0.5), transparent);
}
.star-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.star-title { font-family: 'Space Grotesk', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.25) !important; -webkit-text-fill-color: rgba(255,255,255,0.25) !important; }
.star-overall { font-family: 'Space Grotesk', sans-serif; font-size: 30px; font-weight: 800; line-height: 1; }
.star-dims { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px; }
.star-dim { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 14px 8px; text-align: center; transition: border-color 0.2s ease; }
.star-dim:hover { border-color: rgba(102,126,234,0.3); }
.star-dim-val { font-family: 'Space Grotesk', sans-serif; font-size: 26px; font-weight: 800; line-height: 1; margin-bottom: 5px; }
.star-dim-label { font-size: 10px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(255,255,255,0.28) !important; -webkit-text-fill-color: rgba(255,255,255,0.28) !important; }
.star-feedback { font-size: 13px; line-height: 1.7; color: rgba(255,255,255,0.48) !important; -webkit-text-fill-color: rgba(255,255,255,0.48) !important; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 14px; }
.fb-good { color: #34d399 !important; -webkit-text-fill-color: #34d399 !important; font-weight: 600; }
.fb-bad { color: #f87171 !important; -webkit-text-fill-color: #f87171 !important; font-weight: 600; display: block; margin-top: 6px; }

/* ══════════════════════════════════════
   PROGRESS BAR
══════════════════════════════════════ */
.prog-wrap { margin-bottom: 32px; }
.prog-meta { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.prog-label { font-size: 11px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(255,255,255,0.25) !important; -webkit-text-fill-color: rgba(255,255,255,0.25) !important; }
.prog-val { font-family: 'Space Grotesk', sans-serif; font-size: 13px; font-weight: 700; color: #a5b4fc !important; -webkit-text-fill-color: #a5b4fc !important; background: rgba(102,126,234,0.1); border: 1px solid rgba(102,126,234,0.2); padding: 3px 12px; border-radius: 50px; }
.prog-track { height: 6px; background: rgba(255,255,255,0.06); border-radius: 100px; overflow: hidden; position: relative; }
.prog-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2, #f093fb); border-radius: 100px; transition: width 0.6s cubic-bezier(0.4,0,0.2,1); position: relative; }
.prog-fill::after { content: ''; position: absolute; right: 0; top: 50%; transform: translateY(-50%); width: 10px; height: 10px; background: #f093fb; border-radius: 50%; box-shadow: 0 0 8px rgba(240,147,251,0.8); }

/* ══════════════════════════════════════
   METRICS
══════════════════════════════════════ */
.metric-row { display: grid; grid-template-columns: 1.5fr 1fr 1fr 1fr; gap: 14px; margin-bottom: 30px; }
.metric-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 20px; padding: 24px 16px; text-align: center; transition: all 0.3s ease; position: relative; overflow: hidden; }
.metric-box::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent); }
.metric-box:hover { border-color: rgba(102,126,234,0.35); transform: translateY(-2px); box-shadow: 0 8px 30px rgba(102,126,234,0.12); }
.metric-box.main-box { background: linear-gradient(135deg, rgba(102,126,234,0.18), rgba(118,75,162,0.14)); border-color: rgba(102,126,234,0.4); box-shadow: 0 8px 40px rgba(102,126,234,0.2); }
.metric-box.main-box::before { background: linear-gradient(90deg, transparent, rgba(102,126,234,0.6), rgba(240,147,251,0.4), transparent); }
.metric-num { font-family: 'Space Grotesk', sans-serif; font-size: 42px; font-weight: 800; line-height: 1; margin-bottom: 8px; }
.metric-lbl { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(255,255,255,0.3) !important; -webkit-text-fill-color: rgba(255,255,255,0.3) !important; }

/* ══════════════════════════════════════
   DONE BANNER
══════════════════════════════════════ */
.done-banner {
    background: linear-gradient(135deg, rgba(102,126,234,0.12), rgba(240,147,251,0.08));
    border: 1px solid rgba(102,126,234,0.28); border-radius: 22px;
    padding: 44px; text-align: center; margin-bottom: 30px;
    position: relative; overflow: hidden;
}
.done-banner::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(102,126,234,0.7), rgba(240,147,251,0.5), transparent); }
.done-banner::after { content: ''; position: absolute; top: -80px; right: -80px; width: 240px; height: 240px; background: radial-gradient(circle, rgba(240,147,251,0.1), transparent 70%); pointer-events: none; }
.done-banner h2 { font-family: 'Space Grotesk', sans-serif; font-size: 36px; font-weight: 800; background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 50%, #f0abfc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 10px; position: relative; }
.done-banner p { color: rgba(255,255,255,0.5) !important; -webkit-text-fill-color: rgba(255,255,255,0.5) !important; font-size: 16px; position: relative; }

/* ══════════════════════════════════════
   SESSION PILL
══════════════════════════════════════ */
.sess-pill { display: inline-flex; align-items: center; gap: 9px; background: rgba(102,126,234,0.08); border: 1px solid rgba(102,126,234,0.22); border-radius: 50px; padding: 8px 18px; font-size: 12px; font-weight: 600; color: #a5b4fc !important; -webkit-text-fill-color: #a5b4fc !important; margin-top: 22px; }
.sess-dot { width: 7px; height: 7px; background: #10b981; border-radius: 50%; box-shadow: 0 0 6px rgba(16,185,129,0.7); animation: pulse 2s ease-in-out infinite; }

/* ══════════════════════════════════════
   SECTION LABEL
══════════════════════════════════════ */
.sec-label { font-family: 'Space Grotesk', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.22) !important; -webkit-text-fill-color: rgba(255,255,255,0.22) !important; margin-bottom: 16px; margin-top: 6px; display: flex; align-items: center; gap: 10px; }
.sec-label::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.05); }

/* ══════════════════════════════════════
   ALERTS
══════════════════════════════════════ */
.stSuccess > div { background: rgba(16,185,129,0.07) !important; border: 1px solid rgba(16,185,129,0.22) !important; border-radius: 14px !important; color: #34d399 !important; }
.stError > div { background: rgba(239,68,68,0.07) !important; border: 1px solid rgba(239,68,68,0.22) !important; border-radius: 14px !important; color: #fca5a5 !important; }
.stWarning > div { background: rgba(245,158,11,0.07) !important; border: 1px solid rgba(245,158,11,0.22) !important; border-radius: 14px !important; color: #fcd34d !important; }
.stInfo > div { background: rgba(102,126,234,0.07) !important; border: 1px solid rgba(102,126,234,0.22) !important; border-radius: 14px !important; color: #a5b4fc !important; }

/* ══════════════════════════════════════
   EXPANDER
══════════════════════════════════════ */
.streamlit-expanderHeader { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 12px !important; color: rgba(255,255,255,0.7) !important; font-family: 'Inter', sans-serif !important; font-weight: 600 !important; font-size: 14px !important; transition: all 0.2s ease !important; }
.streamlit-expanderHeader:hover { border-color: rgba(102,126,234,0.3) !important; background: rgba(102,126,234,0.05) !important; }
.streamlit-expanderContent { background: rgba(255,255,255,0.02) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-top: none !important; border-radius: 0 0 12px 12px !important; color: rgba(255,255,255,0.68) !important; padding: 16px !important; }

/* ══════════════════════════════════════
   METRIC WIDGET
══════════════════════════════════════ */
[data-testid="metric-container"] { background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 14px !important; padding: 18px !important; transition: all 0.2s ease !important; }
[data-testid="metric-container"]:hover { border-color: rgba(102,126,234,0.3) !important; }
[data-testid="metric-container"] label { color: rgba(255,255,255,0.3) !important; font-size: 10px !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
[data-testid="metric-container"] [data-testid="metric-value"] { font-family: 'Space Grotesk', sans-serif !important; font-size: 30px !important; font-weight: 800 !important; color: #a5b4fc !important; }

/* ══════════════════════════════════════
   MISC
══════════════════════════════════════ */
hr { border-color: rgba(255,255,255,0.06) !important; margin: 30px 0 !important; }
.stSpinner > div { color: #667eea !important; }
[data-testid="column"] { padding: 0 8px !important; }
p { color: rgba(255,255,255,0.72); -webkit-text-fill-color: rgba(255,255,255,0.72); }
strong { color: rgba(255,255,255,0.9) !important; -webkit-text-fill-color: rgba(255,255,255,0.9) !important; }
code { background: rgba(102,126,234,0.1) !important; color: #a5b4fc !important; -webkit-text-fill-color: #a5b4fc !important; border-radius: 6px !important; padding: 2px 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ────────────────────────────────────────────────────
API_URL = "http://localhost:8000"

# ── Session State ────────────────────────────────────────────────
defaults = {
    "session_id": None, "interview_started": False,
    "interview_complete": False, "current_question": None,
    "question_number": 1, "total_questions": 15,
    "question_type": "technical", "chat_history": [],
    "scores_history": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers ──────────────────────────────────────────────────────
def check_api():
    try:
        return requests.get(f"{API_URL}/", timeout=3).status_code == 200
    except:
        return False

def score_color(s):
    if s >= 7: return "#34d399"
    if s >= 5: return "#fbbf24"
    return "#f87171"

def readiness_label(pct):
    if pct >= 80: return "🟢 Strong — Ready to interview"
    if pct >= 65: return "🟡 Good — Minor gaps to address"
    if pct >= 50: return "🟠 Fair — Needs more preparation"
    return "🔴 Needs work — Focused study required"

def render_star(scores):
    overall = scores.get("overall", 0)
    col = score_color(overall)
    s,t,a,r = scores.get("S",0), scores.get("T",0), scores.get("A",0), scores.get("R",0)
    good = scores.get("good","")[:140]
    missing = scores.get("missing","")[:140]
    st.markdown(f"""
    <div class="star-card">
        <div class="star-header">
            <span class="star-title">⭐ STAR Evaluation</span>
            <span class="star-overall" style="color:{col}">{overall}<span style="font-size:15px;color:rgba(255,255,255,0.18)">/10</span></span>
        </div>
        <div class="star-dims">
            <div class="star-dim"><div class="star-dim-val" style="color:{score_color(s)}">{s}</div><div class="star-dim-label">Situation</div></div>
            <div class="star-dim"><div class="star-dim-val" style="color:{score_color(t)}">{t}</div><div class="star-dim-label">Task</div></div>
            <div class="star-dim"><div class="star-dim-val" style="color:{score_color(a)}">{a}</div><div class="star-dim-label">Action</div></div>
            <div class="star-dim"><div class="star-dim-val" style="color:{score_color(r)}">{r}</div><div class="star-dim-label">Result</div></div>
        </div>
        <div class="star-feedback">
            <span class="fb-good">✓ Strong —</span> {good}
            <span class="fb-bad">✗ Missing —</span> {missing}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <div class="hero-content">
        <div class="hero-badge"><span class="hero-badge-dot"></span>AI-Powered Interview Coach</div>
        <h1>InterviewCopilot</h1>
        <p class="hero-sub">Resume × Job Description × Company Intelligence<br>Every question personalised just for you</p>
        <div class="hero-tags">
            <span class="hero-tag">🧠 Multi-Agent AI</span>
            <span class="hero-tag">📊 STAR Scoring</span>
            <span class="hero-tag">🏢 Company Research</span>
            <span class="hero-tag">📄 PDF Report</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if not check_api():
    st.error("⚠ FastAPI backend offline — run: `uvicorn api.main:app --reload --port 8000`")
    st.stop()

st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["  🚀  Setup  ", "  🎤  Interview  ", "  📊  Report  "])


# ════════════════════════════════════════════════════════════════
# TAB 1 — SETUP
# ════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="sec-label">Configure Your Session</p>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="card"><p class="card-title">📄 Resume</p>', unsafe_allow_html=True)

        # Upload section label
        st.markdown("""
        <p style="font-size:11px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
        color:rgba(165,180,252,0.5);-webkit-text-fill-color:rgba(165,180,252,0.5);margin-bottom:8px;">
        Upload PDF Resume
        </p>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "upload",
            type=["pdf"],
            label_visibility="collapsed"
        )

        resume_text = ""
        if uploaded:
            with st.spinner("Extracting resume text..."):
                try:
                    r = requests.post(
                        f"{API_URL}/upload-resume",
                        files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
                    )
                    if r.status_code == 200:
                        resume_text = r.json()["resume_text"]
                        st.success(f"✓ Resume extracted — {r.json()['character_count']:,} characters")
                        with st.expander("👁 Preview extracted text"):
                            st.code(resume_text[:700], language=None)
                except Exception as e:
                    st.error(str(e))

        st.markdown("""
        <p style="font-size:11px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
        color:rgba(165,180,252,0.5);-webkit-text-fill-color:rgba(165,180,252,0.5);
        margin-top:18px;margin-bottom:8px;">
        Or Paste Resume Text
        </p>
        """, unsafe_allow_html=True)

        if not resume_text:
            resume_text = st.text_area(
                "resume_paste",
                height=160,
                placeholder="Paste your full resume here — skills, projects, experience, education...",
                label_visibility="collapsed"
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card"><p class="card-title">💼 Job Details</p>', unsafe_allow_html=True)
        company_name = st.text_input(
            "Target Company",
            placeholder="e.g. Google, Flipkart, Microsoft, Zomato..."
        )
        jd_text = st.text_area(
            "Job Description",
            height=200,
            placeholder="Paste the full job description — required skills, responsibilities, level..."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.5, 2, 1.5])
    with c2:
        go = st.button(
            "🚀  Generate My Interview",
            use_container_width=True,
            disabled=not (resume_text.strip() and jd_text.strip() and company_name.strip())
        )

    if go:
        with st.spinner(f"🤖 Building your personalised {company_name} interview — 30-60 seconds..."):
            try:
                r = requests.post(
                    f"{API_URL}/start",
                    json={"jd_text": jd_text, "company_name": company_name, "resume_text": resume_text},
                    timeout=120
                )
                if r.status_code == 200:
                    d = r.json()
                    st.session_state.update({
                        "session_id": d["session_id"],
                        "interview_started": True,
                        "interview_complete": False,
                        "current_question": d["current_question"],
                        "question_number": d["question_number"],
                        "total_questions": d["total_questions"],
                        "question_type": d.get("question_type", "technical"),
                        "chat_history": [],
                        "scores_history": [],
                    })
                    st.success(f"✓ Ready! {d['total_questions']} personalised questions generated. Switch to the Interview tab!")
                else:
                    st.error(r.json().get("detail", r.text))
            except requests.Timeout:
                st.error("Request timed out — please try again.")
            except Exception as e:
                st.error(str(e))

    if st.session_state.interview_started:
        st.markdown(f"""
        <div class="sess-pill">
            <span class="sess-dot"></span>
            Session {st.session_state.session_id}
            &nbsp;·&nbsp;
            {st.session_state.question_number - 1} / {st.session_state.total_questions} answered
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# TAB 2 — INTERVIEW
# ════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.interview_started:
        st.info("👈 Complete the Setup tab first to generate your personalised interview.")
        st.stop()

    if st.session_state.interview_complete:
        st.markdown("""
        <div class="done-banner">
            <h2>🎯 Interview Complete!</h2>
            <p>All questions answered. Switch to the Report tab to see your readiness score.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    prog = (st.session_state.question_number - 1) / st.session_state.total_questions
    pct = round(prog * 100)
    st.markdown(f"""
    <div class="prog-wrap">
        <div class="prog-meta">
            <span class="prog-label">Interview Progress</span>
            <span class="prog-val">Q{st.session_state.question_number} of {st.session_state.total_questions}</span>
        </div>
        <div class="prog-track"><div class="prog-fill" style="width:{pct}%"></div></div>
    </div>
    """, unsafe_allow_html=True)

    for item in st.session_state.chat_history:
        if item["role"] == "interviewer":
            qtype = item.get("type", "technical")
            idx = item.get("index", "")
            st.markdown(f"""
            <div class="q-card">
                <span class="q-num">Q{idx}</span>
                <span class="q-badge badge-{qtype}">{qtype.replace('_',' ')}</span>
                <div class="q-text">{item['content']}</div>
            </div>""", unsafe_allow_html=True)
        elif item["role"] == "candidate":
            st.markdown(f"""
            <div class="c-msg">
                <div class="c-msg-label">Your Answer</div>
                <div class="c-msg-text">{item['content']}</div>
            </div>""", unsafe_allow_html=True)
        elif item["role"] == "score":
            render_star(item["scores"])

    if st.session_state.current_question:
        qtype = st.session_state.question_type
        st.markdown(f"""
        <div class="q-card">
            <span class="q-num">Q{st.session_state.question_number}</span>
            <span class="q-badge badge-{qtype}">{qtype.replace('_',' ')}</span>
            <div class="q-text">{st.session_state.current_question}</div>
        </div>""", unsafe_allow_html=True)

    answer = st.text_area(
        "Your Answer",
        height=150,
        key=f"ans_{st.session_state.question_number}",
        placeholder="Be specific — describe a real situation, what you did personally, and the measurable outcome..."
    )

    c1, c2, c3 = st.columns([1.5, 2, 1.5])
    with c2:
        submitted = st.button(
            "Submit Answer →",
            use_container_width=True,
            disabled=not answer.strip()
        )

    if submitted and answer.strip():
        st.session_state.chat_history.append({
            "role": "interviewer",
            "content": st.session_state.current_question,
            "type": st.session_state.question_type,
            "index": st.session_state.question_number
        })
        st.session_state.chat_history.append({"role": "candidate", "content": answer})
        with st.spinner("🤖 Evaluating with STAR scoring..."):
            try:
                r = requests.post(
                    f"{API_URL}/answer",
                    json={"session_id": st.session_state.session_id, "answer": answer},
                    timeout=60
                )
                if r.status_code == 200:
                    d = r.json()
                    scores = d["scores"]
                    st.session_state.chat_history.append({"role": "score", "scores": scores})
                    st.session_state.scores_history.append(scores)
                    if d["is_complete"]:
                        st.session_state.interview_complete = True
                        st.session_state.current_question = None
                    else:
                        st.session_state.current_question = d["next_question"]
                        st.session_state.question_number = d["question_number"]
                    st.rerun()
                else:
                    st.error(r.json().get("detail", r.text))
            except Exception as e:
                st.error(str(e))


# ════════════════════════════════════════════════════════════════
# TAB 3 — REPORT
# ════════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.interview_started:
        st.info("Complete your interview first to see your report.")
        st.stop()

    if not st.session_state.interview_complete:
        answered = st.session_state.question_number - 1
        total = st.session_state.total_questions
        st.warning(f"⏳ Interview in progress — {answered}/{total} questions answered.")
        if st.session_state.scores_history:
            avg = sum(s.get("overall", 0) for s in st.session_state.scores_history) / len(st.session_state.scores_history)
            st.metric("Running Average", f"{avg:.1f} / 10")
        st.stop()

    scores = st.session_state.scores_history
    if not scores:
        st.error("No scores found.")
        st.stop()

    avg = sum(s.get("overall", 0) for s in scores) / len(scores)
    pct = round(avg * 10)

    st.markdown(f"""
    <div class="done-banner">
        <h2>{pct}% Readiness Score</h2>
        <p>{readiness_label(pct)}</p>
    </div>
    """, unsafe_allow_html=True)

    avg_s = round(sum(s.get("S", 0) for s in scores) / len(scores), 1)
    avg_t = round(sum(s.get("T", 0) for s in scores) / len(scores), 1)
    avg_a = round(sum(s.get("A", 0) for s in scores) / len(scores), 1)
    avg_r = round(sum(s.get("R", 0) for s in scores) / len(scores), 1)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box main-box">
            <div class="metric-num" style="background:linear-gradient(135deg,#a5b4fc,#f0abfc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{avg:.1f}</div>
            <div class="metric-lbl">Overall / 10</div>
        </div>
        <div class="metric-box"><div class="metric-num" style="color:{score_color(avg_s)}">{avg_s}</div><div class="metric-lbl">Situation</div></div>
        <div class="metric-box"><div class="metric-num" style="color:{score_color(avg_a)}">{avg_a}</div><div class="metric-lbl">Action</div></div>
        <div class="metric-box"><div class="metric-num" style="color:{score_color(avg_r)}">{avg_r}</div><div class="metric-lbl">Result</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="sec-label">Score Progression</p>', unsafe_allow_html=True)
    import pandas as pd
    df = pd.DataFrame({
        "Question": range(1, len(scores) + 1),
        "Score": [round(s.get("overall", 0), 1) for s in scores]
    }).set_index("Question")
    st.line_chart(df, color="#667eea", height=220)

    st.divider()

    st.markdown('<p class="sec-label">Download Report</p>', unsafe_allow_html=True)
    dc1, dc2 = st.columns(2)
    with dc1:
        try:
            r = requests.get(f"{API_URL}/report/{st.session_state.session_id}", timeout=30)
            if r.status_code == 200 and "pdf" in r.headers.get("content-type", ""):
                st.download_button("⬇ Download PDF Report", r.content,
                    f"report_{st.session_state.session_id}.pdf", "application/pdf", use_container_width=True)
            elif os.path.exists("outputs/interview_report.pdf"):
                with open("outputs/interview_report.pdf", "rb") as f:
                    st.download_button("⬇ Download PDF Report", f.read(),
                        "interview_report.pdf", "application/pdf", use_container_width=True)
        except Exception as e:
            st.error(str(e))
    with dc2:
        if os.path.exists("outputs/report.html"):
            with open("outputs/report.html", "r", encoding="utf-8") as f:
                st.download_button("⬇ Download HTML Report", f.read(),
                    "interview_report.html", "text/html", use_container_width=True)

    st.divider()

    st.markdown('<p class="sec-label">Question Breakdown</p>', unsafe_allow_html=True)
    for i, s in enumerate(scores, 1):
        overall = s.get("overall", 0)
        with st.expander(f"Q{i}  ·  {s.get('question_type','').replace('_',' ').title()}  ·  Score: {overall}/10"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Situation", f"{s.get('S', 0)}/10")
            c2.metric("Task", f"{s.get('T', 0)}/10")
            c3.metric("Action", f"{s.get('A', 0)}/10")
            c4.metric("Result", f"{s.get('R', 0)}/10")
            st.markdown(f"**✓ Strong:** {s.get('good', '')}")
            st.markdown(f"**✗ Missing:** {s.get('missing', '')}")
            if s.get("model_answer"):
                st.markdown(f"**💡 Model Answer:** {s.get('model_answer', '')}")

    st.divider()
    c1, c2, c3 = st.columns([1.5, 2, 1.5])
    with c2:
        if st.button("🔄 Start New Interview", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)