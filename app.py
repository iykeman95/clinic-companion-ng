import streamlit as st
from datetime import datetime
import html

# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(page_title="Clinic Companion NG", page_icon="🏥", layout="centered")

DISCLAIMER = (
    "⚠️ **Educational use only (not medical advice).**\n\n"
    "- This tool does **not** diagnose illness or recommend treatment.\n"
    "- Do **not** start/stop medicines based on this.\n"
    "- Use it to prepare for a conversation with a licensed clinician.\n"
    "- If you feel very unwell or symptoms are severe, **seek urgent medical care**."
)

def _provided_num(x) -> bool:
    return x is not None and float(x) > 0

def safe_text(s: str) -> str:
    """Escape text that might contain HTML-like characters."""
    return html.escape(s or "").strip()

# ---------------------------
# Educational classification helpers (non-diagnostic)
# ---------------------------
def classify_bp(sys_bp: int, dia_bp: int) -> str:
    if sys_bp <= 0 or dia_bp <= 0:
        return "Not provided"
    # soften to reduce panic: treat 120–124 as near-typical
    if sys_bp < 90 or dia_bp < 60:
        return "Low range"
    if sys_bp < 125 and dia_bp < 80:
        return "Typical / near typical"
    if 125 <= sys_bp <= 129 and dia_bp < 80:
        return "Borderline (monitor)"
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
        return "Not provided"
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

def classify_pulse(pulse: int) -> str:
    if pulse <= 0:
        return "Not provided"
    if pulse < 60:
        return "Below typical resting range"
    if 60 <= pulse <= 100:
        return "Typical resting range"
    if pulse > 100:
        return "Above typical resting range"
    return "Check entries"

def pulse_context() -> str:
    return "Pulse can rise with fever, dehydration, pain, anxiety, or recent activity. Clinicians interpret it with symptoms."

def classify_pcv(pcv: float, sex: str) -> str:
    if pcv <= 0:
        return "Not provided"
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

def classify_glucose(glucose_mmol: float, fasting: bool) -> str:
    if glucose_mmol <= 0:
        return "Not provided"
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

# ---------------------------
# BMI
# ---------------------------
def compute_bmi(height_cm: float, weight_kg: float):
    if height_cm <= 0 or weight_kg <= 0:
        return None
    h_m = height_cm / 100.0
    return weight_kg / (h_m * h_m)

def classify_bmi(bmi: float) -> str:
    if bmi is None:
        return "Not provided"
    if bmi < 18.5:
        return "Lower than typical range"
    if bmi < 25:
        return "Typical range"
    if bmi < 30:
        return "Above typical range"
    return "Higher risk range"

# ---------------------------
# Hydration (educational scoring)
# ---------------------------
def hydration_risk(drinking_less, urine_color, peeing_less, vomiting, diarrhea, heat_sweat, dry_dizzy):
    score = 0
    if drinking_less == "Yes":
        score += 1
    if urine_color == "Yellow":
        score += 1
    if urine_color == "Dark yellow":
        score += 2
    if peeing_less == "Yes":
        score += 2
    if vomiting == "Some":
        score += 1
    if vomiting == "Frequent":
        score += 2
    if diarrhea == "Some":
        score += 1
    if diarrhea == "Frequent":
        score += 2
    if heat_sweat == "Yes":
        score += 1
    if dry_dizzy == "Yes":
        score += 1

    if score >= 6:
        return "High", score
    if score >= 3:
        return "Moderate", score
    return "Low", score

def hydration_advice(level: str):
    if level == "High":
        return [
            "If you cannot keep fluids down, feel faint/confused, or symptoms are worsening, seek urgent medical care.",
            "Small sips frequently can be easier than large amounts at once, especially if nauseated.",
            "If vomiting/diarrhea is present, you can ask your clinician/pharmacist about oral rehydration solutions (ORS).",
        ]
    if level == "Moderate":
        return [
            "Increase fluid intake gradually. Small frequent sips may be easier if nauseated.",
            "Watch for urine becoming lighter and urinating more normally over time.",
            "If fever/heat exposure is present, drink a bit more than usual and rest.",
        ]
    return [
        "Hydration looks okay from what you entered. Keep drinking fluids regularly.",
        "If you’re in heat or sweating heavily, increase fluids a little and monitor urine color.",
    ]

