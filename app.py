import streamlit as st
import pandas as pd
import os
import tempfile

from pipeline import process_resume

st.set_page_config(page_title="Deterministic ATS Leaderboard", layout="wide", page_icon="🚀")

st.title("Automated Resume Extraction & Ranking Engine")
st.markdown("Deterministic scoring. Explainable AI. Zero bias.")

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Configure Scoring Weights")
st.sidebar.markdown("Adjust priorities based on job requirements.")

with st.sidebar.expander("Adjust Weights (%)", expanded=False):
    w_internships = st.slider("Internships", 0, 40, 20)
    w_skills = st.slider("Skills & Certs", 0, 40, 20)
    w_projects = st.slider("Projects", 0, 40, 15)
    w_cgpa = st.slider("CGPA", 0, 30, 10)
    w_achievements = st.slider("Achievements", 0, 30, 10)
    w_experience = st.slider("Experience", 0, 30, 5)
    w_extra = st.slider("Extra-curricular", 0, 20, 5)
    w_degree = st.slider("Degree Type", 0, 10, 3)
    w_lang = st.slider("Language", 0, 10, 3)
    w_online = st.slider("Online Presence", 0, 10, 3)
    # Bumped the last two from 2 to 3 to fix the prompt's 98% math error
    w_college = st.slider("College Tier", 0, 10, 3)
    w_school = st.slider("School Marks", 0, 10, 3)

custom_weights = {
    "internships": w_internships,
    "skills": w_skills,
    "projects": w_projects,
    "cgpa_score": w_cgpa,
    "achievements": w_achievements,
    "experience": w_experience,
    "extracurricular": w_extra,
    "degree_score": w_degree,
    "language": w_lang,
    "online": w_online,
    "college": w_college,
    "school": w_school
}

# --- THE ARCHITECT'S NORMALIZATION ---
total_raw_weight = sum(custom_weights.values())
if total_raw_weight == 0:
    total_raw_weight = 1 # Prevent division by zero

# Mathematically force the weights to exactly 100%
normalized_weights = {k: (v / total_raw_weight) * 100 for k, v in custom_weights.items()}

if total_raw_weight == 100:
    st.sidebar.success("Weights equal exactly 100%.")
else:
    st.sidebar.info(f"Raw sum is {total_raw_weight}%. Auto-normalized to 100%.")

st.sidebar.divider()
st.sidebar.header("Batch Processing")
uploaded_files = st.sidebar.file_uploader("Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    st.sidebar.success(f"Loaded {len(uploaded_files)} resumes.")
    
    if st.button("Run Deterministic Ranking"):
        with st.spinner("Extracting, segmenting, and scoring..."):
            results = []
            
            for file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file.getvalue())
                    tmp_path = tmp.name
                
                # Pass the NORMALIZED weights to the pipeline
                score_data = process_resume(tmp_path, normalized_weights)
                
                if score_data.get("status") in ["success", "WARNING_ISSUED", "FRAUD_DETECTED"]:
                    is_fraud = "invisible_text" in score_data.get("fraud_flags", [])
                    
                    # Update status label to show the warning clearly
                    if is_fraud:
                        status_label = "⚠️ WARNING (Hidden Text)"
                    else:
                        status_label = "Fresher" if score_data.get("fresher") else "Experienced"
                    
                    results.append({
                        "Candidate": file.name,
                        "Score": score_data["total_score"],
                        "Status": status_label,
                        "Completeness": f"{score_data.get('completeness')}/4",
                        "Raw Breakdown": score_data["breakdown"]
                    })
                else:
                    st.error(f"Failed to process {file.name}: {score_data.get('error_message')}")
                
                os.remove(tmp_path) 
            
            if results:
                df = pd.DataFrame(results)
                df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
                
                df.index = df.index + 1
                df.index.name = "Rank"


                st.subheader("🏆 Candidate Leaderboard")
                st.dataframe(
                    df[["Candidate", "Score", "Status", "Completeness"]],
                    column_config={
                        "Score": st.column_config.ProgressColumn(
                            "Final Score (0-100)", 
                            format="%.2f", 
                            min_value=0, 
                            max_value=100
                        )
                    },
                    use_container_width=True
                )
                
                st.divider()
                st.subheader("🔍 Explainability & Score Breakdown")
                
                for idx, row in df.iterrows():
                    with st.expander(f"Candidate: {row['Candidate']} - Score: {row['Score']}"):
                        
                        # Display the specific warning if hidden text was found
                        if "WARNING" in row['Raw Breakdown']:
                            st.error(row['Raw Breakdown']["WARNING"])
                        
                        col1, col2, col3 = st.columns(3)
                        
                        exp_score = row['Raw Breakdown'].get('experience', 0)
                        int_score = row['Raw Breakdown'].get('internships', 0)
                        
                        col1.metric("Experience/Internships", round(exp_score + int_score, 2))
                        col2.metric("Skills", round(row['Raw Breakdown'].get('skills', 0), 2))
                        col3.metric("Education/CGPA", round(row['Raw Breakdown'].get('cgpa_score', 0), 2))
                        
                        st.json(row['Raw Breakdown'])
                        st.markdown("#### Score Distribution")
                        
                        numeric_breakdown = {k: v for k, v in row['Raw Breakdown'].items() if isinstance(v, (int, float))}
                        if numeric_breakdown:
                            chart_data = pd.DataFrame(
                                list(numeric_breakdown.items()), 
                                columns=['Category', 'Points']
                            ).set_index('Category')
                            st.bar_chart(chart_data)
                        else:
                            st.warning("No numeric breakdown available to display chart.")