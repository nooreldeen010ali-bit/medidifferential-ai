
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="MediDifferential AI",
    page_icon="🩺",
    layout="centered"
)

st.title("🩺 MediDifferential AI")
st.caption("Educational clinical decision support")

st.warning(
    "Educational prototype only. Not a confirmed diagnosis. "
    "Seek urgent care for severe or worsening symptoms."
)

st.info(
    "Use fictional data only. Uploaded files are sent to the "
    "AI provider. Do not upload identifiable patient records."
)

with st.form("case_form"):
    age = st.number_input("Age", 0, 120, 24)
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
        "Upload an image or PDF report",
        type=["png", "jpg", "jpeg", "webp", "pdf"]
    )
    submitted = st.form_submit_button(
        "Analyze case", type="primary"
    )

if submitted:
    if not symptoms.strip() and not labs.strip() and uploaded is None:
        st.error("Enter symptoms, laboratory results, or a file.")
    else:
        try:
            client = genai.Client(
                api_key=st.secrets["GEMINI_API_KEY"]
            )

            prompt = f"""
Provide an educational differential diagnosis, not a definitive
diagnosis. Explain supporting and opposing evidence, dangerous
alternatives, missing information, and appropriate next steps.
Do not invent findings or probabilities. Do not prescribe drugs.
State uncertainty and recommend clinician verification.

Age: {age}
Sex: {sex}
Symptoms: {symptoms or "Not provided"}
History and medications: {history or "Not provided"}
Laboratory results: {labs or "Not provided"}
Imaging type: {imaging_type}

This is an educational case. It must not be used alone for
clinical decisions. Identify red flags requiring urgent care.
"""

            contents = [prompt]

            if uploaded is not None:
                if uploaded.size > 10 * 1024 * 1024:
                    st.error("Please upload a file smaller than 10 MB.")
                    st.stop()

                mime = uploaded.type
                if mime not in (
                    "image/png", "image/jpeg",
                    "image/webp", "application/pdf"
                ):
                    st.error("Unsupported file format.")
                    st.stop()

                contents.append(
                    types.Part.from_bytes(
                        data=uploaded.getvalue(),
                        mime_type=mime
                    )
                )

            with st.spinner("Analyzing case..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
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
                    "AI output can be wrong. A qualified clinician "
                    "must verify the findings."
                )
            else:
                st.error("The model returned no text. Try again.")

        except KeyError:
            st.error("GEMINI_API_KEY is missing from Streamlit Secrets.")
        except Exception as exc:
            st.error(
                "Analysis failed. Check API access, quota, model "
                "availability, and Secrets configuration."
            )
            st.caption(str(exc)[:300])
                
