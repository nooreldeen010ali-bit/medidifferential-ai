import streamlit as 
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

Patient age: {age}
Sex: {sex}
Symptoms and duration: {symptoms or "Not provided"}
History and medications: {history or "Not provided"}
Laboratory results: {labs or "Not provided"}
Imaging type: {imaging_type}

Give a structured educational assessment:
1. Case summary.
2. Missing information.
3. Differential diagnoses with supporting and opposing evidence.
4. Dangerous diagnoses that must not be missed.
5. Further assessment or investigations a clinician may consider.
6. Limitations of the supplied data.
7. Red flags requiring urgent or emergency assessment.

Do not claim a definitive diagnosis.
Do not invent findings, reference ranges, or probabilities.
Do not prescribe medication or doses.
State uncertainty clearly and use headings and bullet points.
A qualified clinician must verify all conclusions.
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
                    max_completion_tokens=1800
                )

            answer = response.choices[0].message.content

            if answer:
                st.subheader("Differential assessment")
                st.markdown(answer)
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
