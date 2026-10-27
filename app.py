import streamlit as st
import datetime
import sys
import io
from supabase import create_client, Client

# --- 1. Page Config ---
st.set_page_config(
    page_title="Python Learners Journal",
    page_icon="🐍",
    layout="wide"
)

# --- 2. Custom CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    section[data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1f2937; }
    .custom-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); margin-bottom: 20px;
    }
    h1, h2, h3 { color: #38bdf8 !important; }
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6 0%, #6366f1 100%);
        color: white; border: none; border-radius: 8px; padding: 10px 20px;
        font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #2563eb 0%, #4f46e5 100%);
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Supabase Connection ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error("Cloud database connection failed. Please check your API keys.")

# --- 4. Database Functions ---
def fetch_all_notes():
    try:
        response = supabase.table("notes").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception:
        return []

def fetch_user_notes(user_email):
    try:
        response = supabase.table("notes").select("*").eq("email", user_email).order("created_at", desc=True).execute()
        return response.data
    except Exception:
        return []

def insert_note(title, author, email, category, concept, code):
    data = {
        "title": title, "author": author, "email": email,
        "category": category, "concept": concept, "code": code
    }
    supabase.table("notes").insert(data).execute()

def get_active_learners():
    try:
        response = supabase.table("notes").select("author").execute()
        unique_authors = set([row['author'] for row in response.data if row['author']])
        return list(unique_authors)
    except Exception:
        return []

# --- 5. Sidebar (Admin & Active Users) ---
st.sidebar.markdown("<h2>🐍 Python Learners</h2>", unsafe_allow_html=True)

st.sidebar.markdown("---")
with st.sidebar.expander("🔐 Admin Login"):
    admin_pass = st.text_input("Admin Password", type="password")
    if st.button("Login as Admin"):
        if admin_pass == ADMIN_PASSWORD:
            st.session_state['is_admin'] = True
            st.success("Admin Login Successful!")
        else:
            st.error("Incorrect Password!")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Active Learners")
learners = get_active_learners()
if len(learners) > 0:
    for learner in learners:
        st.sidebar.write(f"👤 {learner}")
else:
    st.sidebar.info("No active learners yet.")

# --- 6. Main UI & Tabs ---
st.markdown("<h1>📝 Python Learners - Connected Journal</h1>", unsafe_allow_html=True)

tabs_list = ["✍️ New Entry", "▶️ Live Code Runner", "🔒 My Private Notes"]
if st.session_state.get('is_admin', False):
    tabs_list.append("👑 Admin Panel")

tabs = st.tabs(tabs_list)

# --- TAB 1: Add New Entry ---
with tabs[0]:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("Add a New Entry")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        title = st.text_input("Topic Name", placeholder="e.g., Functions & Arguments")
        category = st.selectbox("Category", ["Basics", "Data Structures", "Functions", "OOP", "Libraries", "Projects"])
    with col2:
        author = st.text_input("Your Name (Required)", placeholder="e.g., Ahmad")
        email = st.text_input("Your Email (Optional)", placeholder="ahmad@example.com")

    concept = st.text_area("What did you learn? (Concept)", placeholder="Write details here...", height=100)
    user_code = st.text_area("Python Code", value="print('Hello Python Learners!')", height=150)
    
    if st.button("💾 Save to Cloud", type="primary"):
        if not author or author.strip() == "":
            st.error("⚠️ Please enter your name first!")
        elif not title or not concept:
            st.error("Please fill in both Topic Name and Concept.")
        else:
            insert_note(title, author, email, category, concept, user_code)
            st.success(f"🎉 Great job {author}! Your note has been saved to the cloud.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: Live Code Runner ---
with tabs[1]:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("▶️ Python Live Runner")
    test_code = st.text_area("Write code here:", value="print('Testing Live Python!')", height=180)
    if st.button("🚀 Run Code"):
        try:
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            exec(test_code)
            sys.stdout = old_stdout
            output = buffer.getvalue()
            st.code(output if output else "Code executed successfully!", language="text")
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: My Private Notes ---
with tabs[2]:
    st.subheader("🔒 My Private Notes")
    search_email = st.text_input("Enter your email to find your notes:", placeholder="ahmad@example.com")
    
    if search_email:
        my_notes = fetch_user_notes(search_email)
        if not my_notes:
            st.info("No notes found for this email.")
        else:
            for entry in my_notes:
                st.markdown(f"### 📌 {entry['title']} ({entry['category']})")
                st.markdown(f"**Concept:** {entry['concept']}")
                st.code(entry["code"], language="python")
                st.markdown("---")

# --- TAB 4: ADMIN PANEL ---
if st.session_state.get('is_admin', False):
    with tabs[3]:
        st.subheader("👑 Admin Dashboard - All Notes")
        all_notes = fetch_all_notes()
        for entry in all_notes:
            st.markdown(f"**{entry.get('author')} ({entry.get('email', 'No Email')})** - {entry['title']}")
            st.code(entry["code"], language="python")
            st.markdown("---")
            