import streamlit as st
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import numpy as np

load_dotenv()

st.set_page_config(page_title="FinAgent - Amortization Calculator", page_icon="🤖", layout="wide")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

ANALYSIS_LABELS = {
    "amortization": "Loan Amortization Analysis",
    "advisory": "Loan Advisory Report"
}

def calculate_amortization(principal, annual_rate, years):
    monthly_rate = annual_rate / 12 / 100
    months = years * 12
    
    if monthly_rate > 0:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    else:
        monthly_payment = principal / months
    
    schedule = []
    balance = principal
    total_interest = 0
    
    for month in range(1, months + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        total_interest += interest_payment
        
        schedule.append({
            'Month': month,
            'Payment': round(monthly_payment, 2),
            'Principal': round(principal_payment, 2),
            'Interest': round(interest_payment, 2),
            'Balance': round(max(balance, 0), 2)
        })
    
    total_payment = monthly_payment * months
    
    return monthly_payment, total_interest, total_payment, pd.DataFrame(schedule)

def format_analysis(text):
    lines = text.split("\n")
    formatted = []
    in_list = False
    for line in lines:
        line = line.strip()
        if line.startswith("## "):
            formatted.append(f"<h3>{line[3:]}</h3>")
            in_list = False
        elif line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. ") or line.startswith("4. ") or line.startswith("5. "):
            if not in_list:
                formatted.append("<ul>")
                in_list = True
            formatted.append(f"<li>{line[3:]}</li>")
        elif line.startswith("-"):
            if not in_list:
                formatted.append("<ul>")
                in_list = True
            formatted.append(f"<li>{line[1:].strip()}</li>")
        elif in_list and not line:
            formatted.append("</ul>")
            in_list = False
        elif line:
            if in_list:
                formatted.append("</ul>")
                in_list = False
            formatted.append(f"<p>{line}</p>")
    return "".join(formatted)

if "history" not in st.session_state:
    st.session_state.history = []

st.markdown("""
<style>
    :root {
        --bg: #0a0e17;
        --surface: #111827;
        --surface2: #1a2235;
        --border: #1e2d45;
        --accent: #00d4aa;
        --accent2: #3b82f6;
        --accent3: #f59e0b;
        --danger: #ef4444;
        --text: #e2e8f0;
        --muted: #64748b;
        --green: #10b981;
        --red: #ef4444;
    }
    .stApp {
        background: var(--bg);
        color: var(--text);
    }
    .main-header {
        text-align: center;
        padding: 40px 0 30px;
    }
    .main-header h1 {
        font-family: 'Syne', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 10px 0;
    }
    .main-header h1 em {
        color: var(--accent);
    }
    .workflow-box {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 30px;
    }
    .workflow-steps {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .workflow-step {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 12px 16px;
    }
    .score-card {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .risk-badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .risk-low { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
    .risk-medium { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
    .risk-high { background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
    .analysis-content h3 {
        font-family: 'Syne', sans-serif;
        font-size: 1rem;
        color: var(--accent);
        margin: 20px 0 8px;
        padding-bottom: 6px;
        border-bottom: 1px solid rgba(0,212,170,0.15);
    }
    .analysis-content p { margin-bottom: 10px; }
    .analysis-content ul { padding-left: 20px; margin-bottom: 10px; }
    .analysis-content li { margin-bottom: 4px; }
    .history-item {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .thinking-step {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 0;
        color: var(--muted);
    }
    .thinking-step.done { color: var(--green); }
    .thinking-step.active { color: var(--accent); }
    .step-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: currentColor;
    }
    .step-dot.spinning {
        animation: spin 0.8s linear infinite;
        border-radius: 0;
        background: none;
        border: 2px solid currentColor;
        border-top-color: transparent;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .positive { color: var(--green); }
    .negative { color: var(--red); }
    .neutral { color: var(--accent3); }
    .stButton>button {
        background: linear-gradient(135deg, var(--accent), #00b894);
        border: none;
        border-radius: 10px;
        color: #0a0e17;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        padding: 12px 24px;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 24px rgba(0,212,170,0.25);
    }
    .stButton>button:disabled {
        opacity: 0.5;
    }
    .preset-btn {
        background: var(--surface2);
        border: 1px solid var(--border);
        border-radius: 6px;
        color: var(--muted);
        font-size: 0.75rem;
        padding: 6px 12px;
        cursor: pointer;
    }
    .preset-btn:hover { border-color: var(--accent); color: var(--accent); }
    .about-box {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>Intelligent <em>Amortization</em> Calculator</h1>
    <p style="color: var(--muted); max-width: 600px; margin: 0 auto;">
        An AI-powered agent that calculates loan amortization schedules and provides intelligent insights for banking and lending decisions.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.markdown("### 📋 Loan Data Input")
    
    analysis_type = st.selectbox("Analysis Type", list(ANALYSIS_LABELS.keys()), format_func=lambda x: ANALYSIS_LABELS[x])
    
    st.markdown("**Or Upload Excel File**")
    uploaded_file = st.file_uploader("Upload Excel file with loan data", type=['xlsx', 'xls'])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.dataframe(df, use_container_width=True)
            st.session_state.excel_data = df
            st.success(f"Loaded {len(df)} rows from Excel file")
        except Exception as e:
            st.error(f"Error reading Excel: {e}")
    
    st.markdown("**Quick Presets**")
    preset_cols = st.columns(4)
    with preset_cols[0]:
        if st.button("Mortgage", key="preset_mortgage"):
            st.session_state.preset = "mortgage"
    with preset_cols[1]:
        if st.button("Auto Loan", key="preset_auto"):
            st.session_state.preset = "auto"
    with preset_cols[2]:
        if st.button("Business", key="preset_business"):
            st.session_state.preset = "business"
    with preset_cols[3]:
        if st.button("Personal", key="preset_personal"):
            st.session_state.preset = "personal"
    
    PRESETS = {
        "mortgage": {
            "name": "Home Mortgage",
            "principal": 250000,
            "annual_rate": 6.5,
            "years": 30,
            "context": "30-year fixed rate mortgage for a residential property. Borrower has excellent credit history and stable employment."
        },
        "auto": {
            "name": "Auto Loan",
            "principal": 35000,
            "annual_rate": 7.5,
            "years": 5,
            "context": "5-year auto loan for new vehicle purchase. Borrower has good credit score and existing debt obligations."
        },
        "business": {
            "name": "Business Loan",
            "principal": 150000,
            "annual_rate": 9.5,
            "years": 7,
            "context": "Working capital loan for small business expansion. Business has consistent revenue growth over 3 years."
        },
        "personal": {
            "name": "Personal Loan",
            "principal": 25000,
            "annual_rate": 12.0,
            "years": 3,
            "context": "Personal loan for home improvement. Borrower has moderate credit score and existing financial obligations."
        }
    }
    
    if "preset" in st.session_state:
        p = PRESETS[st.session_state.preset]
        entity_name = p["name"]
        principal = p["principal"]
        annual_rate = p["annual_rate"]
        years = p["years"]
        context = p["context"]
    elif "excel_data" in st.session_state and st.session_state.excel_data is not None:
        df = st.session_state.excel_data
        entity_name = str(df.iloc[0].get("Name", df.iloc[0].get("name", "Excel Loan")))
        principal = float(df.iloc[0].get("Principal", df.iloc[0].get("principal", 0)))
        annual_rate = float(df.iloc[0].get("Annual_Rate", df.iloc[0].get("annual_rate", 0)))
        years = int(df.iloc[0].get("Years", df.iloc[0].get("years", 1)))
        context = str(df.iloc[0].get("Context", df.iloc[0].get("context", "Excel loan data analysis")))
    else:
        p = PRESETS["mortgage"]
        entity_name = p["name"]
        principal = p["principal"]
        annual_rate = p["annual_rate"]
        years = p["years"]
        context = p["context"]
    
    st.markdown("### 📊 Loan Parameters")
    col_data1, col_data2 = st.columns(2)
    with col_data1:
        st.markdown(f"**Loan Name:** {entity_name}")
        st.markdown(f"**Principal:** ${principal:,.2f}")
    with col_data2:
        st.markdown(f"**Annual Rate:** {annual_rate}%")
        st.markdown(f"**Term:** {years} years")
    
    run_btn = st.button("🚀 Run AI Amortization Analysis")

with col2:
    st.markdown("### 📁 Analysis History")
    if st.session_state.history:
        for h in st.session_state.history[:6]:
            st.markdown(f"""
            <div class="history-item">
                <strong>{h['entity']}</strong><br>
                <small style="color: var(--muted)">{h['type']}</small><br>
                <span style="color: var(--accent3); font-weight: 600;">${h['monthly']:,.0f}/mo</span>
                <span style="float: right; font-size: 0.7rem; color: var(--muted);">{h['time']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: var(--muted); font-size: 0.85rem;'>No analyses run yet.</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div class="about-box">
        <p style="font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;">ℹ️ About This Agent</p>
        <p style="font-size: 0.8rem; color: var(--muted); line-height: 1.6;">
            This AI agent uses <strong>Llama 3 via OpenRouter</strong> as its free LLM reasoning engine.
        </p>
        <p style="font-size: 0.8rem; color: var(--muted); margin-top: 8px;">
            <strong>HBF2212 Capstone Project</strong> — Great Zimbabwe University
        </p>
    </div>
    """, unsafe_allow_html=True)

if run_btn:
    monthly_payment, total_interest, total_payment, schedule = calculate_amortization(principal, annual_rate, years)
    analysis_label = ANALYSIS_LABELS[analysis_type]
    
    if total_interest > principal * 0.5:
        risk_level = "high"
    elif total_interest > principal * 0.25:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    with st.spinner("🤔 Agent is analyzing..."):
        thinking_phases = [
            "Ingesting loan parameters...",
            "Computing amortization schedule...",
            "Calculating financial metrics...",
            "Running LLM analysis and generating insights...",
            "Structuring decision-support output..."
        ]
        
        progress_bar = st.progress(0)
        for i, phase in enumerate(thinking_phases):
            st.markdown(f"<div class='thinking-step active'><div class='step-dot spinning'></div> {phase}</div>", unsafe_allow_html=True)
            progress_bar.progress((i + 1) / len(thinking_phases))
        
        prompt = f"""You are an expert AI financial analyst specializing in loan amortization analysis.

Analyse the following loan data and produce a comprehensive {analysis_label} report.

LOAN DATA:
- Loan Name: {entity_name}
- Principal Amount: USD {principal:,.2f}
- Annual Interest Rate: {annual_rate}%
- Loan Term: {years} years
- Monthly Payment: USD {monthly_payment:,.2f}
- Total Interest: USD {total_interest:,.2f}
- Total Payment: USD {total_payment:,.2f}
- Interest to Principal Ratio: {(total_interest/principal)*100:.1f}%
- Additional Context: {context}

ANALYSIS TYPE: {analysis_label}

Produce a structured report with these sections:
1. **Executive Summary** - 2-3 sentence overview of the loan
2. **Amortization Overview** - Key metrics and payment breakdown
3. **Interest Analysis** - How much interest paid vs principal
4. **Payment Schedule Insights** - Early vs late payment patterns
5. **Recommendations** - 3-5 actionable recommendations for the borrower
6. **Risk Assessment** - Identify potential risks
7. **Conclusion** - Overall assessment

Use specific numbers. Be analytical, professional, and precise."""

    if not GROQ_API_KEY:
        st.error("⚠️ GROQ_API_KEY not set. Please configure your API key.")
        st.info("Get a free API key from https://console.groq.com/keys")
    else:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1200
                },
                timeout=60
            )
            
            if response.status_code != 200:
                st.error(f"API Error: {response.text}")
            else:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                
                st.session_state.history.insert(0, {
                    "entity": entity_name,
                    "type": analysis_label,
                    "monthly": monthly_payment,
                    "time": datetime.now().strftime("%H:%M"),
                    "risk": risk_level
                })
                
                risk_class = f"risk-{risk_level}"
                risk_emoji = "🟢" if risk_level == "low" else "🟡" if risk_level == "medium" else "🔴"
                
                st.markdown("---")
                st.markdown("### 📊 Agent Output & Decision Support Report")
                
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.markdown(f"""
                    <div class="score-card">
                        <div class="score-val positive">${monthly_payment:,.2f}</div>
                        <div class="score-label">Monthly Payment</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_s2:
                    st.markdown(f"""
                    <div class="score-card">
                        <div class="score-val negative">${total_interest:,.2f}</div>
                        <div class="score-label">Total Interest</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_s3:
                    st.markdown(f"""
                    <div class="score-card">
                        <div class="score-val neutral">${total_payment:,.2f}</div>
                        <div class="score-label">Total Payment</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="margin: 16px 0;">
                    <span class="risk-badge {risk_class}">{risk_emoji} {risk_level.upper()} COST RISK</span>
                    <span style="font-size: 0.8rem; color: var(--muted); margin-left: 10px;">{analysis_label} · {entity_name}</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"<div class='analysis-content'>{format_analysis(text)}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### 📋 Amortization Schedule")
                st.dataframe(schedule, use_container_width=True, height=400)
                
                st.markdown("### 📈 Payment Breakdown Chart")
                chart_data = schedule[['Month', 'Principal', 'Interest']].head(60) if years > 5 else schedule[['Month', 'Principal', 'Interest']]
                chart_data = chart_data.set_index('Month')
                st.bar_chart(chart_data)
                
        except Exception as e:
            st.error(f"Agent Error: {str(e)}")
