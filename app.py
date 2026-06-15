import os
import re

import pandas as pd
import streamlit as st


CSV_FILE = "shodhganga_final_clean.csv"
SUMMARY_MODEL = "sshleifer/distilbart-cnn-12-6"


st.set_page_config(
    page_title="IIT Patna Research Explorer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .thesis-card {
        padding: 18px 20px;
        border-radius: 8px;
        background-color: #f8f9fa;
        margin-bottom: 12px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }
    .thesis-title {
        margin-top: 0;
        margin-bottom: 10px;
        color: #111827 !important;
        font-size: 22px;
        line-height: 1.3;
    }
    .thesis-meta {
        color: #374151 !important;
        font-size: 14px;
        margin-bottom: 0;
    }
    .keyword-tag {
        display: inline-block;
        background-color: #e9ecef;
        color: #495057;
        padding: 4px 8px;
        border-radius: 4px;
        margin-right: 5px;
        margin-bottom: 5px;
        font-size: 12px;
        font-family: monospace;
    }
    .open-link {
        display: inline-block;
        background-color: #ffffff;
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b;
        padding: 0.45rem 0.8rem;
        border-radius: 4px;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 14px;
    }
    .open-link:hover {
        background-color: #fff5f5;
        color: #e03131 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("🎓 IIT Patna - ShodhGanga Research Explorer")
st.subheader(
    "Filter PhD theses by domain keywords, read AI summaries, and open public thesis records."
)


def clean_text(value, default=""):
    if pd.isna(value):
        return default
    return str(value).strip()


def clean_keyword(keyword):
    keyword = str(keyword).strip().strip(".")
    keyword = keyword.replace(" xiii", "").replace(" xiv", "")
    keyword = re.sub(r"\s+", " ", keyword)
    return keyword.title()


def html_escape(value):
    value = str(value)
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


@st.cache_data(show_spinner=False)
def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(), f"`{CSV_FILE}` was not found. Put it in the same folder as `app.py`."

    try:
        df = pd.read_csv(CSV_FILE, skiprows=1)
    except Exception:
        df = pd.read_csv(CSV_FILE)

    df.columns = df.columns.str.strip()

    required_columns = [
        "Sr No",
        "Topic",
        "Researcher",
        "Date",
        "Keywords",
        "Abstract_Text",
        "Link",
    ]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        return pd.DataFrame(), "Missing required CSV columns: " + ", ".join(missing_columns)

    df["Sr No"] = df["Sr No"].apply(lambda x: clean_text(x, "N/A"))
    df["Topic"] = df["Topic"].apply(lambda x: clean_text(x, "Untitled Thesis"))
    df["Researcher"] = df["Researcher"].apply(lambda x: clean_text(x, "IIT Patna Scholar"))
    df["Date"] = df["Date"].apply(lambda x: clean_text(x, "Recent"))
    df["Keywords"] = df["Keywords"].apply(lambda x: clean_text(x, "General Research"))
    df["Abstract_Text"] = df["Abstract_Text"].apply(lambda x: clean_text(x, ""))
    df["Link"] = df["Link"].apply(lambda x: clean_text(x, ""))

    return df, None


@st.cache_resource(show_spinner=False)
def load_summary_model():
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(SUMMARY_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARY_MODEL)
    return tokenizer, model


def get_all_keywords(df):
    all_keywords = set()
    for keyword_string in df["Keywords"]:
        for keyword in str(keyword_string).split(","):
            keyword = clean_keyword(keyword)
            if len(keyword) > 2 and "Keywords" not in keyword and keyword.lower() != "nan":
                all_keywords.add(keyword)
    return sorted(all_keywords)


def get_row_keywords(keyword_string):
    tags = []
    for keyword in str(keyword_string).split(","):
        keyword = clean_keyword(keyword)
        if keyword and "Keywords" not in keyword and keyword.lower() != "nan":
            tags.append(keyword)
    return tags


def clean_abstract(raw_text):
    cleaned_abstract = re.sub(
        r"(Abstract|Keywords:.*)",
        "",
        str(raw_text),
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()
    cleaned_abstract = " ".join(cleaned_abstract.split())

    if not cleaned_abstract:
        return None

    return cleaned_abstract


@st.cache_data(show_spinner=False)
def summarize_fast(raw_text):
    cleaned_abstract = clean_abstract(raw_text)
    if not cleaned_abstract:
        return None, "Text context extraction is unavailable for this item."

    sentences = re.split(r"(?<=[.!?])\s+", cleaned_abstract)
    sentences = [sentence.strip() for sentence in sentences if len(sentence.strip()) > 30]
    if not sentences:
        return cleaned_abstract[:500], None

    summary = " ".join(sentences[:4])
    return summary[:900], None


@st.cache_data(show_spinner=False)
def summarize_with_ai(raw_text):
    cleaned_abstract = clean_abstract(raw_text)
    if not cleaned_abstract:
        return None, "Text context extraction is unavailable for this item."

    truncated_text = cleaned_abstract[:1500]
    tokenizer, model = load_summary_model()
    inputs = tokenizer(
        truncated_text,
        return_tensors="pt",
        max_length=1024,
        truncation=True,
    )
    output_ids = model.generate(
        **inputs,
        max_length=120,
        min_length=45,
        num_beams=4,
        do_sample=False,
        early_stopping=True,
    )
    return tokenizer.decode(output_ids[0], skip_special_tokens=True), None


df, load_error = load_data()

if load_error:
    st.error(load_error)
    st.stop()

if df.empty:
    st.info("No thesis records found in the CSV file.")
    st.stop()


all_keywords = get_all_keywords(df)

st.sidebar.header("🔍 Filter Options")
selected_keywords = st.sidebar.multiselect(
    "Select Domain Keywords",
    all_keywords,
    placeholder="Choose tags, for example Deep Learning",
)

summary_mode = st.sidebar.radio(
    "Summary Mode",
    ["Fast summary", "AI summary"],
    help="Fast summary is instant. AI summary is slower but rewrites the abstract more naturally.",
)

search_text = st.sidebar.text_input(
    "Search topic or researcher",
    placeholder="Type a name or topic",
)

filtered_df = df.copy()

if selected_keywords:
    filtered_df = filtered_df[
        filtered_df["Keywords"].apply(
            lambda value: any(keyword.lower() in value.lower() for keyword in selected_keywords)
        )
    ]

if search_text.strip():
    query = search_text.strip().lower()
    filtered_df = filtered_df[
        filtered_df["Topic"].str.lower().str.contains(query, na=False)
        | filtered_df["Researcher"].str.lower().str.contains(query, na=False)
    ]

st.sidebar.markdown("---")
st.sidebar.metric("Matching Theses Found", f"{len(filtered_df)} / {len(df)}")


if filtered_df.empty:
    st.info("No research items match your current filters.")
    st.stop()


for _, row in filtered_df.iterrows():
    topic = html_escape(row["Topic"])
    researcher = html_escape(row["Researcher"])
    date = html_escape(row["Date"])
    serial_no = html_escape(row["Sr No"])
    link = html_escape(row["Link"])

    st.markdown(
        f"""
        <div class="thesis-card">
            <h3 class="thesis-title" style="color:#111827 !important;">📄 {topic}</h3>
            <p class="thesis-meta" style="color:#374151 !important;">
                <strong>👤 Researcher:</strong> {researcher}
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <strong>📅 Submission Year:</strong> {date}
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <strong>🔢 Serial Identifier:</strong> IITP-#{serial_no}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tags = get_row_keywords(row["Keywords"])[:8]
    if tags:
        tags_html = " ".join(
            f'<span class="keyword-tag">🏷️ {html_escape(tag)}</span>' for tag in tags
        )
        st.markdown(tags_html, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 4])

    with col1:
        summarize_clicked = st.button(
            "✨ Summarize",
            key=f"summary_{row['Sr No']}",
            type="primary",
        )

    with col2:
        if row["Link"]:
            st.markdown(
                f'<a class="open-link" href="{link}" target="_blank">🌐 Open Full Record on ShodhGanga</a>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("No public link available for this record.")

    if summarize_clicked:
        try:
            if summary_mode == "AI summary":
                spinner_text = "Loading AI model and summarizing abstract..."
                summarize_function = summarize_with_ai
                summary_heading = "🤖 AI Abstract Summary"
            else:
                spinner_text = "Creating fast summary..."
                summarize_function = summarize_fast
                summary_heading = "📝 Fast Abstract Summary"

            with st.spinner(spinner_text):
                summary_text, summary_error = summarize_function(row["Abstract_Text"])

            if summary_error:
                st.error(summary_error)
            else:
                st.markdown(f"##### {summary_heading}")
                st.success(summary_text)
        except Exception as error:
            st.error(f"Summarization failed: {error}")
            st.info(
                "Install the required packages with: `pip install streamlit pandas transformers torch`"
            )

    st.markdown("<br><hr style='border-top: 1px dashed #cccccc;'><br>", unsafe_allow_html=True)
