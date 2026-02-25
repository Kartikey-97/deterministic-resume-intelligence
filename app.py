import streamlit as st
import pandas as pd
import os
import tempfile

from pipeline import process_resume

st.set_page_config(page_title="Deterministic ATS Leaderboard", layout="wide", page_icon="")

st.title(" Automated Resume Extraction & Ranking Engine")
st.markdown("Deterministic scoring. Explainable AI. Zero bias.")

# Sidebar for uploads
st.sidebar.header("Batch Processing")
uploaded_files = st.sidebar.file_uploader("Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    # Fixed the double message right here
    st.sidebar.success(f"Loaded {len(uploaded_files)} resumes.")
    
    if st.button("Run Deterministic Ranking"):
        with st.spinner("Extracting, segmenting, and scoring..."):
            
            results = []
            
            for file in uploaded_files:
                # 1. Save uploaded file temporarily to pass to PyMuPDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file.getvalue())
                    tmp_path = tmp.name
                
                # 2. RUN THE MASTER PIPELINE
                score_data = process_resume(tmp_path)
                
                # 3. Append to Leaderboard if successful
                if score_data.get("status") in ["success", "FRAUD_DETECTED"]:
                    # Check for fraud flags
                    is_fraud = "invisible_text" in score_data.get("fraud_flags", [])
                    status_label = "FRAUD" if is_fraud else ("Fresher" if score_data.get("fresher") else "Experienced")
                    
                    results.append({
                        "Candidate": file.name,
                        "Score": score_data["total_score"],
                        "Status": status_label,
                        "Completeness": f"{score_data.get('completeness')}/4",
                        "Raw Breakdown": score_data["breakdown"]
                    })
                else:
                    st.error(f"Failed to process {file.name}: {score_data.get('error_message')}")
                
                # Clean up the temp file
                os.remove(tmp_path) 
            
            # Create Leaderboard
            if results:
                df = pd.DataFrame(results)
                
                # --- THE ARCHITECT'S SOFT CURVE ---
                # Safely boosts scores without over-inflating mediocre batches.
                max_raw_score = df["Score"].max()
                
                # Only apply the curve if the top score is below a respectable threshold (e.g., 85)
                if max_raw_score > 0 and max_raw_score < 85:
                    # We close 60% of the gap between their score and 85
                    gap = 85 - max_raw_score
                    target_top_score = max_raw_score + (gap * 0.6)
                    
                    curve_multiplier = target_top_score / max_raw_score
                    df["Score"] = (df["Score"] * curve_multiplier).clip(upper=100).round(2)
                # ---------------------------------------------------
                
                # Sort by highest score first
                df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
                
                st.subheader("Candidate Leaderboard")
                
                # Use st.dataframe to render the progress column
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
                
                # Explainability Section
                st.divider()
                st.subheader("🔍 Explainability & Score Breakdown")
                
                for idx, row in df.iterrows():
                    with st.expander(f"Candidate: {row['Candidate']} - Score: {row['Score']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        # Handle potential missing keys gracefully
                        exp_score = row['Raw Breakdown'].get('experience', 0)
                        int_score = row['Raw Breakdown'].get('internships', 0)
                        
                        col1.metric("Experience/Internships", f"{exp_score + int_score}")
                        col2.metric("Skills", row['Raw Breakdown'].get('skills', 0))
                        col3.metric("Education/CGPA", row['Raw Breakdown'].get('cgpa_score', 0))
                        
                        st.json(row['Raw Breakdown'])
                        
                        # Add a visual chart for the judges
                        st.markdown("#### Score Distribution")
                        
                        # DEFENSIVE ENGINEERING: Filter out non-numeric values (like our FRAUD_PENALTY string)
                        # so the bar chart doesn't crash.
                        numeric_breakdown = {k: v for k, v in row['Raw Breakdown'].items() if isinstance(v, (int, float))}
                        
                        if numeric_breakdown:
                            chart_data = pd.DataFrame(
                                list(numeric_breakdown.items()), 
                                columns=['Category', 'Points']
                            ).set_index('Category')
                            st.bar_chart(chart_data)
                        else:
                            st.warning("No numeric breakdown available to display chart.")