# ---------------------------
# Red flags (conservative)
# ---------------------------
def red_flags(symptoms_text: str, sys_bp: int, dia_bp: int, temp_c: float, glucose_mmol: float,
             vomiting: str, diarrhea: str):
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

    # dehydration + inability to keep fluids down (simple proxy)
    if vomiting == "Frequent" or diarrhea == "Frequent":
        flags.append("Frequent vomiting/diarrhea can cause dehydration. Seek care if you can’t keep fluids down.")

    return list(dict.fromkeys(flags))

# ---------------------------
# Questions generator
# ---------------------------
def smart_questions(has_bp, has_temp, has_pulse, has_pcv, has_glucose, has_hydration, has_bmi):
    qs = [
        "Based on my symptoms and examination, what are the main things you are considering?",
        "Which result matters most right now, and which ones can be monitored later?",
        "Should we repeat any readings (BP/temperature) to confirm accuracy?",
        "Do I need more tests? If yes, which ones and when?",
        "What warning signs mean I should return urgently or go to emergency care?",
        "While we investigate, what practical steps should I focus on (hydration, rest, meals, sleep)?",
    ]
    if has_bp:
        qs.append("Was my blood pressure checked properly (correct cuff size, sitting position, after rest)?")
    if has_temp:
        qs.append("If this is fever, what causes are most likely in my case, and what tests are needed?")
    if has_pulse:
        qs.append("Is my pulse expected for my condition (fever, pain, anxiety, dehydration)?")
    if has_pcv:
        qs.append("If my PCV is low, should we check iron deficiency, malaria (if relevant), or bleeding?")
    if has_glucose:
        qs.append("Should I do fasting glucose or HbA1c to confirm what this reading means?")
    if has_hydration:
        qs.append("Could dehydration be contributing to my symptoms, and what should I monitor at home?")
    if has_bmi:
        qs.append("Does my weight/BMI affect what you want to check (BP, glucose, sleep, lifestyle risks)?")
    return qs[:12]

