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
    # Helps us treat 0/0.0 as "not provided"
    return x is not None and x != 0 and x != 0.0

# ---------------------------
# Educational classification helpers (non-diagnostic)
# ---------------------------
def classify_bp(sys_bp: int, dia_bp: int) -> str:
    if sys_bp <= 0 or dia_bp <= 0:
        return "Not provided or invalid entry."
    if sys_bp < 90 or dia_bp < 60:
        return "Low blood pressure range."
    if sys_bp < 120 and dia_bp < 80:
        return "Typical range."
    if 120 <= sys_bp <= 129 and dia_bp < 80:
        return "Slightly above typical (often called 'elevated')."
    if 130 <= sys_bp <= 139 or 80 <= dia_bp <= 89:
        return "High blood pressure range (mild to moderate)."
    if sys_bp >= 140 or dia_bp >= 90:
        return "High blood pressure range."
    return "Check entries."

def bp_context(sys_bp: int, dia_bp: int) -> str:
    if sys_bp <= 0 or dia_bp <= 0:
        return ""
    return (
        "Blood pressure can change due to stress, pain, poor sleep, caffeine, dehydration, and illness. "
        "Doctors often repeat readings after you rest for 5–10 minutes."
    )

def classify_temp(temp_c: float) -> str:
    if temp_c <= 0:
        return "Not provided or invalid entry."
    if temp_c < 36.0:
        return "Below typical range."
    if 36.0 <= temp_c <= 37.7:
        return "Typical range."
    if 37.8 <= temp_c <= 38.9:
        return "Fever range."
    if temp_c >= 39.0:
        return "High fever range."
    return "Check entry."

def temp_context(temp_c: float) -> str:
    if temp_c <= 0:
        return ""
    return (
        "Fever is the body’s response to infection or inflammation. In Nigeria, clinicians may consider things like "
        "malaria or respiratory infections depending on symptoms and test results."
    )

def classify_glucose(glucose_mmol: float, fasting: bool) -> str:
    if glucose_mmol <= 0:
        return "Not provided or invalid entry."

    # Educational ranges (labs differ; not diagnostic)
    if fasting:
        if glucose_mmol < 3.9:
            return "Low fasting range."
        if 3.9 <= glucose_mmol <= 5.5:
            return "Typical fasting range."
        if 5.6 <= glucose_mmol <= 6.9:
            return "Above typical fasting range."
        if glucose_mmol >= 7.0:
            return "High fasting range."
    else:
        if glucose_mmol < 3.9:
            return "Low range."
        if 3.9 <= glucose_mmol <= 7.7:
            return "Common random range."
        if 7.8 <= glucose_mmol <= 11.0:
            return "Above typical random range."
        if glucose_mmol > 11.0:
            return "High random range."

    return "Check entry."

def glucose_context(glucose_mmol: float, fasting: bool) -> str:
    if glucose_mmol <= 0:
        return ""
    if fasting:
        return (
            "Fasting glucose is best interpreted with context (illness, stress, medications). "
            "Doctors may confirm with a repeat test or HbA1c."
        )
    return (
        "Random glucose depends on what you ate recently and how long ago. "
        "Doctors may suggest fasting glucose or HbA1c for clarity."
    )

def classify_pcv(pcv: float, sex: str) -> str:
    if pcv <= 0:
        return "Not provided or invalid entry."

    # Conservative adult ranges (varies by lab; educational)
    if sex == "Male":
        low_cut, high_cut = 40.0, 54.0
    elif sex == "Female":
        low_cut, high_cut = 36.0, 48.0
    else:
        low_cut, high_cut = 37.0, 52.0

    if pcv < low_cut:
        return "Below typical range."
    if low_cut <= pcv <= high_cut:
        return "Typical range."
    if pcv > high_cut:
        return "Above typical range."
    return "Check entry."

def pcv_context(pcv: float) -> str:
    if pcv <= 0:
        return ""
    return (
        "When PCV is low, doctors often check nutrition, recent infections (including malaria depending on exposure), "
        "and any history of blood loss. It does not automatically mean something serious, but it deserves review."
    )

