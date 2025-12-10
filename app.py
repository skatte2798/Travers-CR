import streamlit as st
import openai
import os
import tempfile
from io import BytesIO
from fpdf import FPDF

# ========================= CONFIG =========================
openai.api_key = st.secrets["OPENAI_API_KEY"]

def generate_pdf(transcription, analysis):
    pdf = FPDF()
    pdf.add_page()

    font_path = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")
    pdf.add_font("DejaVu", "", font_path, uni=True)

    pdf.set_font("DejaVu", "", 18)
    pdf.cell(0, 15, "Call Quality Report", ln=1, align="C")
    pdf.ln(10)
    
    pdf.set_font("DejaVu", "", 11)
    
    # Sanitize text to avoid unsupported characters
    transcription_safe = transcription.encode("latin1", errors="replace").decode("latin1")
    analysis_safe = analysis.encode("latin1", errors="replace").decode("latin1")
    
    pdf.multi_cell(0, 7, f"Transcription:\n\n{transcription_safe}\n\n\nAI Analysis:\n\n{analysis_safe}")
    
    # Write PDF to a BytesIO buffer
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer  # return a file-like object


# ========================= CSS =========================
st.markdown("""
<style>
    /* Thin black top bar */
    .topbar {
        background:#000;
        height:6px;
        position:fixed;
        top:0; left:0; right:0;
        z-index:9999;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background:#0a1f3d !important;
        padding: 2rem 1rem;
    }

    .sidebar-title {
        color:#00d4ff;
        font-size:2rem;
        font-weight:700;
        text-align:center;
        margin-bottom:1rem;
        line-height:1.3;
    }

    /* Sidebar buttons */
    .stButton > button {
        background:linear-gradient(135deg, #4a90e2, #007aff);
        color:white;
        border-radius:12px;
        padding:0.7rem 1rem;
        font-weight:bold;
        width:100%;
        border:none;
        box-shadow:0 4px 12px rgba(0,0,0,0.2);
    }
    .stButton > button:hover {
        background:linear-gradient(135deg, #357abd, #0051c8);
        box-shadow:0 6px 18px rgba(0,0,0,0.25);
        transform:translateY(-1px);
    }

    .sidebar-sub {
        color:#9fc5ff;
        text-align:center;
        margin-top:2rem;
        font-size:0.85rem;
    }

    /* Main page */
    .main > div {
        background:#f8f9fc;
        padding-top:5rem !important;
    }
    .block-container {
        max-width:900px;
        padding:2rem;
    }

    /* Upload icon */
    .upload-icon {
        text-align:center;
        margin-bottom:1rem;
    }

    .pill {
        background:white;
        padding:1rem 2rem;
        border-radius:50px;
        text-align:center;
        box-shadow:0 4px 15px rgba(0,0,0,0.05);
        font-size:0.95rem;
        color:#555;
    }
</style>
""", unsafe_allow_html=True)

# Top bar
st.markdown('<div class="topbar"></div>', unsafe_allow_html=True)

