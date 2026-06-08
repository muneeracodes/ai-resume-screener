import streamlit as st
import os
import shutil
from pipeline.downloader import download_audio, is_playlist, format_duration
from pipeline.transcriber import transcribe, get_transcript_with_timestamps
from pipeline.detector import detect_language, get_language_message, get_whisper_language_name
from pipeline.summarizer import summarize, summarize_playlist

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Summarizer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .meta-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    .lang-badge {
        display: inline-block;
        background: #ede9fe;
        color: #5b21b6;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .summary-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        line-height: 1.8;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
    }
    .stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    summary_style = st.radio(
        "📝 Summary style",
        options=["bullets", "short", "detailed", "timestamps"],
        format_func=lambda x: {
            "bullets": "🔵 Bullet Points",
            "short": "⚡ Short (3-5 sentences)",
            "detailed": "📖 Detailed",
            "timestamps": "🕐 Key Moments with Timestamps",
        }[x],
        index=0,
    )

    st.markdown("---")
    whisper_size = st.select_slider(
        "🎙️ Transcription quality",
        options=["tiny", "base", "small"],
        value="base",
        help="Larger = more accurate but slower. 'base' recommended."
    )

    st.markdown("---")
    show_transcript = st.checkbox("📄 Show full transcript", value=False)

    st.markdown("---")
    st.markdown("**🗑️ Cleanup**")
    if st.button("Clear cached audio files"):
        if os.path.exists("audio"):
            shutil.rmtree("audio")
            os.makedirs("audio")
        st.success("Audio cache cleared!")

    st.markdown("---")
    st.markdown("""
    **How to use:**
    1. Paste a YouTube URL
    2. Choose your summary style
    3. Click Summarize
    
    **Supports:**
    - ✅ Single videos
    - ✅ Playlists
    - ✅ Any language → English summary
    """)

# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">🎬 YouTube Summarizer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Paste any YouTube URL — get an intelligent summary in seconds</p>', unsafe_allow_html=True)

url = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=... or a playlist URL",
    label_visibility="collapsed",
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    summarize_btn = st.button("✨ Summarize", use_container_width=True)

st.markdown("---")

# ── Core logic ────────────────────────────────────────────────────────────────
if summarize_btn and url:
    playlist_mode = is_playlist(url)

    try:
        # ── Step 1: Download ──────────────────────────────────────────────
        with st.status("⬇️ Downloading audio...", expanded=True) as status:
            st.write("Extracting audio from YouTube...")
            audio_path, meta = download_audio(url)
            st.write("✅ Audio downloaded successfully")
            status.update(label="✅ Audio ready", state="complete")

        # ── Playlist mode ─────────────────────────────────────────────────
        if playlist_mode and isinstance(audio_path, list):
            st.info(f"📋 Playlist detected — {len(audio_path)} videos found")

            all_transcripts = []
            progress = st.progress(0)

            for i, (path, m) in enumerate(zip(audio_path, meta)):
                with st.status(f"Processing video {i+1}/{len(audio_path)}: {m['title'][:50]}..."):
                    result = transcribe(path, model_size=whisper_size)
                    lang_name = get_whisper_language_name(result["language"])
                    all_transcripts.append({
                        "title": m["title"],
                        "text": result["text"],
                        "language": lang_name,
                        "segments": result["segments"],
                    })
                    st.write(f"✅ Transcribed — Language: {lang_name}")
                progress.progress((i + 1) / len(audio_path))

            with st.status("🧠 Generating playlist summary..."):
                summary = summarize_playlist(all_transcripts, style=summary_style)

            st.markdown("## 📋 Playlist Summary")
            for m in meta:
                st.markdown(f"**{m['title']}** · {format_duration(m['duration'])}")
            st.markdown("---")
            st.markdown('<div class="summary-box">', unsafe_allow_html=True)
            st.markdown(summary)
            st.markdown('</div>', unsafe_allow_html=True)

            st.download_button(
                "💾 Download summary",
                data=summary,
                file_name="playlist_summary.txt",
                mime="text/plain",
            )

        # ── Single video mode ─────────────────────────────────────────────
        else:
            # Show video metadata
            st.markdown('<div class="meta-card">', unsafe_allow_html=True)
            col_thumb, col_info = st.columns([1, 3])
            with col_thumb:
                if meta.get("thumbnail"):
                    st.image(meta["thumbnail"], use_column_width=True)
            with col_info:
                st.markdown(f"**{meta['title']}**")
                st.markdown(f"⏱️ Duration: {format_duration(meta['duration'])}")
                st.markdown(f"🔗 [Open on YouTube]({meta['url']})")
            st.markdown('</div>', unsafe_allow_html=True)

            # Step 2: Transcribe
            with st.status("🎙️ Transcribing audio...", expanded=True) as status:
                st.write(f"Running Whisper ({whisper_size} model)...")
                result = transcribe(audio_path, model_size=whisper_size)
                lang_code = result["language"]
                lang_name = get_whisper_language_name(lang_code)
                st.write(f"✅ Transcription complete")
                status.update(label="✅ Transcription done", state="complete")

            # Language detection display
            lang_msg = get_language_message(lang_code, lang_name)
            st.markdown(lang_msg)

            # Step 3: Summarize
            transcript_text = result["text"]
            segments = result["segments"]

            # Use timestamped version if timestamps style selected
            if summary_style == "timestamps":
                from pipeline.transcriber import get_transcript_with_timestamps
                transcript_for_summary = get_transcript_with_timestamps(segments)
            else:
                transcript_for_summary = transcript_text

            with st.status("🧠 Generating summary...", expanded=True) as status:
                st.write(f"Sending to GPT (style: {summary_style})...")
                summary = summarize(
                    transcript=transcript_for_summary,
                    style=summary_style,
                    video_title=meta["title"],
                    language=lang_name,
                )
                status.update(label="✅ Summary ready", state="complete")

            # Display summary
            st.markdown("## 📝 Summary")
            st.markdown('<div class="summary-box">', unsafe_allow_html=True)
            st.markdown(summary)
            st.markdown('</div>', unsafe_allow_html=True)

            # Download button
            st.download_button(
                "💾 Download summary",
                data=f"# {meta['title']}\n\nLanguage: {lang_name}\n\n{summary}",
                file_name="summary.txt",
                mime="text/plain",
            )

            # Full transcript (optional)
            if show_transcript:
                st.markdown("---")
                st.markdown("## 📄 Full Transcript")
                if segments:
                    with st.expander("View transcript with timestamps", expanded=False):
                        from pipeline.transcriber import get_transcript_with_timestamps
                        st.text(get_transcript_with_timestamps(segments))
                else:
                    with st.expander("View transcript", expanded=False):
                        st.text(transcript_text)

    except Exception as e:
        st.error(f"❌ Something went wrong: {str(e)}")
        st.markdown("""
        **Common fixes:**
        - Make sure the URL is a valid public YouTube video
        - Private or age-restricted videos cannot be downloaded
        - Check your internet connection
        - Make sure ffmpeg is installed correctly
        """)

elif summarize_btn and not url:
    st.warning("⚠️ Please paste a YouTube URL first.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#9ca3af; font-size:0.85rem;'>"
    "Built with Whisper · OpenAI · Streamlit &nbsp;|&nbsp; "
    "By <a href='https://www.linkedin.com/in/muneera-ibrahim-79561a255' target='_blank'>Muneera Ibrahim</a>"
    "</p>",
    unsafe_allow_html=True,
)
