
import streamlit as st

st.set_page_config(
    page_title="MediDifferential AI",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 MediDifferential AI")
st.caption("Educational Clinical Decision Support")

st.warning(
    "Educational prototype only. Not a confirmed diagnosis. "
    "Seek urgent medical care for severe or rapidly worsening symptoms."
)

st.header("1. Patient Information")

age = st.number_input("Age", min_value=0, max_value=120, value=24)
sex = st.selectbox("Sex", ["Not specified", "Male", "Female"])
symptoms = st.text_area(
    "Symptoms and duration",
    placeholder="Describe symptoms, onset, duration and severity..."
)
history = st.text_area("Medical history and medications")
labs = st.text_area(
    "Laboratory results",
    placeholder="Enter values, units and reference ranges..."
)
uploaded = st.file_uploader(
    "Upload a report or medical image",
    type=["png", "jpg", "jpeg", "pdf"]
)

st.header("2. Preliminary Assessment")

if st.button("Review case"):
    if not symptoms.strip() and not labs.strip() and uploaded is None:
        st.error("Enter symptoms, laboratory results, or upload a file.")
    else:
        st.subheader("Case summary")
        st.write(f"Age: {age}")
        st.write(f"Sex: {sex}")
        st.write("Symptoms:", symptoms or "Not provided")
        st.write("Medical history:", history or "Not provided")
        st.write("Laboratory results:", labs or "Not provided")

        if uploaded:
            st.write("Uploaded file:", uploaded.name)

        st.info(
            "This prototype collects case information only. "
            "AI analysis has not yet been connected. "
            "No diagnosis has been generated."
        )

st.caption(
    "Privacy: use fictional data only. Do not upload identifiable "
    "patient records. This prototype is not for clinical decisions."
)
