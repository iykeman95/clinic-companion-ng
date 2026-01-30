import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Clinic Companion NG", page_icon="🏥", layout="centered")

DISCLAIMER = (
    "⚠️ **Educational use only (not medical advice).**\n\n"
    "- This tool does **not** diagnose illness or recommend treatment.\n"
    "- Do **not** start/stop medicines based on this.\n"
    "- Use it to prepare for a conversation with a licensed clinician.\n"
    "- If you feel very unwell or symptoms are severe, **seek urgent medical care**."
)

def _is_provided(x) -> bool:
    return x is not None and x != 0 and x != 0.0

# ---------------------------
# Educational classification helpers (non-diagnostic)
# ---------------------------
def classify_bp(sys_bp: int, dia_bp: int) -> str:
    if sys_bp <= 0 or dia_bp <= 0:
        return "Not provided."
    if sys_bp < 90 or dia_bp < 60:
        return "Low range"
    if sys_bp < 120 and dia_bp < 80:
        return "Typical range"
    if 120 <= sys_bp <= 129 and dia_bp < 80:
        return "Slightly above typical"
    if 130 <= sys_bp <= 139 or 80 <= dia_bp <= 89:
        return "High range (mild–moderate)"
    if sys_bp >= 140 or dia_bp >= 90:
        return "High range"
    return "Check entries"

def bp_context() -> str:
    return (
        "BP can change due to stress, pain, poor sleep, caffeine, dehydration, and illness. "
        "Clinicians often repeat readings after 5–10 minutes of rest."
    )

def classify_temp(temp_c: float) -> str:
    if temp_c <= 0:
        return "Not provided."
    if temp_c < 36.0:
        return "Below typical"
    if 36.0 <= temp_c <= 37.7:
        return "Typical"
    if 37.8 <= temp_c <= 38.9:
        return "Fever range"
    if temp_c >= 39.0:
        return "High fever range"
    return "Check entries"

def temp_context() -> str:
    return (
        "Fever is the body’s response to infection or inflammation. In Nigeria, clinicians may consider "
        "malaria or respiratory infections depending on symptoms and tests."
    )

def classify_glucose(glucose_mmol: float, fasting: bool) -> str:
    if glucose_mmol <= 0:
        return "Not provided."
    if fasting:
        if glucose_mmol < 3.9:
            return "Low fasting range"
        if 3.9 <= glucose_mmol <= 5.5:
            return "Typical fasting range"
        if 5.6 <= glucose_mmol <= 6.9:
            return "Above typical fasting range"
        if glucose_mmol >= 7.0:
            return "High fasting range"
    else:
        if glucose_mmol < 3.9:
            return "Low range"
        if 3.9 <= glucose_mmol <= 7.7:
            return "Common random range"
        if 7.8 <= glucose_mmol <= 11.0:
            return "Above typical random range"
        if glucose_mmol > 11.0:
            return "High random range"
    return "Check entries"

def glucose_context(fasting: bool) -> str:
    if fasting:
        return "Fasting glucose is best interpreted with context. Clinicians may confirm with repeat testing or HbA1c."
    return "Random glucose depends on recent meals. Clinicians may suggest fasting glucose or HbA1c for clarity."

def classify_pcv(pcv: float, sex: str) -> str:
    if pcv <= 0:
        return "Not provided."
    if sex == "Male":
        low_cut, high_cut = 40.0, 54.0
    elif sex == "Female":
        low_cut, high_cut = 36.0, 48.0
    else:
        low_cut, high_cut = 37.0, 52.0

    if pcv < low_cut:
        return "Below typical"
    if low_cut <= pcv <= high_cut:
        return "Typical"
    if pcv > high_cut:
        return "Above typical"
    return "Check entries"

def pcv_context() -> str:
    return (
        "When PCV is low, clinicians often check nutrition, recent infections (including malaria depending on exposure), "
        "and any history of blood loss. It does not automatically mean something serious, but it deserves review."
    )

def classify_pulse(pulse: int) -> str:
    if pulse <= 0:
        return "Not provided."
    if pulse < 60:
        return "Below typical resting range"
    if 60 <= pulse <= 100:
        return "Typical resting range"
    if pulse > 100:
        return "Above typical resting range"
    return "Check entries"

def pulse_context() -> str:
    return "Pulse can rise with fever, dehydration, pain, anxiety, or recent activity. Clinicians interpret it with symptoms."