def classify_pulse(pulse: int) -> str:
    if pulse <= 0:
        return "Not provided or invalid entry."
    if pulse < 60:
        return "Below typical resting range."
    if 60 <= pulse <= 100:
        return "Typical resting range."
    if pulse > 100:
        return "Above typical resting range."
    return "Check entry."

def pulse_context(pulse: int) -> str:
    if pulse <= 0:
        return ""
    return (
        "Pulse can rise with fever, dehydration, pain, anxiety, or recent activity. "
        "Doctors interpret it together with symptoms and temperature."
    )

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
        ("severe headache", "Severe headache with weakness/vision changes"),
        ("vomit blood", "Vomiting blood"),
        ("black stool", "Black/tarry stool"),
        ("bleeding", "Uncontrolled bleeding"),
    ]
    for key, label in symptom_triggers:
        if key in s:
            flags.append(label)

    # Vitals/lab red flags (conservative thresholds)
    if sys_bp > 180 or dia_bp > 120:
        flags.append("Very high blood pressure range (urgent assessment recommended).")
    if (sys_bp > 0 and dia_bp > 0) and (sys_bp < 85 or dia_bp < 55):
        flags.append("Very low blood pressure range, especially if you feel weak/faint (urgent assessment may be needed).")
    if temp_c >= 39.5:
        flags.append("Very high fever (urgent assessment if persistent or with severe symptoms).")
    if glucose_mmol > 13.9:
        flags.append("Very high blood sugar range (urgent assessment if unwell, vomiting, confusion, or dehydrated).")
    if 0 < glucose_mmol < 3.0:
        flags.append("Very low blood sugar range (urgent assessment if shaky, sweaty, confused, faint).")

    # de-duplicate while preserving order
    return list(dict.fromkeys(flags))

# ---------------------------
# Doctor questions generator
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
        qs.append("Is my pulse expected for my current condition (fever, pain, anxiety, dehydration)?")

    if pcv:
        qs.append("If my PCV is low, should we check for iron deficiency, malaria (if relevant), or bleeding?")

    if glucose_mmol:
        if fasting:
            qs.append("Is this fasting glucose level concerning? Should I do HbA1c or repeat fasting glucose?")
        else:
            qs.append("Since this is random glucose, should I do fasting glucose or HbA1c for clarity?")

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
# UI
# ---------------------------
st.title("🏥 Clinic Companion NG")
st.write(
    "Prepare better for your hospital visit.\n\n"
    "Enter your symptoms and any results you already have. "
    "This tool explains common checks doctors do and helps you know what to ask during your visit."
)
st.info(DISCLAIMER)

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

