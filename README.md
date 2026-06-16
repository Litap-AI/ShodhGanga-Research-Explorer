# IIT Patna ShodhGanga Research Explorer

## 📸 Application Preview

### 🔍 Interactive Filters & Topic Discovery
![Main Dashboard Interface](dashboard.png)

# 🎓 IIT Patna - ShodhGanga Research Explorer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge.svg)](https://share.streamlit.io/)
[![Python Version](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.python.org/)
A Streamlit app for exploring IIT Patna PhD thesis records from a local ShodhGanga CSV dataset.

The app lets you:

- Filter theses by domain keywords
- Search by topic or researcher
- Open public thesis records on ShodhGanga
- Generate fast local summaries instantly
- Optionally generate AI summaries using a Hugging Face model

## Project Files

Keep these files in the same folder:

```text
app.py
shodhganga_final_clean.csv
requirements.txt
```

The CSV file must be named exactly:

```text
shodhganga_final_clean.csv
```

## Required CSV Columns

Your CSV should contain these columns:

```text
Sr No
Topic
Researcher
Date
Keywords
Abstract_Text
Link
```

## Installation

Create and activate a virtual environment if you want:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run The App

```bash
streamlit run app.py
```

Then open the URL shown in the terminal, usually:

```text
https://shodhganga-research-explorer-iitpatna.streamlit.app/
```

## Summary Modes

The sidebar has two summary modes:

- **Fast summary**: Instant, no AI model loading. Best for demos and normal use.
- **AI summary**: Uses a Hugging Face summarization model. Better quality, but slower on the first run.

The first AI summary may take time because the model has to download and load into memory.

## Troubleshooting

If the app says the CSV is missing, make sure `shodhganga_final_clean.csv` is in the same folder as `app.py`.

If AI summarization fails, reinstall dependencies:

```bash
pip install --upgrade -r requirements.txt
```

If the AI model is too slow, use **Fast summary** from the sidebar.
