import streamlit as st
from google import genai
import base64

st.set_page_config(
    page_title="MediDifferential AI",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 MediDifferential AI")
st.caption("AI-assisted clinical learning and differential diagnosis")

st.warning(
    "Educational prototype only. This is not a confirmed diagnosis. "
    "Never delay emergency care."
)

st.info(
    "Use fictional or properly de-identified data only. "
    "Uploaded files are sent to Google for AI analysis."
)

with st.form("clinical_case"):
    st.subheader("Patient information")

    age = st.number_input(
        "Age (years)", min_value=0, max_value=120, value=24
    )

    sex = st.selectbox(
        "Sex", ["Not specified", "Male", "Female"]
    )

    symptoms = st.text_area(
        "Symptoms and duration",
        placeholder="Onset, duration, severity, associated symptoms..."
    )

    history = st.text_area(
        "Medical history and medications"
    )

    labs = st.text_area(
        "Laboratory results",
        placeholder="Values, units and reference ranges..."
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

    elif uploaded is not None and uploaded.size > 10 * 1024 * 1024:
        st.error("File too large. Please upload a file under 10 MB.")

    else:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            client = genai.Client(api_key=api_key)

            prompt = f"""
You are an educational clinical decision-support assistant.
You are NOT a substitute for a licensed clinician.

Analyze this case cautiously.

Age: {age}
Sex: {sex}
Symptoms and duration: {symptoms or "Not provided"}
Medical history and medications: {history or "Not provided"}
Laboratory results: {labs or "Not provided"}
Imaging type: {imaging_type}

Provide a structured educational assessment with these headings:

1. Case summary
2. Important missing information
3. Differential diagnosis
   - Explain supporting and opposing evidence for each possibility.
4. Dangerous conditions that must not be missed
5. Further assessment or investigations a qualified clinician may consider
6. Interpretation and limitations of supplied laboratory or imaging data
7. Red flags and when urgent or emergency assessment is required

Rules:
- Do not claim a definitive diagnosis.
- Do not invent findings, reference ranges, or probabilities.
- Interpret lab results cautiously if units or reference ranges are missing.
- Describe only findings that can actually be assessed from uploaded material.
- Clearly state uncertainty and the need for professional review.
- Do not prescribe medication or doses.
- Use clear headings, bullets, and clinically appropriate language.
- If evidence is insufficient, say so explicitly.
- This output must not be used alone to make clinical decisions.
"""

            model_input = [
                {"type": "text", "text": prompt}
            ]

            if uploaded is not None:
                mime_type = uploaded.type
                file_data = base64.b64encode(
                    uploaded.getvalue()
                ).decode("utf-8")

                if mime_type == "application/pdf":
                    model_input.append({
                        "type": "document",
                        "data": file_data,
                        "mime_type": mime_type
                    })
                elif mime_type in [
                    "image/png",
                    "image/jpeg",
                    "image/webp"
                ]:
                    model_input.append({
                        "type": "image",
                        "data": file_data,
                        "mime_type": mime_type
                    })
                else:
                    st.error("Unsupported file type.")
                    st.stop()

            with st.spinner("Analyzing the educational case..."):
                response = client.interactions.create(
                    model="gemini-3.8-flash",
                    input=model_input
                )

            result = response.output_text

            if result:
                st.subheader("Differential assessment")
                st.markdown(result)

                st.warning(
                    "AI output may be incorrect or incomplete. "
                    "A qualified clinician must verify all findings."
                )
            else:
                st.error(
                    "The model returned no text. Please try again."
                )

        except KeyError:
            st.error(
                "GEMINI_API_KEY is missing from Streamlit Secrets."
            )

        except Exception as exc:
            st.error("Analysis failed.")
            st.caption(
                f"Technical details: {str(exc)[:600]}"
            )
