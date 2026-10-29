import streamlit as st 
import base64
from groq import Groq
from pypdf import PdfReader
from io import BytesIO

st.set_page_config(
    page_title="MediDifferential AI",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 MediDifferential AI")
st.caption("AI-assisted clinical learning and differential diagnosis")

st.warning(
    "Educational prototype only. Not a confirmed diagnosis. "
    "Never delay emergency care."
)

st.info(
    "Use fictional or de-identified data only. "
    "Uploaded images and case details are sent to the AI provider."
)

st.markdown("""
<style>
    .stApp {
        background-color: #f4f8fc;
    }

    h1, h2, h3 {
        color: #123b63;
    }

    [data-testid="stForm"] {
        background-color: white;
        padding: 1.2rem;
        border-radius: 16px;
        border: 1px solid #d8e5f0;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        background-color: #1769aa;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        min-height: 44px;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #0f4f85;
        color: white;
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    section[data-testid="stSidebar"] {
        background-color: #eaf2fa;
    }
</style>
""", unsafe_allow_html=True)

with st.form("clinical_case"):
    st.subheader("Patient information")

    age = st.number_input(
        "Age (years)", min_value=0, max_value=120, value=24
    )
    sex = st.selectbox(
        "Sex", ["Not specified", "Male", "Female"]
    )
    symptoms = st.text_area("Symptoms and duration")
    history = st.text_area("Medical history and medications")
    labs = st.text_area("Laboratory results and units")
    
    
    st.subheader("Vital Signs")

    col1, col2 = st.columns(2)

    with col1:
        temperature = st.number_input(
            "Temperature (°C)",
            min_value=30.0,
            max_value=45.0,
            value=37.0,
            step=0.1
        )

        heart_rate = st.number_input(
            "Heart Rate (beats/min)",
            min_value=0,
            max_value=250,
            value=80
        )

        systolic_bp = st.number_input(
            "Systolic BP (mmHg)",
            min_value=0,
            max_value=300,
            value=120
        )

    with col2:
        respiratory_rate = st.number_input(
            "Respiratory Rate (/min)",
            min_value=0,
            max_value=80,
            value=16
        )

        spo2 = st.number_input(
            "SpO₂ (%)",
            min_value=0,
            max_value=100,
            value=98
        )

        diastolic_bp = st.number_input(
            "Diastolic BP (mmHg)",
            min_value=0,
            max_value=200,
            value=80
        )

    examination = st.text_area(
        "Clinical Examination",
        placeholder="Abdominal tenderness, guarding, rebound, "
                    "chest findings, neurological findings..."
        )
    

    imaging_type = st.selectbox(
        "Imaging type",
        ["None", "X-ray", "CT", "MRI", "Ultrasound", "Other"]
    )

    uploaded = st.file_uploader(
        "Upload an image or PDF report",
        type=["png", "jpg", "jpeg", "webp", "pdf"]
    )

    submitted = st.form_submit_button(
        "Analyze case",
        type="primary",
        use_container_width=True
    )

if submitted:
    if not symptoms.strip() and not labs.strip() and uploaded is None:
        st.error("Enter symptoms, lab results, or upload a file.")

    elif uploaded is not None and uploaded.size > 5 * 1024 * 1024:
        st.error("Please upload a file smaller than 5 MB.")

    else:
        try:
            api_key = st.secrets["GROQ_API_KEY"].strip()
            client = Groq(api_key=api_key)

            prompt = f"""
You are an educational clinical reasoning assistant.
You are not a substitute for a licensed clinician.

PATIENT CASE
Age: {age}
Sex: {sex}
Symptoms and duration: {symptoms or "Not provided"}
Medical history and medications: {history or "Not provided"}
Laboratory results: {labs or "Not provided"}
Imaging type: {imaging_type}
Temperature: {temperature} °C
Heart rate: {heart_rate} beats/min
Blood pressure: {systolic_bp}/{diastolic_bp} mmHg
Respiratory rate: {respiratory_rate}/min
SpO2: {spo2}%
Clinical examination: {examination or "Not provided"}

CLINICAL REASONING RULES 
ADDITIONAL EVIDENCE RULES:

- Never infer or invent laboratory findings that were not explicitly provided.
- Do not claim bandemia unless a band count or differential result explicitly supports it.
- Clearly distinguish observed findings from possible interpretations.
- Do not state that a clinical sign is present unless it was documented.
- If information is missing, write "Not provided" instead of guessing.
- Avoid overconfident language such as "textbook" or "strongly confirms" when the diagnosis has not been verified.
- Check spelling and medical terminology before producing the final answer.
1. CASE SUMMARY
Summarize the key symptoms, vital signs, examination findings,
and abnormal laboratory results. Do not invent missing values.

2. PRIORITIZED DIFFERENTIAL DIAGNOSIS
List up to FIVE clinically relevant diagnoses, ordered by
compatibility with the available evidence.

For each diagnosis, provide:
- Supporting evidence.
- Opposing evidence, if genuinely present.
- Missing information that would help distinguish it.
- A brief explanation of its clinical relevance.

Do not invent numerical probabilities.
Do not add unlikely diagnoses merely to fill the list.
Clearly distinguish leading possibilities from dangerous
conditions that must be excluded.

3. MISSING DATA
Missing information is NOT evidence against a diagnosis.
Explicitly label unavailable findings as "not provided".
Never assume that an examination finding is absent simply
because it was not reported.

4. CLINICAL SCORES
Do not calculate Alvarado, CURB-65, Wells, or other scores
unless all required inputs are available and the score is
appropriate for the case.
If information is incomplete, list the missing components
instead of guessing a score.

5. MUST-NOT-MISS CONDITIONS
Include dangerous alternatives relevant to this presentation.
Explain their specific warning signs and why they matter.
Do not list remote or unrelated emergencies without a reason.

6. INVESTIGATIONS
Suggest investigations a qualified clinician may consider.
Explain what each investigation could clarify.
Consider clinical urgency, patient characteristics,
local protocols, and limitations.
Do not describe one imaging test as universally mandatory
or universally the best choice for every patient.

7. LABORATORY INTERPRETATION
Use supplied values and units accurately.
Do not invent reference ranges.
Interpret results in clinical context and state limitations.

8. IMAGE AND DOCUMENT LIMITATIONS
Describe only findings that can actually be assessed.
If a file cannot be interpreted reliably, state this clearly.
Recommend appropriate professional review.

9. FINAL SUMMARY
End with:
- Leading diagnostic consideration.
- Important alternatives.
- Most important missing information.
- Appropriate urgency of assessment.

SAFETY
Do not claim a confirmed diagnosis.
Do not prescribe medications or doses.
Do not invent clinical findings, calculations, or probabilities.
Do not confuse missing evidence with evidence against disease.
Do not let educational analysis delay emergency assessment.
A qualified clinician must verify all conclusions.

Use concise headings and bullet points.
This is educational support, not a replacement for clinical care.
ADDITIONAL RULES:
- Keep the differential diagnosis focused on the 3 most relevant possibilities.
- Put the leading diagnosis first and explain why.
- Separate urgent red flags from routine follow-up.
- Explain medical terms simply for medical students.
- Use a concise comparison table when useful.
- Avoid repeating the same information.
"""



            content = [{"type": "text", "text": prompt}]

            if uploaded is not None:
                file_bytes = uploaded.getvalue()
                mime = uploaded.type

                if mime == "application/pdf":
                    reader = PdfReader(BytesIO(file_bytes))
                    pdf_text = "\n".join(
                        page.extract_text() or ""
                        for page in reader.pages
                    )

                    if not pdf_text.strip():
                        st.error(
                            "This PDF has no extractable text. "
                            "Try a text-based PDF or upload a page image."
                        )
                        st.stop()

                    content.append({
                        "type": "text",
                        "text": "PDF report text:\n" + pdf_text[:15000]
                    })

                elif mime in [
                    "image/png", "image/jpeg", "image/webp"
                ]:
                    encoded = base64.b64encode(
                        file_bytes
                    ).decode("utf-8")

                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{encoded}"
                        }
                    })

                else:
                    st.error("Unsupported file type.")
                    st.stop()

            with st.spinner("Analyzing the case..."):
                response = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    max_completion_tokens=800
                )

            answer = response.choices[0].message.content

            if answer:
                st.subheader("Differential assessment")
                st.markdown(
    answer.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n"),
    unsafe_allow_html=False
                )
                st.warning(
                    "Educational output only. A qualified clinician "
                    "must verify the findings and conclusions."
                )
            else:
                st.error("No response returned. Please try again.")

        except KeyError:
            st.error(
                "GROQ_API_KEY is missing from Streamlit Secrets. "
                "Check the secret name and save it."
            )

        except Exception as exc:
            st.error("Analysis failed.")
            st.caption(f"Technical details: {str(exc)[:500]}")
