
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="MediDifferential AI",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 MediDifferential AI")
st.caption("AI-assisted clinical learning and differential diagnosis")

st.warning(
    "Educational prototype only. Not a medical device or a "
    "confirmed diagnosis. Never delay emergency care."
)

st.info(
    "Use fictional or properly de-identified data only. "
    "Uploaded content is sent to the AI provider for analysis."
)

with st.form("clinical_case"):
    st.subheader("Patient information")

    age = st.number_input(
        "Age (years)", min_value=0, max_value=120, value=24
    )

    sex = st.selectbox(
        "Sex",
        ["Not specified", "Male", "Female"]
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

    else:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]

            client = genai.Client(api_key=api_key)

            prompt = f"""
You are an educational clinical decision-support assistant.
You are NOT a substitute for a licensed clinician.

Analyze the following case cautiously.

Age: {age}
Sex: {sex}
Symptoms and duration: {symptoms or "Not provided"}
Medical history and medications: {history or "Not provided"}
Laboratory results: {labs or "Not provided"}
Imaging type: {imaging_type}

Instructions:
1. Summarize the case and identify missing information.
2. Provide a differential diagnosis, not a definitive diagnosis.
3. For each possibility, explain supporting and opposing evidence.
4. Discuss important dangerous diagnoses that may need exclusion.
5. Suggest appropriate clinical assessment or investigations
   for a qualified clinician to consider.
6. Interpret laboratory results only when units and reference
   ranges are available; mention relevant limitations.
7. For imaging, describe only visible findings you can assess.
   State uncertainty and recommend professional radiology review.
8. Do not invent findings, reference ranges, or probabilities.
9. Explain when urgent or emergency assessment is needed.
10. If evidence is insufficient, say so explicitly.
11. Do not prescribe treatment or medication doses.
12. Format the answer with clear headings and bullet points.

This output is educational and must not be used alone
to make clinical decisions.
"""

            contents = [prompt]

            if uploaded is not None:
                if uploaded.size > 10 * 1024 * 1024:
                    st.error("File too large. Please use a file under 10 MB.")
                    st.stop()

                mime_type = uploaded.type

                if mime_type not in [
                    "image/png",
                    "image/jpeg",
                    "image/webp",
                    "application/pdf"
                ]:
                    st.error("Unsupported file type.")
                    st.stop()

                file_part = types.Part.from_bytes(
                    data=uploaded.getvalue(),
                    mime_type=mime_type
                )

                contents.append(file_part)

            with st.spinner("Analyzing the educational case..."):
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=2500
                    )
                )

            if response.text:
                st.subheader("Differential assessment")
                st.markdown(response.text)

                st.warning(
                    "AI output may be incorrect or incomplete. "
                    "A qualified clinician must verify all findings."
                )
            else:
                st.error(
                    "The model returned no text. Try again or "
                    "check the model and API configuration."
                )

        except KeyError:
            st.error(
                "GEMINI_API_KEY is missing from Streamlit Secrets."
            )

        except Exception as exc:
            st.error(
                "Analysis failed. Check the API key, model access, "
                "internet connection, and API quota."
            )
            st.caption(f"Technical details: {str(exc)[:400]}")
            