# ========================= SIDEBAR =========================
with st.sidebar:
    st.markdown('<div class="sidebar-title">Travers<br>Call Analyzer</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.button("📊 Dashboard", use_container_width=True)
    st.button("🎧 Upload Call", use_container_width=True)
    st.button("📁 Reports", use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="sidebar-sub">AI-Powered Call Intelligence</div>', unsafe_allow_html=True)

# ========================= MAIN PAGE =========================
st.markdown("<h1 style='text-align:center; color:#1a1a1a;'>Turn Conversations into</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center; color:#4a90e2;'>Insights</h1>", unsafe_allow_html=True)

st.markdown(
    "<p style='text-align:center; color:#666; font-size:1.2rem; max-width:700px; margin:1.5rem auto;'>"
    "Upload your call recordings to get instant, AI-powered quality scoring, transcription, and coaching feedback.</p>",
    unsafe_allow_html=True,
)

# SVG Upload Icon
st.markdown("""
<div class="upload-icon">
    <svg width="70" height="70" viewBox="0 0 24 24" fill="none" stroke="#4a90e2" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round">
        <path d="M16 16v-6a4 4 0 0 0-8 0v6"></path>
        <polyline points="12 12 12 22"></polyline>
        <polyline points="8 18 12 22 16 18"></polyline>
    </svg>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["mp4", "mov", "wav", "m4a"])

# ========================= PROCESS LOGIC =========================
if uploaded_file is not None:
    # Show name + video
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            f"<p style='text-align:center; color:#4a90e2; font-weight:bold;'>{uploaded_file.name}</p>",
            unsafe_allow_html=True
        )
    with col2:
        st.video(uploaded_file)

    if st.button("Analyze Call Recording", type="primary", use_container_width=True):

        # Temp video file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            video_path = tmp.name

        # ===============================
        # Transcribe using Whisper API
        # ===============================
        with st.spinner("Transcribing with Whisper API..."):
            with open(video_path, "rb") as audio_file:
                transcription_response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )

            # Handle OpenAI object response safely
            if hasattr(transcription_response, "text"):
                transcription = transcription_response.text
            elif isinstance(transcription_response, dict):
                transcription = transcription_response.get("text", "")
            else:
                transcription = str(transcription_response)

        st.success("Transcription Complete")
        with st.expander("View Full Transcription"):
            st.write(transcription)

        # ===============================
        # Evaluation using GPT
        # ===============================
        with st.spinner("Running AI Quality Evaluation..."):
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert call-center quality auditor. Provide structured scoring, analysis, and coaching.If a criterion does not apply to the call, intelligently adjust scoring and note “Not Applicable.”  Be objective, concise, and professional."},
                    {"role": "user", "content": f"""
                            Evaluate this call using the following criteria (score each 1–10 unless Not Applicable).  
                            For each section, include:
                                - Score
                                - What went well
                                - Areas for improvement
                                - Coaching tips

                            After evaluating all categories, include:
                                - Overall summary
                                - Overall score (average of applicable categories)

                            Evaluation Criteria:

                            1. Greeting & Professionalism  
                            Did the rep:  
                                • Thank the customer for calling Travers  
                                • Identify themselves  
                                • Sound friendly, sincere, and professional  
                                • Speak clearly with no background noise  
                                • Attempt rapport/connection when appropriate  

                            2. Call Purpose Identification  
                            Did the rep:  
                                • Identify the reason for the call  
                                • Clarify the customer’s needs  
                                • Ask probing questions when needed  

                            3. Verification & Account Accuracy  
                            Did the rep:  
                                • Verify account name/number  
                                • Verify contact name, phone, and email  
                                • Update incorrect info (spoken updates only)  
                                • Ask for/confirm ship-to address if needed  

                            4. Order Entry Accuracy (Items, Pricing, Flyers, Promotions)  
                            Did the rep:  
                                • Ask for PO#  
                                • Ask if ordering from flyer; offer brochures  
                                • Request key code if applicable  
                                • Confirm description, quantity, and price of items  
                                • Offer substitutes/vendor availability when needed  
                                • Offer price-break quantities  

                            5. Accuracy & Product Knowledge  
                            Did the rep:  
                                • Provide accurate information  
                                • Confirm ship-via  
                                • Provide total with tax & shipping  
                                • Provide transit time (as estimate)  
                                • Provide OE# or offer email confirmation  

                            6. Empathy & Tone  
                                Score tone, patience, warmth, empathy, and emotional intelligence.

                            7. Call Control & Efficiency  
                            Did the rep:  
                                • Avoid unnecessary holds or long silences  
                                • Follow correct hold/transfer procedures  
                                • Manage the call efficiently  

                            8. Active Listening  
                            Did the rep:  
                                • Avoid interrupting  
                                • Demonstrate understanding  
                                • Respond appropriately  

                            9. Problem Resolution  
                            Did the rep:  
                                • Fully resolve or progress the customer’s request  
                                • Go above and beyond when appropriate  
                                • Provide complete and correct answers  

                            10. Closing & Next Steps  
                            Did the rep:  
                                • Set follow-up expectations  
                                • Ask if the customer needs anything else  
                                • Thank the customer for choosing Travers  
                                • Close the call professionally  

                        Transcription:
                        {{transcription}}
                    """}
                ],
                temperature=0.4
            )
            analysis = response.choices[0].message.content

        st.markdown("## AI Quality Analysis")
        st.markdown(analysis)

        # PDF Download
        pdf = generate_pdf(transcription, analysis)
        st.download_button(
            label="Download Full Report (PDF)",
            data=pdf,
            file_name=f"Travers_Analysis_{uploaded_file.name.split('.')[0]}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        # Cleanup
        for p in [video_path]:
            if os.path.exists(p):
                os.unlink(p)

else:
    st.markdown("""
    <div style='text-align:center; margin:3rem 0;'>
        <h3 style='color:#1a1a1a; margin:1.5rem 0 0.5rem;'>Upload Call Recording</h3>
        <p style='color:#888;'>Drag & drop your MP4, MOV, or WAV file here,<br>or click to browse.</p>
        <p style='color:#aaa; margin-top:1rem; font-size:0.9rem;'>MP4 • MOV • WAV • M4A</p>
    </div>
    """, unsafe_allow_html=True)

# ========================= FEATURE PILLS =========================
st.markdown("<br><br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown('<div class="pill"><strong>99% Accuracy</strong><br><small>Whisper AI transcription</small></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="pill"><strong>Instant Scoring</strong><br><small>Automated quality rubric</small></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="pill"><strong>Actionable Coaching</strong><br><small>Personalized feedback</small></div>', unsafe_allow_html=True)