# ---------------------------
# Red flag detection (conservative, educational)
# ---------------------------
def red_flags(symptoms_text: str, sys_bp: int, dia_bp: int, temp_c: float, glucose_mmol: float) -> list[str]:
    s = (symptoms_text or "").lower()
    flags = []

    symptom_triggers = [
        ("chest pain", "Chest pain or heavy chest pressure"),
        ("difficulty breathing", "Difficulty breathing"),
        ("shortness of breath", "Shortness of breath"),
        ("faint", "Fainting or repeated fainting"),
        ("confusion", "Confusion or altered mental state"),
        ("seiz", "Seizure / convulsions"),
        ("stroke", "Stroke-like symptoms (face droop, arm weakness, speech trouble)"),
        ("vomit blood", "Vomiting blood"),
        ("black stool", "Black/tarry stool"),
        ("bleeding", "Uncontrolled bleeding"),
    ]
    for key, label in symptom_triggers:
        if key in s:
            flags.append(label)

    if sys_bp > 180 or dia_bp > 120:
        flags.append("Very high blood pressure range (urgent assessment recommended).")
    if (sys_bp > 0 and dia_bp > 0) and (sys_bp < 85 or dia_bp < 55):
        flags.append("Very low blood pressure range, especially if weak/faint (urgent assessment may be needed).")
    if temp_c >= 39.5:
        flags.append("Very high fever (urgent assessment if persistent or with severe symptoms).")
    if glucose_mmol > 13.9:
        flags.append("Very high blood sugar range (urgent assessment if unwell, vomiting, confusion, or dehydrated).")
    if 0 < glucose_mmol < 3.0:
        flags.append("Very low blood sugar range (urgent assessment if shaky, sweaty, confused, faint).")

    return list(dict.fromkeys(flags))

# ---------------------------
# Questions generator
# ---------------------------
def smart_questions(sys_bp: int, dia_bp: int, temp_c: float, pulse: int, pcv: float, glucose_mmol: float, fasting: bool) -> list[str]:
    qs = [
        "Based on my symptoms and examination, what are the main things you are considering?",
        "Which result matters most right now, and which ones can be monitored later?",
        "Should we repeat any readings (BP/temperature) to confirm accuracy?",
        "Do I need more tests? If yes, which ones and when?",
        "What warning signs mean I should return urgently or go to emergency care?",
        "While we investigate, what practical steps should I focus on (hydration, rest, meals, sleep)?",
    ]
    if sys_bp and dia_bp:
        qs.append("Was my blood pressure checked properly (correct cuff size, sitting position, after rest)?")
    if temp_c:
        qs.append("If this is fever, what causes are most likely in my case, and what tests are needed?")
    if pulse:
        qs.append("Is my pulse expected for my condition (fever, pain, anxiety, dehydration)?")
    if pcv:
        qs.append("If my PCV is low, should we check iron deficiency, malaria (if relevant), or bleeding?")
    if glucose_mmol:
        qs.append("Should I do fasting glucose or HbA1c to confirm what this reading means?")
    return qs[:10]

