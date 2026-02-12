import streamlit as st
import requests
import os
import json
import pandas as pd

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


st.set_page_config(page_title="AI Resume Scanner", page_icon="📄", layout="wide")

st.title(body="📄 AI-Powered Resume Screening System")
st.markdown("---")


if "batch_id" not in st.session_state:
    st.session_state.batch_id = None


with st.sidebar:
    st.header(body="1. Upload Resume")
    uploaded_files = st.file_uploader(
        "Choose a PDF resume", type="pdf", accept_multiple_files=True
    )

    if st.button(label="Upload & Process", use_container_width=True):
        if uploaded_files:
            with st.spinner(f"Processing {len(uploaded_files)} resumes..."):
                files_payload = [
                    ("files", (f.name, f.getvalue(), "application/pdf"))
                    for f in uploaded_files
                ]
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/upload", files=files_payload
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.batch_id = data.get("batch_id")
                        st.success(
                            f"Uploaded {data['count']} resumes, Batch ID: {st.session_state.batch_id[:8]}..."
                        )
                    else:
                        st.error(f"Upload Failed {response.text}")

                except Exception as e:
                    st.error(f"Error connecting to backend: {e}")

        else:
            st.warning("Please at least one file")


st.header("2. Job analysis")
jd_text = st.text_area(
    "Paste the Job Description here:",
    height=200,
    placeholder="Required: 3+ years Python, FastAPI, Docker...",
)

if st.button(label="Analyze Resume", type="primary"):
    if not st.session_state.batch_id:
        st.error("Please upload a resume first!")

    elif not jd_text.strip():
        st.warning("Please paste a job description.")

    else:
        with st.spinner("Processing..."):
            payload = {
                "job_description": jd_text,
                "session_id": st.session_state.batch_id,
            }
            try:
                res = requests.post(f"{BACKEND_URL}/analyze", json=payload)

                if res.status_code == 200:
                    data = res.json()
                    results = data["results"]

                    if not results:
                        st.warning("No analysis results returned")
                    else:
                        st.success(f"Analyzed {len(results)} candidates successfully")

                    table_data = []
                    for item in results:
                        analysis = item["analysis"]
                        table_data.append(
                            {
                                "Candidate Name": item["filename"],
                                "Match Score": analysis["match_score"],
                                "Verdict": analysis["recommendation"],
                                "Years Exp": analysis["years_experience_actual"],
                                "Missing Skills": ", ".join(
                                    analysis["missing_keywords"]
                                ),
                            }
                        )

                    df = pd.read_json(json.dumps(table_data))

                    st.dataframe(
                        df,
                        column_config={
                            "Match Score": st.column_config.ProgressColumn(
                                label="Match Score",
                                help="0-100 Score",
                                format="%d%%",
                                min_value=0,
                                max_value=100,
                            )
                        },
                        use_container_width=True,
                    )
                    st.markdown("### 🔍 Detailed Breakdown")
                    for item in results:
                        filename = item["filename"]
                        analysis = item["analysis"]

                        with st.expander(
                            f"📄 {filename} - {analysis['match_score']}% Match"
                        ):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Verdict:** {analysis['recommendation']}")
                                st.write(
                                    f"**Experience:** {analysis['years_experience_actual']} Years"
                                )
                            with col2:
                                st.write(f"**Summary:** {analysis['profile_summary']}")

                            st.error(
                                f"Missing: {', '.join(analysis['missing_keywords'])}"
                            )
                            st.success(
                                f"Matching: {', '.join(analysis['matching_keywords'])}"
                            )

                else:
                    st.error(f"Error: {res.text}")

            except Exception as e:
                st.error(f"Connection Error: {e}")