if submitted:
    st.divider()

    # Guardrail: if user provided nothing, guide them politely
    if not any([
        _is_provided(sys_bp) and _is_provided(dia_bp),
        _is_provided(pulse),
        _is_provided(temp_c),
        _is_provided(pcv),
        _is_provided(glucose),
        (symptoms or "").strip()
    ]):
        st.warning("Please enter at least symptoms or one value (like BP, temperature, PCV, pulse, or glucose).")
        st.stop()

    # 1) What doctors usually look at
    st.subheader("1️⃣ What doctors usually look at")
    st.write("Based on what you entered, here is how clinicians often think about these values in everyday practice:")

    if _is_provided(sys_bp) and _is_provided(dia_bp):
        st.write(f"**Blood Pressure:** {int(sys_bp)}/{int(dia_bp)} mmHg → {classify_bp(int(sys_bp), int(dia_bp))}")
        st.caption(bp_context(int(sys_bp), int(dia_bp)))

    if _is_provided(pulse):
        st.write(f"**Pulse:** {int(pulse)} bpm → {classify_pulse(int(pulse))}")
        st.caption(pulse_context(int(pulse)))

    if _is_provided(temp_c):
        st.write(f"**Temperature:** {float(temp_c):.1f} °C → {classify_temp(float(temp_c))}")
        st.caption(temp_context(float(temp_c)))

    if _is_provided(pcv):
        st.write(f"**PCV:** {float(pcv):.1f}% → {classify_pcv(float(pcv), sex)}")
        st.caption(pcv_context(float(pcv)))

    if _is_provided(glucose):
        st.write(f"**Glucose:** {float(glucose):.1f} mmol/L ({'fasting' if fasting else 'random'}) → {classify_glucose(float(glucose), bool(fasting))}")
        st.caption(glucose_context(float(glucose), bool(fasting)))

    if not any([
        _is_provided(sys_bp) and _is_provided(dia_bp),
        _is_provided(pulse),
        _is_provided(temp_c),
        _is_provided(pcv),
        _is_provided(glucose),
    ]):
        st.info("You didn’t enter any vitals/lab values. That’s okay. You can still use the questions and summary.")

    # 2) What your doctor may want to check
    st.subheader("2️⃣ What your doctor may want to check")
    topics = []

    if (symptoms or "").strip():
        topics.append("Your clinician will likely ask about when the symptoms started, what makes them better/worse, and any medications or supplements.")

    if _is_provided(sys_bp) and _is_provided(dia_bp):
        if int(sys_bp) < 90 or int(dia_bp) < 60:
            topics.append("Low BP range: doctors often check hydration, recent illness, standing vs sitting readings, and any medications that can lower BP.")
        elif int(sys_bp) >= 140 or int(dia_bp) >= 90:
            topics.append("High BP range: clinicians often repeat BP, ask about stress/sleep, salt intake, family history, and may recommend monitoring.")

    if _is_provided(temp_c) and float(temp_c) >= 37.8:
        topics.append("Fever range: in Nigeria, clinicians may consider infections like malaria or respiratory infections depending on symptoms and tests.")

    if _is_provided(pcv) and float(pcv) > 0:
        if sex == "Male" and float(pcv) < 40:
            topics.append("Low PCV: doctors often check nutrition, malaria risk (if relevant), and any bleeding history.")
        elif sex == "Female" and float(pcv) < 36:
            topics.append("Low PCV: doctors often check nutrition, menstrual history, malaria risk (if relevant), and any bleeding history.")
        elif sex == "Prefer not to say" and float(pcv) < 37:
            topics.append("Low PCV: doctors often check nutrition, infection risk, and any bleeding history.")
        elif float(pcv) > 54:
            topics.append("High PCV range can happen with dehydration; clinicians may check hydration status and repeat if needed.")

    if _is_provided(glucose) and float(glucose) > 0:
        if (fasting and float(glucose) >= 5.6) or ((not fasting) and float(glucose) >= 7.8):
            topics.append("Glucose above typical range: doctors may confirm with fasting glucose or HbA1c, and ask about diet, weight changes, and family history.")

    if not topics:
        topics.append("If you share a bit more (symptoms, BP, temperature, PCV, glucose), your clinician can narrow down what to check next.")

    st.write("\n".join([f"- {t}" for t in topics]))

    # 3) When to seek urgent care
    st.subheader("3️⃣ When to seek urgent care")
    flags = red_flags(symptoms, int(sys_bp), int(dia_bp), float(temp_c), float(glucose))
    if flags:
        st.error("If any of the following apply to you, please seek urgent medical care:")
        st.write("\n".join([f"- {f}" for f in flags]))
    else:
        st.success("No obvious urgent red flags detected from what you entered. If symptoms worsen, seek care.")

    # 4) Smart questions
    st.subheader("4️⃣ Smart questions to ask your doctor")
    qs = smart_questions(int(sys_bp), int(dia_bp), float(temp_c), int(pulse), float(pcv), float(glucose), bool(fasting))
    st.write("\n".join([f"{i+1}. {q}" for i, q in enumerate(qs)]))

    # 5) Summary
    st.subheader("5️⃣ Short summary for your clinic visit")
    st.write("You can copy this summary and show it to your doctor. It helps save time and ensures nothing important is missed.")
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