# ---------------------------
# Visit summary builder
# ---------------------------
def build_summary(name: str, age: str, sex: str, symptoms: str,
                  sys_bp: int, dia_bp: int, temp_c: float, pulse: int,
                  pcv: float, glucose: float, fasting: bool) -> str:
    lines = []
    lines.append(f"Patient: {name or 'N/A'} | Age: {age or 'N/A'} | Sex: {sex or 'N/A'}")
    lines.append(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("Symptoms/Concerns:")
    lines.append(f"- {symptoms.strip() if symptoms else 'N/A'}")
    lines.append("")
    lines.append("Values Provided:")
    if sys_bp and dia_bp:
        lines.append(f"- BP: {sys_bp}/{dia_bp} mmHg")
    if pulse:
        lines.append(f"- Pulse: {pulse} bpm")
    if temp_c:
        lines.append(f"- Temperature: {temp_c:.1f} °C")
    if pcv:
        lines.append(f"- PCV: {pcv:.1f} %")
    if glucose:
        lines.append(f"- Glucose: {glucose:.1f} mmol/L ({'fasting' if fasting else 'random'})")
    lines.append("")
    lines.append("Goal for visit:")
    lines.append("- Understand what these values mean in context, confirm what needs repeat testing, and agree next steps.")
    return "\n".join(lines)

# ---------------------------
# UI helpers
# ---------------------------
def status_badge(label: str) -> str:
    # Visual-friendly, neutral wording
    if label in ["Typical range", "Typical", "Typical fasting range", "Common random range", "Typical resting range"]:
        return "✅ Typical"
    if label == "Not provided.":
        return "➖ Not provided"
    if "High" in label or "Low" in label or "Above" in label or "Below" in label or "Fever" in label:
        return "⚠️ Outside usual range"
    return "ℹ️ Check"

def render_card(title: str, value_line: str, classification: str, context: str = ""):
    st.markdown(
        f"""
        <div style="border:1px solid rgba(255,255,255,0.12);
                    border-radius:14px; padding:14px; margin-bottom:10px;">
            <div style="font-size:16px; font-weight:700; margin-bottom:6px;">{title}</div>
            <div style="font-size:14px; margin-bottom:6px;"><b>{value_line}</b></div>
            <div style="font-size:13px; opacity:0.95; margin-bottom:6px;">
                {status_badge(classification)} — {classification}
            </div>
            <div style="font-size:12.5px; opacity:0.85;">
                {context}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------
# Sidebar (UX improvement)
# ---------------------------
with st.sidebar:
    st.header("Quick guide")
    st.write("1) Enter symptoms\n2) Add any values you know\n3) Click **Generate**")
    st.write("You’ll get: explanation, urgent warnings, questions, and a clinic summary.")
    st.divider()
    st.write("**Tip:** If you don’t have lab results, you can still use the doctor questions and summary.")
    st.divider()
    st.caption("Clinic Companion NG is educational and does not replace professional care.")

# ---------------------------
# Hero banner
# ---------------------------
st.markdown(
    """
    <div style="background: linear-gradient(90deg, rgba(15,23,42,1) 0%, rgba(2,132,199,0.25) 100%);
                padding:18px; border-radius:16px; border:1px solid rgba(255,255,255,0.10);">
        <h2 style="margin:0;">🏥 Clinic Companion NG</h2>
        <p style="margin:6px 0 0 0; opacity:0.9;">
            Helping you prepare calmly and confidently for your hospital visit.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")
st.info(DISCLAIMER)

# ---------------------------
# Form
# ---------------------------
with st.form("inputs"):
    st.subheader("Basic details (optional)")
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("Name (optional)")
    with col2:
        age = st.text_input("Age (optional)")
    with col3:
        sex = st.selectbox("Sex (optional)", ["Prefer not to say", "Male", "Female"])

    st.subheader("Symptoms")
    symptoms = st.text_area(
        "Describe symptoms (example: weakness, dizziness, fever, headache, cough, body pain).",
        height=90
    )

    st.subheader("Vitals (enter what you know)")
    c1, c2, c3 = st.columns(3)
    with c1:
        sys_bp = st.number_input("Systolic BP (mmHg)", min_value=0, max_value=300, value=0, step=1)
    with c2:
        dia_bp = st.number_input("Diastolic BP (mmHg)", min_value=0, max_value=200, value=0, step=1)
    with c3:
        pulse = st.number_input("Pulse (bpm)", min_value=0, max_value=250, value=0, step=1)

    c4, c5 = st.columns(2)
    with c4:
        temp_c = st.number_input("Temperature (°C)", min_value=0.0, max_value=45.0, value=0.0, step=0.1)
    with c5:
        pcv = st.number_input("PCV (%)", min_value=0.0, max_value=80.0, value=0.0, step=0.5)

    st.subheader("Blood sugar (optional)")
    c6, c7 = st.columns(2)
    with c6:
        glucose = st.number_input("Glucose (mmol/L)", min_value=0.0, max_value=60.0, value=0.0, step=0.1)
    with c7:
        fasting = st.checkbox("This was a fasting test")

    submitted = st.form_submit_button("Generate Visit Prep")

# ---------------------------
# Results
# ---------------------------
if submitted:
    st.write("")
    st.progress(0.25)
    st.caption("Step 1/4: Reviewing what you entered...")

    if not any([
        (symptoms or "").strip(),
        _is_provided(sys_bp) and _is_provided(dia_bp),
        _is_provided(pulse),
        _is_provided(temp_c),
        _is_provided(pcv),
        _is_provided(glucose),
    ]):
        st.warning("Please enter symptoms or at least one value (BP, temperature, pulse, PCV, or glucose).")
        st.stop()

    st.write("")
    st.progress(0.50)
    st.caption("Step 2/4: What doctors usually look at")

    st.subheader("1️⃣ What doctors usually look at")
    st.write("Here’s a simple, clinic-style view of the values you entered:")

    # Cards layout
    left, right = st.columns(2)

    bp_label = classify_bp(int(sys_bp), int(dia_bp))
    temp_label = classify_temp(float(temp_c))
    pulse_label = classify_pulse(int(pulse))
    pcv_label = classify_pcv(float(pcv), sex)
    glu_label = classify_glucose(float(glucose), bool(fasting))

    with left:
        render_card("🩺 Blood Pressure", f"{int(sys_bp)}/{int(dia_bp)} mmHg" if _is_provided(sys_bp) and _is_provided(dia_bp) else "Not provided",
                    bp_label, bp_context() if bp_label != "Not provided." else "")
        render_card("❤️ Pulse", f"{int(pulse)} bpm" if _is_provided(pulse) else "Not provided",
                    pulse_label, pulse_context() if pulse_label != "Not provided." else "")

    with right:
        render_card("🌡 Temperature", f"{float(temp_c):.1f} °C" if _is_provided(temp_c) else "Not provided",
                    temp_label, temp_context() if temp_label != "Not provided." else "")
        render_card("🧪 PCV", f"{float(pcv):.1f} %" if _is_provided(pcv) else "Not provided",
                    pcv_label, pcv_context() if pcv_label != "Not provided." else "")
        render_card("🍬 Blood Sugar", f"{float(glucose):.1f} mmol/L ({'fasting' if fasting else 'random'})" if _is_provided(glucose) else "Not provided",
                    glu_label, glucose_context(bool(fasting)) if glu_label != "Not provided." else "")

    st.write("")
    st.progress(0.75)
    st.caption("Step 3/4: Checking urgent warning signs and clinic next steps")

    st.subheader("2️⃣ What your doctor may want to check")
    topics = []
    if (symptoms or "").strip():
        topics.append("Timeline of symptoms: when it started, what makes it better/worse, and any medicines or supplements.")
    if _is_provided(sys_bp) and _is_provided(dia_bp):
        if int(sys_bp) < 90 or int(dia_bp) < 60:
            topics.append("Low BP range: hydration, recent illness, standing vs sitting readings, and any BP-lowering medicines.")
        elif int(sys_bp) >= 140 or int(dia_bp) >= 90:
            topics.append("High BP range: repeat BP after rest, stress/sleep, salt intake, family history, and monitoring plan.")
    if _is_provided(temp_c) and float(temp_c) >= 37.8:
        topics.append("Fever range: depending on symptoms, clinicians may consider malaria or respiratory infections and confirm with tests.")
    if _is_provided(pcv):
        if (sex == "Male" and float(pcv) < 40) or (sex == "Female" and float(pcv) < 36) or (sex == "Prefer not to say" and float(pcv) < 37):
            topics.append("Low PCV: nutrition, malaria risk (if relevant), and bleeding history. Clinician may order iron studies or repeat tests.")
    if _is_provided(glucose):
        if (fasting and float(glucose) >= 5.6) or ((not fasting) and float(glucose) >= 7.8):
            topics.append("Glucose above usual range: confirm with fasting glucose or HbA1c and review diet/lifestyle risk factors.")
    if not topics:
        topics.append("If you share more values (or bring your lab paper), your clinician can narrow down the next steps quickly.")

    for t in topics:
        st.write(f"- {t}")

    st.subheader("3️⃣ When to seek urgent care")
    flags = red_flags(symptoms, int(sys_bp), int(dia_bp), float(temp_c), float(glucose))
    if flags:
        st.error("If any of these apply to you, please seek urgent medical care:")
        for f in flags:
            st.write(f"- {f}")
    else:
        st.success("No obvious urgent red flags detected from what you entered. If symptoms worsen, seek care.")

    st.write("")
    st.progress(1.0)
    st.caption("Step 4/4: Questions + clinic summary ready")

    with st.expander("4️⃣ Smart questions to ask your doctor", expanded=True):
        qs = smart_questions(int(sys_bp), int(dia_bp), float(temp_c), int(pulse), float(pcv), float(glucose), bool(fasting))
        for i, q in enumerate(qs, start=1):
            st.write(f"{i}. {q}")

    with st.expander("5️⃣ Short summary for your clinic visit (copy/paste)", expanded=True):
        st.write("You can copy this and show it to your clinician. It saves time and reduces confusion.")
        summary_text = build_summary(
            name=name,
            age=age,
            sex=sex,
            symptoms=symptoms,
            sys_bp=int(sys_bp),
            dia_bp=int(dia_bp),
            temp_c=float(temp_c),
            pulse=int(pulse),
            pcv=float(pcv),
            glucose=float(glucose),
            fasting=bool(fasting),
        )
        st.code(summary_text, language="text")

    st.caption(DISCLAIMER)
    st.write("")
    st.caption("Built with Python + Streamlit. Designed for education and visit preparation, not diagnosis.")
