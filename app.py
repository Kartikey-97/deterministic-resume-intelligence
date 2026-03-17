# ==========================================
# SECTION 1: IMPORTS & PAGE CONFIGURATION
# ==========================================
import streamlit as st
import pandas as pd
import os
import tempfile
import time
import re

from pipeline import process_resume

st.set_page_config(page_title="Resume Ranker", layout="wide")


# ==========================================
# SECTION 2: CUSTOM UI / UX CSS INJECTION
# ==========================================
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Gradient Top Banner */
    .custom-header {
        background: linear-gradient(135deg, #4338CA 0%, #3B82F6 100%);
        padding: 40px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    }
    .custom-header h1 {
        color: #FFFFFF !important;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 5px;
        font-size: 2.2rem;
    }
    .custom-header p {
        color: #E0E7FF !important;
        font-size: 1.1rem;
        margin-top: 0;
        font-weight: 400;
    }

    /* Clean, Centered Section Headers */
    h3 {
        text-align: center;
        color: #1E293B !important; 
        font-weight: 800;
        font-size: 1.6rem;
        margin-top: 40px !important;
        margin-bottom: 25px !important;
        padding-bottom: 10px;
        border-bottom: 2px solid #E2E8F0;
        background: transparent;
        box-shadow: none;
    }

    /* Form Section Headers */
    h4 {
        color: #334155 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        margin-top: 20px !important;
        margin-bottom: 10px !important;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 5px;
    }

    /* Primary Button - Gradient Match */
    button[kind="primary"] {
        background: linear-gradient(135deg, #4338CA 0%, #3B82F6 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4) !important;
    }

    /* Fluid Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        border-color: #4338CA;
    }
    
    /* Fix for the Truncated KPI Text */
    div[data-testid="stMetricValue"] > div {
        white-space: normal !important; 
        font-size: 1.6rem !important; 
        line-height: 1.2 !important;
    }
    
    /* Align Filter Inputs */
    .stMultiSelect, .stTextInput, .stSlider {
        margin-top: 5px;
    }
    
    /* Premium Skill Tags */
    .skill-tag {
        background-color: #F1F5F9;
        color: #334155;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 4px 4px 4px 0;
        border: 1px solid #E2E8F0;
    }
    
    /* Category Header inside Breakdown */
    .breakdown-header {
        font-size: 1.1rem;
        color: #334155;
        font-weight: 600;
        margin-top: 15px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# SECTION 3: UTILITY FUNCTIONS & REGEX
# ==========================================
def clean_and_reindex(data):
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            cleaned_v = clean_and_reindex(v)
            if cleaned_v or isinstance(cleaned_v, (int, float, bool)):
                if isinstance(cleaned_v, (dict, list)) and len(cleaned_v) == 0:
                    continue
                cleaned[k] = cleaned_v
        return cleaned
    elif isinstance(data, list):
        cleaned_list = []
        for item in data:
            cleaned_item = clean_and_reindex(item)
            if cleaned_item or isinstance(cleaned_item, (int, float, bool)):
                if isinstance(cleaned_item, (dict, list)) and len(cleaned_item) == 0:
                    continue
                cleaned_list.append(cleaned_item)
        if cleaned_list:
            return {str(i + 1): v for i, v in enumerate(cleaned_list)}
        else:
            return {}
    else:
        if data == "":
            return {} 
        return data

def extract_contact_info(text, filename):
    """Ultra-robust Regex with multi-subdomain support for developer portfolios."""
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    fallback_name = re.sub(r'[^a-zA-Z]', ' ', filename.replace('.pdf', '')).title().strip()
    name = fallback_name
    
    banned_words = ['resume', 'cv', 'curriculum', 'portfolio', 'education', 'skills', 'summary', 'contact', 'email', 'phone', 'profile', 'page', 'objective', 'experience', 'projects', 'achievements', 'certifications', 'internship', 'declaration']
    
    for line in lines[:15]:
        line_no_email = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '', line)
        line_no_phone = re.sub(r'(?:\+?\d{1,3})?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '', line_no_email)
        clean_line = re.sub(r'[^a-zA-Z\s]', '', line_no_phone).strip()
        
        if not clean_line or len(clean_line.split()) > 4:
            continue
            
        if not any(bw == clean_line.lower() or clean_line.lower().startswith(bw) for bw in banned_words):
            if len(clean_line) > 2:
                name = clean_line.title()
                break

    # Fix bad PDF spaces around '.' and '@' but PRESERVE NEWLINES
    cleaned_for_links = re.sub(r'\s*(@|\.)\s*', r'\1', text)
    
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', cleaned_for_links)
    email = email_match.group(0) if email_match else ""

    phone_match = re.search(r'(?:\+?91|0)?\s*[6-9]\d{9}', text.replace(' ', ''))
    if not phone_match:
        phone_match = re.search(r'(?:\+?\d{1,3})?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    phone = phone_match.group(0) if phone_match else ""

    # Primary Social Links
    linkedin_m = re.search(r'linkedin\.com/in/[a-zA-Z0-9_-]+', cleaned_for_links, re.IGNORECASE)
    linkedin = "https://www." + linkedin_m.group(0) if linkedin_m else ""

    github_m = re.search(r'github\.com/[a-zA-Z0-9_-]+', cleaned_for_links, re.IGNORECASE)
    github = "https://" + github_m.group(0) if github_m else ""

    leetcode_m = re.search(r'leetcode\.com/[a-zA-Z0-9_-]+', cleaned_for_links, re.IGNORECASE)
    leetcode = "https://" + leetcode_m.group(0) if leetcode_m else ""

    # Catch-all Portfolio Extractor
    portfolio = ""
    # THE FIX: Added (?:[a-zA-Z0-9-]+\.)+ to capture nested subdomains like 'ruchipal7534.github.io'
    all_urls = re.findall(r'(?:https?://)?(?:www\.)?(?:[a-zA-Z0-9-]+\.)+(?:com|io|in|net|org|app|me|dev|tech)(?:/[a-zA-Z0-9_.-]+)*', cleaned_for_links)
    
    for u in all_urls:
        u_lower = u.lower()
        
        # Skip if it is the EXACT link we already found for the main 3
        if linkedin_m and linkedin_m.group(0).lower() in u_lower: continue
        if github_m and github_m.group(0).lower() in u_lower: continue
        if leetcode_m and leetcode_m.group(0).lower() in u_lower: continue
        
        # Skip standard email domains and generic sites
        if "gmail.com" in u_lower or "yahoo.com" in u_lower or "canva.com" in u_lower: continue
        
        # If it passed all filters, it is the portfolio!
        portfolio = "https://" + u.replace("https://", "").replace("http://", "") if not u.startswith("http") else u
        break

    return name, email, phone, linkedin, github, leetcode, portfolio


# ==========================================
# SECTION 4: INITIALIZATION & TOP BANNER
# ==========================================
if "processed_results" not in st.session_state:
    st.session_state.processed_results = None
if "processing_time" not in st.session_state:
    st.session_state.processing_time = 0.0

with st.container():
    st.markdown("""
    <div class="custom-header">
        <h1>Resume Ranker</h1>
        <p>Deterministic Scoring Engine | O(N) Complexity | Zero-Bias Architecture</p>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# SECTION 5: SIDEBAR (WEIGHTS & UPLOADER)
# ==========================================
st.sidebar.header("System Parameters")
st.sidebar.markdown("Adjust scoring weights based on current role requirements.")

with st.sidebar.expander("Adjust HR Weights (%)", expanded=False):
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

total_raw_weight = sum(custom_weights.values())
if total_raw_weight == 0:
    total_raw_weight = 1 
normalized_weights = {k: (v / total_raw_weight) * 100 for k, v in custom_weights.items()}

if total_raw_weight == 100:
    st.sidebar.success("Matrix balanced: 100%")
else:
    st.sidebar.info(f"Raw sum: {total_raw_weight}%. Auto-normalized to 100%.")

st.sidebar.divider()
st.sidebar.header("Batch Ingestion")
uploaded_files = st.sidebar.file_uploader("Upload Candidates (PDF)", type=["pdf"], accept_multiple_files=True)

# Telemetry Metrics
if st.session_state.get("processed_results") is not None:
    df_stats = st.session_state.processed_results
    st.sidebar.markdown("""
    <div style="background-color: #F8FAFC; padding: 16px; border-radius: 8px; border: 1px solid #E2E8F0; font-size: 0.95rem; color: #1E293B; margin-top: 15px;">
        <div style="margin-bottom: 10px; display: flex; justify-content: space-between;">
            <strong>Uploaded resumes:</strong> 
            <span style="color:#4338CA; font-weight:700;">{count}</span>
        </div>
        <div style="margin-bottom: 10px; display: flex; justify-content: space-between;">
            <strong>Processing time:</strong> 
            <span style="color:#4338CA; font-weight:700;">{time}s</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <strong>Avg score:</strong> 
            <span style="color:#4338CA; font-weight:700;">{avg:.1f}</span>
        </div>
    </div>
    """.format(
        count=len(df_stats), 
        time=st.session_state.processing_time, 
        avg=df_stats['Score'].mean()
    ), unsafe_allow_html=True)


# ==========================================
# SECTION 6: PROCESSING ENGINE & LOADING UI
# ==========================================
if uploaded_files:
    if st.button("Initialize Deterministic Ranking", type="primary", width="stretch"):
        
        loading_placeholder = st.empty()
        loading_placeholder.markdown("""
        <style>
            .loader-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 50px 0; }
            .paper-loader { width: 70px; height: 90px; background: #FFFFFF; border: 2px solid #CBD5E1; border-radius: 6px; position: relative; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); overflow: hidden; }
            .written-line { height: 4px; background: #E2E8F0; margin: 12px 10px; border-radius: 2px; width: 0%; animation: writing 1.5s infinite ease-in-out; }
            .written-line:nth-child(2) { animation-delay: 0.3s; margin-top: 15px; }
            .written-line:nth-child(3) { animation-delay: 0.6s; margin-top: 15px; max-width: 60%; }
            .pen { position: absolute; width: 8px; height: 35px; background: linear-gradient(to bottom, #4338CA 80%, #1E293B 20%); border-radius: 4px; top: 0; left: 0; transform-origin: bottom center; animation: scribble 1.5s infinite ease-in-out; box-shadow: -2px 2px 5px rgba(0,0,0,0.2); z-index: 10; }
            .pen::after { content: ''; position: absolute; bottom: -4px; left: 2px; width: 4px; height: 4px; background: #0F172A; border-radius: 50%; }
            @keyframes writing { 0% { width: 0%; } 50% { width: 70%; } 100% { width: 0%; } }
            @keyframes scribble { 0% { top: 5px; left: 5px; transform: rotate(-30deg); } 25% { top: 5px; left: 45px; transform: rotate(15deg); } 50% { top: 32px; left: 5px; transform: rotate(-30deg); } 75% { top: 32px; left: 45px; transform: rotate(15deg); } 100% { top: 5px; left: 5px; transform: rotate(-30deg); } }
            .loader-text { margin-top: 25px; color: #4338CA; font-weight: 700; font-size: 1.1rem; letter-spacing: 0.5px; animation: pulse 1.5s infinite; }
            @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
        </style>
        <div class="loader-container">
            <div class="paper-loader">
                <div class="pen"></div>
                <div class="written-line"></div>
                <div class="written-line"></div>
                <div class="written-line"></div>
            </div>
            <div class="loader-text">Executing Deterministic Math Engine...</div>
        </div>
        """, unsafe_allow_html=True)
        
        results = []
        start_time = time.time()
        
        for file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file.getvalue())
                tmp_path = tmp.name
            
            score_data = process_resume(tmp_path, normalized_weights)
            
            if score_data.get("status") in ["success", "WARNING_ISSUED", "FRAUD_DETECTED"]:
                is_fraud = "invisible_text" in score_data.get("fraud_flags", [])
                status_label = "FLAGGED (Anomalous Format)" if is_fraud else ("Fresher" if score_data.get("fresher") else "Experienced")
                profession = score_data.get("profession", "General / Uncategorized")
                
                exp_years = 0
                ext_data = score_data.get("extracted_data", {})
                if ext_data and "experience" in ext_data and "total_experience_years" in ext_data["experience"]:
                    exp_years = ext_data["experience"]["total_experience_years"]
                
                results.append({
                    "Candidate": file.name,
                    "Profession": profession.title(),
                    "Experience (Years)": exp_years,
                    "Score": score_data["total_score"],
                    "Status": status_label,
                    "Completeness": f"{score_data.get('completeness')}/4",
                    "Raw Breakdown": score_data["breakdown"],
                    "Extracted Data": score_data.get("extracted_data", {}),
                    "Raw Text": score_data.get("raw_text", "")
                })
            else:
                st.error(f"Processing failed for {file.name}: {score_data.get('error_message')}")
            
            os.remove(tmp_path) 
            
        end_time = time.time()
        st.session_state.processing_time = round(end_time - start_time, 2)
            
        loading_placeholder.empty()
        
        if results:
            df = pd.DataFrame(results)
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)
            st.session_state.processed_results = df
            st.rerun()


# ==========================================
# SECTION 7: DASHBOARD RENDERING & KPIs
# ==========================================
if st.session_state.get("processed_results") is not None:
    df = st.session_state.processed_results.copy()

    st.markdown("### Executive Overview")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    top_prof = df['Profession'].mode()[0] if not df.empty else "N/A"
    
    kpi1.metric("Total Candidates", len(df))
    kpi2.metric("Median Score", f"{df['Score'].median():.2f}")
    kpi3.metric("Highest Density Role", top_prof)
    
    fraud_count = len(df[df['Status'].str.contains("FLAGGED")])
    kpi4.metric("Security Alerts", fraud_count, delta_color="inverse")


    # ==========================================
    # SECTION 8: ADVANCED FILTERING ENGINE
    # ==========================================
    st.markdown("### Advanced Filtering")
    
    with st.container(border=True):
        col_prof, col_skill, col_exp, col_score = st.columns([1.5, 1.5, 1, 1])
        
        with col_prof:
            available_professions = sorted(df["Profession"].unique())
            selected_professions = st.multiselect(
                "Filter by Profession (Blank = All):", 
                options=available_professions, 
                default=[] 
            )
            
        with col_skill:
            skill_search = st.text_input("Search Taxonomy (e.g., Python, React):").lower().strip()
            
        with col_exp:
            max_exp = int(df["Experience (Years)"].max()) if not df.empty else 10
            min_exp_filter = st.slider("Min Experience (Yrs):", 0, max(10, max_exp), 0)
            
        with col_score:
            min_score_filter = st.slider("Min Score Threshold:", 0, 100, 0)

    # Apply Filters
    if selected_professions:
        filtered_df = df[
            (df["Profession"].isin(selected_professions)) & 
            (df["Experience (Years)"] >= min_exp_filter) &
            (df["Score"] >= min_score_filter)
        ]
    else:
        filtered_df = df[
            (df["Experience (Years)"] >= min_exp_filter) &
            (df["Score"] >= min_score_filter)
        ]
    
    if skill_search:
        def has_skill(extracted_data):
            return skill_search in str(extracted_data).lower()
        filtered_df = filtered_df[filtered_df["Extracted Data"].apply(has_skill)]

    filtered_df = filtered_df.sort_values(by="Score", ascending=False).reset_index(drop=True)
    filtered_df.index = filtered_df.index + 1
    filtered_df.index.name = "Rank"


    # ==========================================
    # SECTION 9: TABBED LEADERBOARD & DATA
    # ==========================================
    st.markdown("### Candidate Leaderboard")
    tab1, tab2 = st.tabs(["Evaluated Candidates", "System Defense Log"])
    
    with tab1:
        if filtered_df.empty:
            st.info("No candidates match your current filter parameters.")
        else:
            st.dataframe(
                filtered_df[["Candidate", "Profession", "Experience (Years)", "Score", "Status", "Completeness"]],
                column_config={
                    "Score": st.column_config.ProgressColumn(
                        "Final Score (0-100)", 
                        format="%.2f", 
                        min_value=0, 
                        max_value=100
                    ),
                    "Status": st.column_config.TextColumn("Tier / Status")
                },
                use_container_width=True
            )
            
            st.markdown("### In-Depth Explainability & Verification")
            for idx, row in filtered_df.iterrows():
                with st.expander(f"{row['Candidate']}  |  Score: {row['Score']:.2f}"):
                    
                    if "FLAGGED" in row['Status']:
                        st.error("SECURITY ALERT: Anomalous formatting detected. System flagged potential hidden text or microscopic fonts. Math bounds applied.")
                    
                    inner_tab1, inner_tab2, inner_tab3 = st.tabs(["Score & Insights", "HR CRM Verification", "Developer Audit"])
                    
                    # --- TAB 1: VISUAL INSIGHTS ---
                    with inner_tab1:
                        st.markdown("<div class='breakdown-header'>Algorithm Score Distribution</div>", unsafe_allow_html=True)
                        
                        exp_score = row['Raw Breakdown'].get('experience', 0) + row['Raw Breakdown'].get('internships', 0)
                        skill_score = row['Raw Breakdown'].get('skills', 0)
                        edu_score = row['Raw Breakdown'].get('cgpa_score', 0)
                        proj_score = row['Raw Breakdown'].get('projects', 0)
                        
                        p_col1, p_col2 = st.columns(2)
                        with p_col1:
                            st.write(f"**Experience/Internships:** {exp_score:.2f} pts")
                            st.progress(min(int(exp_score), 100))
                            st.write(f"**Education/CGPA:** {edu_score:.2f} pts")
                            st.progress(min(int(edu_score), 100))
                        with p_col2:
                            st.write(f"**Skills Extraction:** {skill_score:.2f} pts")
                            st.progress(min(int(skill_score), 100))
                            st.write(f"**Projects Detected:** {proj_score:.2f} pts")
                            st.progress(min(int(proj_score), 100))
                            
                        st.markdown("---")
                        st.markdown("<div class='breakdown-header'>Extracted Taxonomy Tags</div>", unsafe_allow_html=True)
                        
                        extracted_json = row['Extracted Data']
                        skills_data = extracted_json.get('skills', {})
                        
                        all_skills = []
                        for category, skill_list in skills_data.items():
                            if isinstance(skill_list, dict):
                                all_skills.extend(skill_list.values())
                            elif isinstance(skill_list, list):
                                all_skills.extend(skill_list)
                        
                        if all_skills:
                            formatted_skills = [s.replace("_", " ").title() for s in all_skills]
                            tags_html = "".join([f"<span class='skill-tag'>{skill}</span>" for skill in set(formatted_skills)])
                            st.markdown(tags_html, unsafe_allow_html=True)
                        else:
                            st.write("No recognized taxonomy skills extracted.")

                    # --- TAB 2: COMPREHENSIVE HR CRM FORM & DOWNLOAD ---
                    with inner_tab2:
                        st.markdown("<div class='breakdown-header'>Candidate CRM Profile</div>", unsafe_allow_html=True)
                        st.write("Review, amend, and complete the extracted candidate profile. Verified profiles can be downloaded as an official HTML record.")
                        
                        ext_data = row['Extracted Data']
                        exp_data = ext_data.get('experience', {})
                        proj_data = ext_data.get('projects', {})
                        edu_data = ext_data.get('education', {})
                        
                        c_name, c_email, c_phone, c_linkedin, c_github, c_leetcode, c_portfolio = extract_contact_info(row['Raw Text'], row['Candidate'])
                        
                        exp_val = float(exp_data.get('total_experience_years', row['Experience (Years)']))
                        
                        with st.form(key=f"crm_form_{idx}", border=True):
                            
                            st.markdown("#### Identity & Contact Information")
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                f_name = st.text_input("Full Name", value=c_name)
                            with c2:
                                f_email = st.text_input("Email Address", value=c_email)
                            with c3:
                                f_phone = st.text_input("Phone Number", value=c_phone)
                                
                            st.markdown("#### Digital Footprint & Profiles")
                            link1, link2, link3, link4 = st.columns(4)
                            with link1:
                                f_li = st.text_input("LinkedIn Profile", value=c_linkedin)
                            with link2:
                                f_git = st.text_input("GitHub Profile", value=c_github)
                            with link3:
                                f_leet = st.text_input("LeetCode Profile", value=c_leetcode)
                            with link4:
                                f_port = st.text_input("Personal Portfolio", value=c_portfolio)
                                
                            st.markdown("#### Professional Experience & Projects")
                            p1, p2, p3, p4 = st.columns(4)
                            with p1:
                                f_track = st.text_input("Assigned Track", value=row['Profession'])
                            with p2:
                                f_exp = st.number_input("Experience (Years)", value=exp_val, min_value=0.0, step=0.1, format="%.1f")
                            with p3:
                                f_int = st.number_input("Internships Detected", value=int(exp_data.get('internship_count', 0)), min_value=0)
                            with p4:
                                f_proj = st.number_input("Projects Detected", value=int(proj_data.get('project_count', 0)), min_value=0)
                                
                            st.markdown("#### Skills & Competencies (Categorized)")
                            
                            f_skills = {}
                            if skills_data:
                                # SEMANTIC GROUPING ENGINE: Consolidate overlapping AI classifications
                                consolidated_categories = {}
                                for category, skill_list in skills_data.items():
                                    cat_name = category.replace("_", " ").title()
                                    
                                    if any(kw in cat_name for kw in ["Ai", "Artificial", "Ml"]):
                                        cat_name = "AI & Machine Learning"
                                    elif any(kw in cat_name for kw in ["Devops", "Cloud", "Infrastructure"]):
                                        cat_name = "DevOps & Cloud"
                                    elif any(kw in cat_name for kw in ["Data", "Analytics"]):
                                        cat_name = "Data & Analytics"
                                    elif any(kw in cat_name for kw in ["Security", "Cyber"]):
                                        cat_name = "Cybersecurity"
                                    elif any(kw in cat_name for kw in ["Web", "Mobile"]):
                                        cat_name = "Web & Mobile Development"
                                    elif any(kw in cat_name for kw in ["Programming", "Language"]):
                                        cat_name = "Programming Languages"
                                    elif any(kw in cat_name for kw in ["Communication", "Corporate", "Effectiveness", "Skill"]):
                                        cat_name = "Soft Skills"
                                    elif any(kw in cat_name for kw in ["Research", "Education", "Academia", "Science", "Training"]):
                                        cat_name = "Research & Education"
                                    
                                    if isinstance(skill_list, dict):
                                        skill_vals = list(skill_list.values())
                                    else:
                                        skill_vals = skill_list
                                        
                                    if cat_name not in consolidated_categories:
                                        consolidated_categories[cat_name] = set()
                                        
                                    for s in skill_vals:
                                        consolidated_categories[cat_name].add(s.replace("_", " ").title())
                                
                                skill_cols = st.columns(2)
                                col_idx = 0
                                for cat_name, skill_set in consolidated_categories.items():
                                    if not skill_set: continue
                                    cat_skills = ", ".join(sorted(list(skill_set)))
                                    
                                    with skill_cols[col_idx % 2]:
                                        f_skills[cat_name] = st.text_input(cat_name, value=cat_skills, key=f"skill_{idx}_{col_idx}")
                                    col_idx += 1
                            else:
                                st.write("No recognized taxonomy skills extracted.")
                                         
                            st.markdown("#### Education & System Metrics")
                            e1, e2 = st.columns(2)
                            with e1:
                                f_edu = st.text_input("Degree Detected", value="Yes" if edu_data.get('degree_detected') else "No Data")
                            with e2:
                                st.text_input("System Completeness Score", value=row['Completeness'], disabled=True)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            submit_btn = st.form_submit_button("Verify Data & Generate Export", type="primary", width="stretch")
                            
                            if submit_btn:
                                html_content = f"""
                                <!DOCTYPE html>
                                <html>
                                <head>
                                <style>
                                    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1E293B; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; }}
                                    h1 {{ color: #4338CA; border-bottom: 2px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 30px; }}
                                    h2 {{ color: #334155; margin-top: 30px; font-size: 18px; text-transform: uppercase; letter-spacing: 1px; }}
                                    .box {{ background: #F8FAFC; padding: 20px; border-radius: 8px; border: 1px solid #E2E8F0; margin-bottom: 20px; }}
                                    ul {{ list-style-type: none; padding: 0; margin: 0; }}
                                    li {{ margin-bottom: 10px; font-size: 15px; border-bottom: 1px dashed #E2E8F0; padding-bottom: 5px; }}
                                    li:last-child {{ border-bottom: none; }}
                                    b {{ color: #0F172A; display: inline-block; width: 150px; }}
                                </style>
                                </head>
                                <body>
                                    <h1>Verified Candidate Profile: {f_name}</h1>
                                    
                                    <div class="box">
                                        <h2>Contact & Identity</h2>
                                        <ul>
                                            <li><b>Email:</b> {f_email}</li>
                                            <li><b>Phone:</b> {f_phone}</li>
                                        </ul>
                                    </div>
                                    
                                    <div class="box">
                                        <h2>Digital Footprint</h2>
                                        <ul>
                                            <li><b>LinkedIn:</b> <a href="{f_li}">{f_li}</a></li>
                                            <li><b>GitHub:</b> <a href="{f_git}">{f_git}</a></li>
                                            <li><b>LeetCode:</b> <a href="{f_leet}">{f_leet}</a></li>
                                            <li><b>Portfolio:</b> <a href="{f_port}">{f_port}</a></li>
                                        </ul>
                                    </div>
                                    
                                    <div class="box">
                                        <h2>Professional Summary</h2>
                                        <ul>
                                            <li><b>Track:</b> {f_track}</li>
                                            <li><b>Experience:</b> {f_exp} Years</li>
                                            <li><b>Internships:</b> {f_int}</li>
                                            <li><b>Projects:</b> {f_proj}</li>
                                            <li><b>Degree Detected:</b> {f_edu}</li>
                                        </ul>
                                    </div>
                                    
                                    <div class="box">
                                        <h2>Verified Skills Matrix</h2>
                                        <ul>
                                """
                                for k, v in f_skills.items():
                                    html_content += f"<li><b>{k}:</b> {v}</li>\n"
                                
                                html_content += """
                                        </ul>
                                    </div>
                                </body>
                                </html>
                                """
                                
                                st.session_state[f"export_{idx}"] = html_content
                                st.success("Data Verified! Click the button below to download the official HTML record.")

                        if f"export_{idx}" in st.session_state:
                            st.download_button(
                                label="Download Official Profile (HTML)",
                                data=st.session_state[f"export_{idx}"],
                                file_name=f"{c_name.replace(' ', '_')}_Profile.html",
                                mime="text/html"
                            )

                    # --- TAB 3: RAW DEVELOPER AUDIT ---
                    with inner_tab3:
                        st.markdown("**Structured Data Mapping:**")
                        polished_data = clean_and_reindex(extracted_json)
                        st.json(polished_data)
                        
                        st.markdown("**Raw String Extraction:**")
                        st.text_area(
                            "Audit Log", 
                            value=row['Raw Text'], 
                            height=200, 
                            label_visibility="collapsed", 
                            disabled=True, 
                            key=f"raw_text_area_{idx}_{row['Candidate']}"
                        )
        
    with tab2:
        fraud_df = df[df['Status'].str.contains("FLAGGED", case=False, na=False)]
        
        if not fraud_df.empty:
            st.error(f"Intercepted {len(fraud_df)} candidate(s) attempting to bypass the visual shield.")
            st.dataframe(fraud_df[["Candidate", "Profession", "Score", "Completeness"]], use_container_width=True)
        else:
            st.success("No formatting anomalies or manipulation detected in the current candidate pool. Shield intact.")