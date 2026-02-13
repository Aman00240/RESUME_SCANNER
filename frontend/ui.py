import streamlit as st
import requests
import os
import json
import pandas as pd

if "BACKEND_URL" in st.secrets:
    BACKEND_URL = st.secrets["BACKEND_URL"]
else:
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
st.set_page_config(page_title="AI Resume Scanner", page_icon="📄", layout="wide")

st.title(body="AI Resume Screening System")
st.markdown("---")


if "batch_id" not in st.session_state:
    st.session_state.batch_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None


with st.sidebar:
    st.header(body="Upload Resume")
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
            st.warning("Please select at least one file")


st.header("Job analysis")
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
            try:
                payload = {
                    "job_description": jd_text,
                    "session_id": st.session_state.batch_id,
                }
                res = requests.post(f"{BACKEND_URL}/analyze", json=payload)
                if res.status_code == 200:
                    st.session_state.analysis_results = res.json()["results"]
                else:
                    st.error(f"Error: {res.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")

if st.session_state.analysis_results:
    st.success("Analysis Complete!")
    results = st.session_state.analysis_results

    table_data = []
    for item in results:
        analysis = item["analysis"]
        table_data.append(
            {
                "Candidate Name": item["filename"],
                "Match Score": analysis["match_score"],
                "Verdict": analysis["recommendation"],
                "Years Exp": analysis["years_experience_actual"],
                "Missing Skills": ", ".join(analysis["missing_keywords"]),
            }
        )

    df = pd.read_json(json.dumps(table_data))
    st.dataframe(
        df,
        column_config={
            "Match Score": st.column_config.ProgressColumn(
                format="%d%%", min_value=0, max_value=100
            )
        },
        use_container_width=True,
    )

    st.markdown("### 🔍 Detailed Breakdown")

    for item in results:
        filename = item["filename"]
        analysis = item["analysis"]
        resume_id = f"{st.session_state.batch_id}||{filename}"

        with st.expander(f"📄 {filename} - {analysis['match_score']}% Match"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Verdict:** {analysis['recommendation']}")
                st.write(f"**Experience:** {analysis['years_experience_actual']} Years")
            with c2:
                st.write(f"**Summary:** {analysis['profile_summary']}")

            st.error(f"Missing: {', '.join(analysis['missing_keywords'])}")
            st.success(f"Matching: {', '.join(analysis['matching_keywords'])}")

            st.markdown("---")
            st.subheader("💬 Chat with Resume")

            chat_container = st.container()

            with chat_container:
                col_input, col_btn = st.columns([4, 1])

                with col_input:
                    q_input = st.text_input(
                        "Ask a question:",
                        key=f"input_{filename}",
                        placeholder="e.g. Does he know SQL?",
                    )

                with col_btn:
                    st.write("")
                    st.write("")
                    ask_click = st.button("Ask", key=f"btn_{filename}")

                if ask_click and q_input:
                    with st.spinner("Thinking..."):
                        try:
                            chat_payload = {
                                "resume_id": resume_id,
                                "question": q_input,
                                "job_description": jd_text,
                            }
                            api_res = requests.post(
                                f"{BACKEND_URL}/chat", json=chat_payload
                            )
                            if api_res.status_code == 200:
                                ans = api_res.json()["answer"]
                                st.session_state.chat_history[filename] = ans
                            else:
                                st.error(f"API Error: {api_res.text}")
                        except Exception as e:
                            st.error(f"Conn Error: {e}")

                # Show Answer from History
                if filename in st.session_state.chat_history:
                    st.info(f"🤖 **Answer:** {st.session_state.chat_history[filename]}")
