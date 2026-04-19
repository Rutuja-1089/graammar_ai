from langchain_community.llms import Ollama
import streamlit as st
import difflib
import time

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Grammar AI", layout="wide")

# -------------------------
# CSS
# -------------------------
st.markdown("""
<style>
html, body, .stApp {
    background: radial-gradient(circle at top, #0b0320, #020617 70%);
    color: #e9d5ff;
}
.block-container {
    max-width: 1100px;
    margin: auto;
    padding-top: 2rem;
}
.card {
    background: rgba(88, 28, 135, 0.25);
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 18px;
    border: 1px solid rgba(168,85,247,0.3);
    box-shadow: 0 0 18px rgba(139,92,246,0.2);
}
textarea {
    background: #140a2a !important;
    border: 1px solid #6d28d9 !important;
    color: #f3e8ff !important;
    border-radius: 10px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #c084fc);
    color: white;
    border-radius: 10px;
}
.output-box {
    background: #140a2a;
    padding: 12px;
    border-radius: 10px;
    border-left: 4px solid #c084fc;
    margin-top: 10px;
}
.del { color: #f87171; text-decoration: line-through; }
.add { color: #4ade80; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# TITLE
# -------------------------
st.title("Grammar Correction AI")

# -------------------------
# SESSION STATE
# -------------------------
for key in ["input", "corrected", "explanation"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# -------------------------
# SIDEBAR (UNCHANGED)
# -------------------------
with st.sidebar:
    st.subheader("Settings")
    tone = st.selectbox("Tone", ["Neutral", "Formal", "Casual"])
    model = st.selectbox("Model", ["gemma2:2b", "gemma3:4b"])

    if st.button("Clear"):
        for key in ["input", "corrected", "explanation"]:
            st.session_state[key] = ""
        st.rerun()

# -------------------------
# MODE
# -------------------------
mode = st.radio("Select Input Mode", ["Text Input", "File Upload"])

user_text = ""
uploaded_file = None

if mode == "Text Input":
    user_text = st.text_area("Enter text", height=180)

elif mode == "File Upload":
    uploaded_file = st.file_uploader("Upload (.txt, .pdf, .docx)", type=["txt","pdf","docx"])

# -------------------------
# FILE READER
# -------------------------
def read_file(file):
    import docx
    from PyPDF2 import PdfReader

    if file.name.endswith(".txt"):
        return file.read().decode()

    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join([p.extract_text() or "" for p in reader.pages])

    if file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    return ""

# -------------------------
# PROMPT
# -------------------------
def generate_prompt(text):
    return f"""
You are a grammar correction AI.

Return STRICTLY in this format:

CORRECTED:
<only corrected text>

EXPLANATION:
- point 1
- point 2

Rules:
- No explanation inside corrected
- No extra text
- Tone: {tone}

Text:
{text}
"""

# -------------------------
# PROCESS
# -------------------------
if st.button("Correct"):

    if mode == "Text Input":
        data = user_text
    else:
        data = read_file(uploaded_file) if uploaded_file else ""

    if not data.strip():
        st.warning("Provide input")
        st.stop()

    st.session_state.input = data

    with st.spinner("Processing..."):
        llm = Ollama(model=model)
        response = llm.invoke(generate_prompt(data))

    # -------------------------
    # PARSE OUTPUT
    # -------------------------
    corrected = ""
    explanation = ""

    if "EXPLANATION:" in response:
        parts = response.split("EXPLANATION:")
        corrected = parts[0].replace("CORRECTED:", "").strip()
        explanation = parts[1].strip()
    else:
        corrected = response.strip()

    st.session_state.corrected = corrected
    st.session_state.explanation = explanation

# -------------------------
# OUTPUT
# -------------------------
if st.session_state.corrected:

    st.subheader("Corrected Output")

    placeholder = st.empty()
    typed = ""

    for char in st.session_state.corrected:
        typed += char
        placeholder.markdown(
            f"<div class='output-box'>{typed}</div>",
            unsafe_allow_html=True
        )
        time.sleep(0.003)

# -------------------------
# EXPLANATION
# -------------------------
if st.session_state.explanation:
    st.subheader("Explanation")
    st.markdown(
        f"<div class='output-box'>{st.session_state.explanation}</div>",
        unsafe_allow_html=True
    )

# -------------------------
# COMPARISON
# -------------------------
if st.session_state.corrected:

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original")
        st.markdown(
            f"<div class='output-box'>{st.session_state.input}</div>",
            unsafe_allow_html=True
        )

    with col2:
        st.subheader("Corrected")
        st.markdown(
            f"<div class='output-box'>{st.session_state.corrected}</div>",
            unsafe_allow_html=True
        )

# -------------------------
# DIFF
# -------------------------
if st.session_state.corrected:

    o = st.session_state.input.split()
    c = st.session_state.corrected.split()

    matcher = difflib.SequenceMatcher(None, o, c)
    result = []

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            result += o[i1:i2]
        elif op == "replace":
            result.append(f"<span class='del'>{' '.join(o[i1:i2])}</span>")
            result.append(f"<span class='add'>{' '.join(c[j1:j2])}</span>")
        elif op == "delete":
            result.append(f"<span class='del'>{' '.join(o[i1:i2])}</span>")
        elif op == "insert":
            result.append(f"<span class='add'>{' '.join(c[j1:j2])}</span>")

    st.subheader("Changes")
    st.markdown(
        f"<div class='output-box'>{' '.join(result)}</div>",
        unsafe_allow_html=True
    )

# -------------------------
# DOWNLOAD
# -------------------------
if st.session_state.corrected:
    st.download_button("Download", st.session_state.corrected)