# ---------------------------
# Summary builder
# ---------------------------
def build_summary(caregiver: bool, patient_name: str, age: str, sex: str,
                  symptoms: str, onset: str, progression: str, main_concern: str,
                  meds: str, supplements: str,
                  sys_bp: int, dia_bp: int, pulse: int, temp_c: float,
                  pcv: float, glucose: float, fasting: bool,
                  height_cm: float, weight_kg: float, bmi: float,
                  hyd_inputs: dict):
    who = "Patient" if not caregiver else "Patient (info provided by caregiver)"
    lines = []
    lines.append(f"{who}: {patient_name or 'N/A'} | Age: {age or 'N/A'} | Sex: {sex or 'N/A'}")
    lines.append(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("Symptoms/Concerns:")
    if symptoms.strip():
        lines.append(f"- {symptoms.strip()}")
    else:
        lines.append("- N/A")
    if onset:
        lines.append(f"- Started: {onset}")
    if progression:
        lines.append(f"- Trend: {progression}")
    if main_concern.strip():
        lines.append(f"- Main worry: {main_concern.strip()}")

    lines.append("")
    lines.append("Medicines / Supplements (as reported):")
    if meds.strip():
        lines.append(f"- Medicines: {meds.strip()}")
    else:
        lines.append("- Medicines: N/A")
    if supplements.strip():
        lines.append(f"- Supplements/herbal: {supplements.strip()}")
    else:
        lines.append("- Supplements/herbal: N/A")

    lines.append("")
    lines.append("Values Provided:")
    if sys_bp > 0 and dia_bp > 0:
        lines.append(f"- BP: {sys_bp}/{dia_bp} mmHg")
    if pulse > 0:
        lines.append(f"- Pulse: {pulse} bpm")
    if temp_c > 0:
        lines.append(f"- Temperature: {temp_c:.1f} °C")
    if pcv > 0:
        lines.append(f"- PCV: {pcv:.1f} %")
    if glucose > 0:
        lines.append(f"- Glucose: {glucose:.1f} mmol/L ({'fasting' if fasting else 'random'})")
    if height_cm > 0 and weight_kg > 0 and bmi is not None:
        lines.append(f"- Height/Weight: {height_cm:.1f} cm / {weight_kg:.1f} kg | BMI: {bmi:.1f} kg/m²")

    # hydration summary (brief)
    if any(v for v in hyd_inputs.values() if v):
        lines.append("")
        lines.append("Hydration notes (as reported):")
        for k, v in hyd_inputs.items():
            if v:
                lines.append(f"- {k}: {v}")

    lines.append("")
    lines.append("Goal for visit:")
    lines.append("- Understand what these findings mean in context, confirm what needs repeat testing, and agree next steps.")
    return "\n".join(lines)

# ---------------------------
# UI helpers (safe HTML card rendering)
# ---------------------------
def status_badge(label: str) -> str:
    typical_markers = {
        "Typical / near typical", "Typical", "Typical fasting range", "Common random range", "Typical resting range", "Typical range"
    }
    if label in typical_markers:
        return "✅ Typical"
    if label == "Not provided":
        return "➖ Not provided"
    if "High" in label or "Low" in label or "Above" in label or "Below" in label or "Fever" in label or "Borderline" in label:
        return "⚠️ Outside usual range"
    return "ℹ️ Check"

def render_card(title: str, value_line: str, classification: str, context: str = ""):
    # Escape everything to prevent any tag leakage
    t = safe_text(title)
    v = safe_text(value_line)
    c = safe_text(classification)
    ctx = safe_text(context)

    st.markdown(
        f"""
        <div style="border:1px solid rgba(255,255,255,0.12);
                    border-radius:14px; padding:14px; margin-bottom:10px;">
            <div style="font-size:16px; font-weight:700; margin-bottom:6px;">{t}</div>
            <div style="font-size:14px; margin-bottom:6px;"><b>{v}</b></div>
            <div style="font-size:13px; opacity:0.95; margin-bottom:6px;">
                {status_badge(classification)} — {c}
            </div>
            <div style="font-size:12.5px; opacity:0.85; line-height:1.35;">
                {ctx}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.header("Quick guide")
    st.write("1) Enter symptoms")
    st.write("2) Add any values you know")
    st.write("3) Click **Generate**")
    st.write("")
    st.write("You’ll get: explanation, urgent warnings, questions, and a clinic summary.")
    st.divider()
    st.caption("Tip: If you don’t have lab results, you can still use the doctor questions and summary.")
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

st.markdown(
    "> It’s normal to feel worried when test results don’t make sense. This tool helps you organize your story and questions — not to diagnose you."
)

# ---------------------------
# Input form
# ---------------------------
with st.form("inputs"):
    st.subheader("Basic details (optional)")
    caregiver = st.checkbox("I am filling this for someone else (caregiver mode)")

    col1, col2, col3 = st.columns(3)
    with col1:
        patient_name = st.text_input("Name (optional)")
    with col2:
        age = st.text_input("Age (optional)")
    with col3:
        sex = st.selectbox("Sex (optional)", ["Prefer not to say", "Male", "Female"])

    st.subheader("Body measurements (optional)")
    b1, b2 = st.columns(2)
    with b1:
        height_cm = st.number_input("Height (cm)", min_value=0.0, max_value=250.0, value=0.0, step=0.5)
    with b2:
        weight_kg = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0, value=0.0, step=0.5)

    st.subheader("Symptoms")
    symptoms = st.text_area(
        "Describe symptoms (example: weakness, dizziness, fever, headache, cough, body pain).",
        height=90
    )

    st.subheader("Symptom timeline (optional)")
    t1, t2 = st.columns(2)
    with t1:
        onset = st.selectbox(
            "When did these symptoms start?",
            ["", "Today", "2–3 days ago", "1–2 weeks ago", "Longer than 2 weeks"]
        )
    with t2:
        progression = st.selectbox(
            "How are the symptoms changing?",
            ["", "Getting better", "Getting worse", "About the same"]
        )
    main_concern = st.text_area("What worries you most right now? (optional)", height=70)

    st.subheader("Medicines & supplements (optional)")
    meds = st.text_input("Current medicines (if any) — e.g., BP meds, painkillers, antibiotics")
    supplements = st.text_input("Supplements/herbal mixtures (if any)")

    st.subheader("Hydration check (optional)")
    h1, h2, h3 = st.columns(3)
    with h1:
        drinking_less = st.selectbox("Drinking less than usual?", ["", "No", "Yes"])
    with h2:
        urine_color = st.selectbox("Urine color (best guess)", ["", "Pale yellow", "Yellow", "Dark yellow"])
    with h3:
        peeing_less = st.selectbox("Urinating less than usual?", ["", "No", "Yes"])

    h4, h5, h6 = st.columns(3)
    with h4:
        vomiting = st.selectbox("Vomiting?", ["", "No", "Some", "Frequent"])
    with h5:
        diarrhea = st.selectbox("Diarrhea?", ["", "No", "Some", "Frequent"])
    with h6:
        heat_sweat = st.selectbox("Heat exposure / heavy sweating?", ["", "No", "Yes"])

    dry_dizzy = st.selectbox("Dry mouth or dizziness?", ["", "No", "Yes"])

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
    g1, g2 = st.columns(2)
    with g1:
        glucose = st.number_input("Glucose (mmol/L)", min_value=0.0, max_value=60.0, value=0.0, step=0.1)
    with g2:
        fasting = st.checkbox("This was a fasting test")

    st.caption("You can leave any field blank if you don’t know it.")
    submitted = st.form_submit_button("Generate Visit Prep")

# ---------------------------
# Results
# ---------------------------
if submitted:
    st.write("")
    st.progress(0.25)
    st.caption("Step 1/4: Reviewing what you entered...")

    has_any = any([
        safe_text(symptoms),
        sys_bp > 0 and dia_bp > 0,
        pulse > 0,
        temp_c > 0,
        pcv > 0,
        glucose > 0,
        height_cm > 0 and weight_kg > 0,
        any([drinking_less, urine_color, peeing_less, vomiting, diarrhea, heat_sweat, dry_dizzy]),
        safe_text(meds),
        safe_text(supplements),
        onset,
        progression,
        safe_text(main_concern),
    ])

    if not has_any:
        st.warning("Please enter symptoms or at least one value (BP, temperature, pulse, PCV, glucose, BMI, or hydration info).")
        st.stop()

    # Jump navigation
    st.markdown(
        """
        **Jump to:**  
        - [Vitals snapshot](#vitals-snapshot)  
        - [Doctor checks](#doctor-checks)  
        - [Urgent care](#urgent-care)  
        - [Questions](#questions)  
        - [Clinic summary](#clinic-summary)
        """
    )

    st.write("")
    st.progress(0.50)
    st.caption("Step 2/4: What doctors usually look at")

    st.markdown('<a name="vitals-snapshot"></a>', unsafe_allow_html=True)
    st.subheader("1️⃣ Vitals snapshot (clinic-style)")

    bmi = compute_bmi(height_cm, weight_kg)
    bp_label = classify_bp(int(sys_bp), int(dia_bp))
    temp_label = classify_temp(float(temp_c))
    pulse_label = classify_pulse(int(pulse))
    pcv_label = classify_pcv(float(pcv), sex)
    glu_label = classify_glucose(float(glucose), bool(fasting))
    bmi_label = classify_bmi(bmi)

    left, right = st.columns(2)

    with left:
        render_card(
            "🩺 Blood Pressure",
            f"{int(sys_bp)}/{int(dia_bp)} mmHg" if sys_bp > 0 and dia_bp > 0 else "Not provided",
            bp_label,
            bp_context() if bp_label != "Not provided" else ""
        )
        render_card(
            "❤️ Pulse",
            f"{int(pulse)} bpm" if pulse > 0 else "Not provided",
            pulse_label,
            pulse_context() if pulse_label != "Not provided" else ""
        )

    with right:
        render_card(
            "🌡 Temperature",
            f"{float(temp_c):.1f} °C" if temp_c > 0 else "Not provided",
            temp_label,
            temp_context() if temp_label != "Not provided" else ""
        )
        render_card(
            "🧪 PCV",
            f"{float(pcv):.1f} %" if pcv > 0 else "Not provided",
            pcv_label,
            pcv_context() if pcv_label != "Not provided" else ""
        )
        render_card(
            "🍬 Blood Sugar",
            f"{float(glucose):.1f} mmol/L ({'fasting' if fasting else 'random'})" if glucose > 0 else "Not provided",
            glu_label,
            glucose_context(bool(fasting)) if glu_label != "Not provided" else ""
        )

    # BMI card (optional)
    if bmi is not None:
        render_card(
            "📏 BMI (Body Mass Index)",
            f"{bmi:.1f} kg/m²",
            bmi_label,
            "BMI is one of many tools clinicians use. It does not tell the whole health story."
        )

    st.write("")
    st.progress(0.75)
    st.caption("Step 3/4: What your doctor may want to check + urgent warnings")

    st.markdown('<a name="doctor-checks"></a>', unsafe_allow_html=True)
    st.subheader("2️⃣ Doctor checks (what clinicians commonly ask next)")

    doctor_checks = []

    # Timeline
    if onset or progression:
        doctor_checks.append("Symptom timeline: when it started and whether it’s getting better/worse/same.")
    else:
        doctor_checks.append("Symptom timeline: when it started, what triggers it, what makes it better/worse.")

    # Hydration context
    if any([drinking_less, urine_color, peeing_less, vomiting, diarrhea, heat_sweat, dry_dizzy]):
        doctor_checks.append("Hydration: intake, vomiting/diarrhea, urine color and frequency, heat/sweating exposure.")
    else:
        doctor_checks.append("Hydration: fluid intake, urine color, vomiting/diarrhea, fever/heat exposure.")

    # Medicines
    doctor_checks.append("Medicines and supplements: BP meds, painkillers, antibiotics, herbs/supplements.")

    # BP
    if sys_bp > 0 and dia_bp > 0:
        if int(sys_bp) < 90 or int(dia_bp) < 60:
            doctor_checks.append("Low BP range: hydration status, standing vs sitting readings, recent illness, medication effects.")
        elif int(sys_bp) >= 140 or int(dia_bp) >= 90:
            doctor_checks.append("High BP range: repeat BP after rest, sleep/stress, salt intake, monitoring plan.")
        else:
            doctor_checks.append("BP interpretation: confirm correct cuff/position and repeat after rest if needed.")

    # Fever
    if temp_c > 0 and float(temp_c) >= 37.8:
        doctor_checks.append("Fever: likely causes in your context (including malaria/respiratory infections) and tests to confirm.")

    # PCV
    if pcv > 0:
        low_male = (sex == "Male" and float(pcv) < 40)
        low_female = (sex == "Female" and float(pcv) < 36)
        low_unsure = (sex == "Prefer not to say" and float(pcv) < 37)
        if low_male or low_female or low_unsure:
            doctor_checks.append("Low PCV: nutrition, malaria risk (if relevant), and bleeding history; consider iron studies/repeat test.")

    # Glucose
    if glucose > 0:
        doctor_checks.append("Glucose: confirm with fasting glucose or HbA1c if needed, depending on context and symptoms.")

    # BMI
    if bmi is not None:
        doctor_checks.append("Weight/BMI: consider lifestyle risks and whether it relates to BP/glucose/sleep patterns.")

    for item in doctor_checks:
        st.write(f"- {item}")

    # Hydration output (educational)
    st.subheader("💧 Hydration check (educational)")
    if any([drinking_less, urine_color, peeing_less, vomiting, diarrhea, heat_sweat, dry_dizzy]):
        level, score = hydration_risk(drinking_less, urine_color, peeing_less, vomiting, diarrhea, heat_sweat, dry_dizzy)

        if level == "High":
            st.error(f"Hydration risk: **{level}** (score {score})")
        elif level == "Moderate":
            st.warning(f"Hydration risk: **{level}** (score {score})")
        else:
            st.success(f"Hydration risk: **{level}** (score {score})")

        st.write("What you can do now (safe steps):")
        for tip in hydration_advice(level):
            st.write(f"- {tip}")
    else:
        st.info("Optional: fill the hydration section to get hydration guidance.")

    st.markdown('<a name="urgent-care"></a>', unsafe_allow_html=True)
    st.subheader("3️⃣ When to seek urgent care")
    flags = red_flags(
        symptoms_text=symptoms,
        sys_bp=int(sys_bp),
        dia_bp=int(dia_bp),
        temp_c=float(temp_c),
        glucose_mmol=float(glucose),
        vomiting=vomiting,
        diarrhea=diarrhea
    )

    if flags:
        st.error("If any of these apply to you, please seek urgent medical care:")
        for f in flags:
            st.write(f"- {f}")
    else:
        st.success("No obvious urgent red flags detected from what you entered. If symptoms worsen, seek care.")

    st.write("")
    st.progress(1.0)
    st.caption("Step 4/4: Questions + clinic summary ready")

    st.markdown('<a name="questions"></a>', unsafe_allow_html=True)
    with st.expander("4️⃣ Smart questions to ask your doctor", expanded=True):
        has_bp = (sys_bp > 0 and dia_bp > 0)
        has_temp = (temp_c > 0)
        has_pulse = (pulse > 0)
        has_pcv = (pcv > 0)
        has_glucose = (glucose > 0)
        has_hyd = any([drinking_less, urine_color, peeing_less, vomiting, diarrhea, heat_sweat, dry_dizzy])
        has_bmi = (bmi is not None)

        qs = smart_questions(has_bp, has_temp, has_pulse, has_pcv, has_glucose, has_hyd, has_bmi)
        for i, q in enumerate(qs, start=1):
            st.write(f"{i}. {q}")

    st.subheader("🧾 What to bring to the clinic (simple checklist)")
    st.write("- Previous test results / hospital cards (if any)")
    st.write("- A list of medicines and supplements you’ve taken recently")
    st.write("- This summary (copy/paste below)")
    st.write("- A trusted person to accompany you if you feel anxious or weak")

    st.markdown('<a name="clinic-summary"></a>', unsafe_allow_html=True)
    with st.expander("5️⃣ Short summary for your clinic visit (copy/paste)", expanded=True):
        st.write("You can copy this and show it to your clinician. It saves time and reduces confusion.")

        hyd_inputs = {
            "Drinking less": drinking_less,
            "Urine color": urine_color,
            "Peeing less": peeing_less,
            "Vomiting": vomiting,
            "Diarrhea": diarrhea,
            "Heat/sweating": heat_sweat,
            "Dry mouth/dizziness": dry_dizzy,
        }

        summary_text = build_summary(
            caregiver=caregiver,
            patient_name=patient_name,
            age=age,
            sex=sex,
            symptoms=symptoms,
            onset=onset,
            progression=progression,
            main_concern=main_concern,
            meds=meds,
            supplements=supplements,
            sys_bp=int(sys_bp),
            dia_bp=int(dia_bp),
            pulse=int(pulse),
            temp_c=float(temp_c),
            pcv=float(pcv),
            glucose=float(glucose),
            fasting=bool(fasting),
            height_cm=float(height_cm),
            weight_kg=float(weight_kg),
            bmi=bmi if bmi is not None else None,
            hyd_inputs=hyd_inputs
        )

        # Copy-friendly display + download
        st.text_area("Clinic summary (copy this):", value=summary_text, height=260)
        st.download_button(
            "Download summary as .txt",
            data=summary_text.encode("utf-8"),
            file_name="clinic_companion_summary.txt",
            mime="text/plain",
        )

    st.caption(DISCLAIMER)
    st.caption("Built with Python + Streamlit. Designed for education and visit preparation, not diagnosis.")
