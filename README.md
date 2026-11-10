# 💬 FAQ Assistant

A clean, keyword-based FAQ chatbot built with Python and [Streamlit](https://streamlit.io). It answers common customer questions (business hours, shipping, returns, payments, order tracking, support and more) instantly, with no external APIs or databases.

## Features

- **Native chat interface** using `st.chat_message` and `st.chat_input`, with history kept in `st.session_state`
- **Friendly greeting** loaded automatically on start
- **Keyword matching** that is case-insensitive, scores multi-word phrases higher, and matches word prefixes ("ship" finds "shipping")
- **Typo tolerance** so misspellings like "shiping" or "refnd" still find the right answer
- **Quick FAQ buttons** in the sidebar, plus a search box to filter them
- **Related-question suggestions** shown after each answer
- **Thumbs up / down feedback** on answers
- **Typing effect** for replies, with an on/off toggle
- **Message timestamps** and **session stats** (questions asked, helpful answers)
- **Download chat** as a `.txt` transcript
- **Clear Chat History** button to reset the conversation
- **`help` command** that lists everything the bot can answer
- **Polite fallback** with clickable suggestions when a question isn't understood

## Project Structure

```
.
├── app.py             # The complete application
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Getting Started

**Requirements:** Python 3.9+ and Streamlit 1.31 or newer.

1. Put the project files in one folder and open a terminal there.
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   streamlit run app.py
   ```
5. Open the local URL shown in the terminal (usually http://localhost:8501).

## Customizing

### Replace the placeholder details
Open `app.py` and update the sample contact details (`support@example.com`, `+1 (800) 555-0199`) and the policy text in the `FAQS` list to match your real business.

### Add a new FAQ
Add one dictionary to the `FAQS` list in `app.py`:

```python
{
    "id": "warranty",                      # short unique name
    "label": "🛡️ Warranty",                # sidebar button text
    "question": "What does the warranty cover?",
    "keywords": ["warranty", "guarantee", "defect cover"],
    "related": ["returns", "support"],     # ids of suggested follow-ups
    "answer": "**Warranty**\n\nAll products include a 1-year warranty.",
},
```

The sidebar button, search, matching and related suggestions pick it up automatically. Every id used in `related` must match the `id` of an existing FAQ.

### Tune the matching
- **Keywords:** add more words or phrases to an FAQ's `keywords` list. Longer phrases score higher.
- **Typo sensitivity:** change `FUZZY_CUTOFF` near the top of the logic section. Higher values (up to 1.0) are stricter, lower values are more forgiving.

## How Matching Works

1. The user's message is lower-cased.
2. Each FAQ is scored: every matched keyword adds points equal to its number of words, so "return policy" beats "return".
3. Long single keywords (5+ letters) also earn a point on a close fuzzy match to catch typos.
4. The highest-scoring FAQ wins. If nothing matches, the bot checks for small talk (hello, thanks, bye, help) and otherwise shows the fallback reply with suggestions.

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | Run `python -m streamlit run app.py` |
| The typing effect doesn't play | Upgrade Streamlit: `pip install --upgrade streamlit` |
| Port already in use | Run `streamlit run app.py --server.port 8502` |

## Ideas for Next Steps

- Load FAQs from a JSON or CSV file so non-developers can edit them
- Add an AI-powered fallback for questions the keywords don't cover
- Support multiple languages
- Log unanswered questions to find gaps in your FAQ list
