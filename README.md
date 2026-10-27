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
st.caption("AI-assisted clinical learning")

st.warning(
    "Educational use only. Not a confirmed diagnosis. "
    "Never delay emergency care."
)

st.info(
    "Use fictional or de-identified data only. "
    "Text and images are sent to the AI provider."
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
    labs = st.text_area("Laboratory results and reference ranges")

    imaging_type = st.selectbox(
        "Imaging type",
        ["None", "X-ray", "CT", "MRI", "Ultrasound", "Other"]
    )

    uploaded = st.file_uploader(
        "Upload an image or PDF",
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

    elif uploaded and uploaded.size > 5 * 1024 * 1024:
        st.error("Please upload a file smaller than 5 MB.")

    else:
        try:
            client = Groq(
                api_key=st.secrets["GROQ_API_KEY"]
            )

            prompt = f"""
You are an educational clinical reasoning assistant.
You are not a substitute for a licensed clinician.

Patient age: {age}
Sex: {sex}
Symptoms and duration: {symptoms or "Not provided"}
History and medications: {history or "Not provided"}
Laboratory results: {labs or "Not provided"}
Imaging type: {imaging_type}

Provide:
1. Case summary.
2. Important missing information.
3. Differential diagnoses with supporting and opposing evidence.
4. Dangerous diagnoses that must not be missed.
5. Further assessment or investigations a clinician may consider.
6. Limitations of the supplied data.
7. Red flags requiring urgent or emergency assessment.

Do not claim a definitive diagnosis.
Do not invent findings, reference ranges, or probabilities.
Do not prescribe medications or doses.
State uncertainty clearly.
Use clear headings and bullet points.
A qualified clinician must verify all conclusions.
"""

            content = [
                {"type": "text", "text": prompt}
            ]

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
                            "No selectable text found in this PDF. "
                            "Try uploading a screenshot of the page."
                        )
                        st.stop()

                    content.append({
                        "type": "text",
                        "text": "Extracted PDF text:\n" + pdf_text[:20000]
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

            with st.spinner("Analyzing case..."):
                result = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    max_completion_tokens=1800
                )

            answer = result.choices[0].message.content

            if answer:
                st.subheader("Differential assessment")
                st.markdown(answer)
                st.warning(
                    "Educational output only. Verify with a "
                    "qualified clinician."
                )
            else:
                st.error("No response returned. Please try again.")

        except KeyError:
            st.error("Add GROQ_API_KEY to Streamlit Secrets.")

        except Exception as exc:
            st.error("Analysis failed.")
            st.caption(f"Technical details: {str(exc)[:500]}")
