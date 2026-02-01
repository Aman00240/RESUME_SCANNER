import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


st.set_page_config(page_title="AI Resume Scanner", page_icon="📄", layout="wide")

st.title(body="📄 AI-Powered Resume Screening System")
st.markdown("---")


if "session_id" not in st.session_state:
    st.session_state.session_id = None


with st.sidebar:
    st.header(body="1. Upload Resume")
    uploaded_file = st.file_uploader("Choose a PDF resume", type="pdf")

    if st.button(label="Upload & Process", use_container_width=True):
        if uploaded_file:
            with st.spinner(text="Processing PDF.."):
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "application/pdf",
                    )
                }
                try:
                    response = requests.post(f"{BACKEND_URL}/upload", files=files)

                    if response.status_code == 200:
                        st.session_state.session_id = response.json().get("session_id")
                        st.success(f"Uploaded ID:{st.session_state.session_id[:8]}...")
                    else:
                        st.error(f"Upload Failed {response.text}")

                except Exception as e:
                    st.error(f"Error connecting to backend: {e}")

        else:
            st.warning("Please select a file first")


st.header("2. Job analysis")
jd_text = st.text_area(
    "Paste the Job Description here:",
    height=250,
    placeholder="Required: 3+ years Python, FastAPI, Docker...",
)

if st.button(label="Analyze Resume", type="primary"):
    if not st.session_state.session_id:
        st.error("Please upload a resume first!")

    elif not jd_text.strip():
        st.warning("Please paste a job description.")

    else:
        with st.spinner("Processing..."):
            payload = {
                "job_description": jd_text,
                "session_id": st.session_state.session_id,
            }
            try:
                res = requests.post(f"{BACKEND_URL}/analyze", json=payload)

                if res.status_code == 200:
                    data = res.json()

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Match Score", f"{data['match_score']}%")

                    with col2:
                        verdict = data["recommendation"]

                        if verdict == "Strong Match":
                            st.success(f"Verdict:**{verdict}**")
                        elif verdict == "Reject":
                            st.error(f"Verdict: **{verdict}**")
                        else:
                            st.info(f"Verdict: **{verdict}**")

                    with col3:
                        st.write(
                            f"**Experience:** {data['years_experience_actual']} (Req: {data['years_experience_required']})"
                        )

                    st.markdown("---")

                    k_col1, k_col2 = st.columns(2)
                    with k_col1:
                        st.success("Matching Keywords:")
                        st.write(
                            ", ".join(data["matching_keywords"])
                            if data["matching_keywords"]
                            else None
                        )
                    with k_col2:
                        st.error("Missing Keywords")
                        st.write(
                            ", ".join(data["missing_keywords"])
                            if data["missing_keywords"]
                            else "None"
                        )

                    st.subheader("Executive Summary")
                    st.info(data["profile_summary"])

                else:
                    st.error(f"Error: {res.json().get('detail', 'Unknown Error')}")

            except Exception as e:
                st.error(f"Connection Error: {e}")
