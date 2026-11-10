"""
FAQ Chatbot v2 - a clean, keyword-based customer support assistant.

New in this version:
  * Typing (streaming) effect for answers, with an on/off toggle
  * Typo-tolerant matching ("shiping" still finds Shipping)
  * Clickable "related question" suggestions after every answer
  * Thumbs up / down feedback on answers
  * Searchable quick-FAQ list in the sidebar
  * Message timestamps
  * Session stats (questions asked, helpful answers)
  * Download the conversation as a text file
  * "help" command that lists everything the bot can answer

Run with:
    pip install streamlit
    streamlit run app.py
"""

import difflib
import re
import time
from datetime import datetime

import streamlit as st

# ----------------------------------------------------------------------------
# PAGE CONFIG (must be the first Streamlit call)
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="FAQ Assistant",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# FAQ DATASET
# Each entry has:
#   id       - short unique name (used for "related" links)
#   label    - text on the sidebar quick-access button
#   question - the question shown in chat when a button is clicked
#   keywords - words/phrases used for matching (case-insensitive).
#              Single words match the START of a word, so "ship" matches
#              "shipping". Multi-word phrases score higher than single words.
#   related  - ids of FAQs suggested after this answer
#   answer   - the chatbot's reply (Markdown supported)
# NOTE: Replace the placeholder contact details with your real ones.
# ----------------------------------------------------------------------------
FAQS = [
    {
        "id": "hours",
        "label": "🕒 Business Hours",
        "question": "What are your business hours?",
        "keywords": [
            "business hours", "opening hours", "working hours", "store hours",
            "hours", "open", "close", "closing", "timing", "timings",
            "schedule", "weekend", "sunday", "saturday",
        ],
        "related": ["support", "shipping"],
        "answer": (
            "**Our business hours are:**\n\n"
            "- Monday – Friday: 9:00 AM – 6:00 PM\n"
            "- Saturday: 10:00 AM – 4:00 PM\n"
            "- Sunday: Closed\n\n"
            "Our online store is open 24/7, so you can place orders any time!"
        ),
    },
    {
        "id": "shipping",
        "label": "🚚 Shipping & Delivery",
        "question": "How does shipping and delivery work?",
        "keywords": [
            "shipping", "delivery", "ship", "deliver", "courier", "dispatch",
            "how long", "arrive", "shipping cost", "shipping time",
            "international", "express",
        ],
        "related": ["tracking", "returns", "payment"],
        "answer": (
            "**Shipping & Delivery**\n\n"
            "- Standard shipping: 3–5 business days\n"
            "- Express shipping: 1–2 business days\n"
            "- Free standard shipping on orders over USD 50\n"
            "- We ship to most countries; international delivery takes "
            "7–14 business days\n\n"
            "Orders are dispatched within 24 hours on business days."
        ),
    },
    {
        "id": "returns",
        "label": "↩️ Return Policy",
        "question": "What is your return policy?",
        "keywords": [
            "return policy", "return", "refund", "exchange", "money back",
            "send back", "replace", "replacement", "damaged", "defective",
            "cancel",
        ],
        "related": ["support", "tracking"],
        "answer": (
            "**Return Policy**\n\n"
            "- You can return most items within **30 days** of delivery\n"
            "- Items must be unused and in their original packaging\n"
            "- Refunds are issued to your original payment method within "
            "5–7 business days after we receive the item\n"
            "- Damaged or defective items are replaced free of charge\n\n"
            "To start a return, contact our support team with your order number."
        ),
    },
    {
        "id": "payment",
        "label": "💳 Payment Options",
        "question": "Which payment options do you accept?",
        "keywords": [
            "payment options", "payment", "pay", "credit card", "debit card",
            "card", "paypal", "upi", "cash on delivery", "cod", "net banking",
            "wallet", "checkout", "invoice", "accept",
        ],
        "related": ["discounts", "shipping"],
        "answer": (
            "**Accepted Payment Methods**\n\n"
            "- Credit and debit cards (Visa, Mastercard, American Express)\n"
            "- PayPal\n"
            "- UPI and net banking\n"
            "- Digital wallets (Apple Pay, Google Pay)\n"
            "- Cash on delivery (select locations)\n\n"
            "All transactions are encrypted and secure."
        ),
    },
    {
        "id": "tracking",
        "label": "📦 Track My Order",
        "question": "How can I track my order?",
        "keywords": [
            "track my order", "order tracking", "track", "tracking",
            "where is my order", "order status", "status", "shipment",
            "parcel", "package", "whereabouts", "tracking number",
        ],
        "related": ["shipping", "support"],
        "answer": (
            "**Tracking Your Order**\n\n"
            "1. Check the confirmation email we sent when your order shipped\n"
            "2. Click the **Track Order** link inside that email\n"
            "3. Or log in to your account and open **My Orders**\n\n"
            "Tracking details are usually available within 24 hours of dispatch."
        ),
    },
    {
        "id": "support",
        "label": "🧑‍💼 Contact Human Support",
        "question": "How can I contact a human support agent?",
        "keywords": [
            "human support", "human", "agent", "representative", "support",
            "contact", "customer service", "talk to someone", "speak to",
            "phone", "call", "email", "complaint", "help desk", "person",
        ],
        "related": ["hours", "returns"],
        "answer": (
            "**Contact Our Support Team**\n\n"
            "- Email: support@example.com\n"
            "- Phone: +1 (800) 555-0199\n"
            "- Hours: Monday – Friday, 9:00 AM – 6:00 PM\n\n"
            "We typically reply to emails within 24 hours."
        ),
    },
    {
        "id": "password",
        "label": "🔐 Account & Password",
        "question": "How do I reset my password?",
        "keywords": [
            "reset password", "forgot password", "password", "login",
            "log in", "sign in", "account", "username", "locked",
        ],
        "related": ["support"],
        "answer": (
            "**Resetting Your Password**\n\n"
            "1. Go to the **Login** page and click **Forgot Password**\n"
            "2. Enter the email address linked to your account\n"
            "3. Open the reset link we email you and choose a new password\n\n"
            "If you don't receive the email, check your spam folder or "
            "contact our support team."
        ),
    },
    {
        "id": "discounts",
        "label": "🎁 Discounts & Offers",
        "question": "Do you have any discount codes or offers?",
        "keywords": [
            "discount", "coupon", "promo", "promo code", "offer", "offers",
            "sale", "voucher", "deal", "deals", "code",
        ],
        "related": ["payment", "shipping"],
        "answer": (
            "**Discounts & Offers**\n\n"
            "- Subscribe to our newsletter for 10% off your first order\n"
            "- Seasonal sales run throughout the year\n"
            "- Enter your promo code in the **Promo Code** box at checkout\n\n"
            "Only one promo code can be used per order."
        ),
    },
]

# Quick lookup: FAQ id -> FAQ dictionary
FAQ_BY_ID = {faq["id"]: faq for faq in FAQS}

# Suggestions shown on the greeting, help and fallback messages
DEFAULT_SUGGESTIONS = ["shipping", "returns", "tracking", "support"]

# Small-talk word sets (whole-word matching)
GREETING_WORDS = {"hi", "hello", "hey", "hii", "greetings", "namaste"}
THANKS_WORDS = {"thanks", "thank", "thankyou", "thx", "cheers"}
BYE_WORDS = {"bye", "goodbye", "cya"}
HELP_WORDS = {"help", "menu", "topics", "options"}

# How similar (0-1) a typed word must be to a keyword to count as a typo match
FUZZY_CUTOFF = 0.88

GREETING_MESSAGE = (
    "👋 **Hello! Welcome to our FAQ Assistant.**\n\n"
    "I can help with business hours, shipping, returns, payments, order "
    "tracking, and contacting our support team.\n\n"
    "Type your question below, pick a topic from the sidebar, or tap one of "
    "the suggestions here."
)


# ----------------------------------------------------------------------------
# CHATBOT LOGIC
# ----------------------------------------------------------------------------
def tokenize(text: str) -> list:
    """Lower-case the text and return the list of words in it."""
    return re.findall(r"[a-z0-9']+", text.lower())


def find_best_faq(user_message: str):
    """
    Score every FAQ against the user's message and return the best match.

    Scoring: each matched keyword adds points equal to the number of words in
    the keyword, so specific phrases ("return policy") beat generic words
    ("return"). Single keywords of 5+ letters also get 1 point if the user
    made a small typo ("shiping" ~ "shipping"). Returns None if no match.
    """
    text = user_message.lower()
    tokens = sorted(set(tokenize(text)))
    best_faq, best_score = None, 0

    for faq in FAQS:
        score = 0
        for keyword in faq["keywords"]:
            kw = keyword.lower()
            # \b = word boundary at the START only, so "ship" matches
            # "shipping" but "hip" would not match "ship".
            if re.search(r"\b" + re.escape(kw), text):
                score += len(kw.split())
            elif " " not in kw and len(kw) >= 5 and difflib.get_close_matches(
                kw, tokens, n=1, cutoff=FUZZY_CUTOFF
            ):
                score += 1
        if score > best_score:
            best_faq, best_score = faq, score

    return best_faq if best_score > 0 else None


def get_response(user_message: str):
    """
    Return (reply_text, faq_id, related_ids) for a user message.
    faq_id is None for small talk, help and fallback replies.
    """
    words = set(tokenize(user_message))

    faq = find_best_faq(user_message)
    if faq is not None:
        return faq["answer"], faq["id"], faq["related"]

    if words & HELP_WORDS:
        topics = "\n".join(f"- {f['label']}" for f in FAQS)
        return (
            "😊 **Happy to help!** Here's what I can answer:\n\n"
            f"{topics}\n\n"
            "Just type your question or tap a suggestion below."
        ), None, DEFAULT_SUGGESTIONS
    if words & GREETING_WORDS and len(words) <= 4:
        return "Hello again! 😊 What would you like to know?", None, DEFAULT_SUGGESTIONS
    if words & THANKS_WORDS:
        return "You're very welcome! 😊 Is there anything else I can help with?", None, []
    if words & BYE_WORDS:
        return "Goodbye! 👋 Have a wonderful day.", None, []

    return (
        "🤔 Sorry, I couldn't find an answer to that.\n\n"
        "Try rephrasing your question, or tap one of the suggestions below. "
        "You can also reach a human agent at **support@example.com**."
    ), None, DEFAULT_SUGGESTIONS


def stream_text(text: str):
    """Yield text a few characters at a time to create a typing effect."""
    for chunk in re.findall(r"\S+\s*|\s+", text):
        yield chunk
        time.sleep(0.015)


# ----------------------------------------------------------------------------
# SESSION STATE HELPERS
# ----------------------------------------------------------------------------
def new_message(role, content, faq_id=None, related=None, animate=False):
    """Create a chat message dictionary with a unique id and timestamp."""
    st.session_state.msg_counter += 1
    return {
        "id": st.session_state.msg_counter,
        "role": role,
        "content": content,
        "time": datetime.now().strftime("%I:%M %p"),
        "faq_id": faq_id,          # set only for real FAQ answers
        "related": related or [],  # ids of suggested follow-up FAQs
        "feedback": None,          # None, "up" or "down"
        "animate": animate,        # True -> play typing effect once
    }


def greeting_message():
    """The friendly first message shown at start and after clearing."""
    return new_message(
        "assistant", GREETING_MESSAGE, related=DEFAULT_SUGGESTIONS
    )


def init_state() -> None:
    """Create session variables on first run (they persist across reruns)."""
    if "msg_counter" not in st.session_state:
        st.session_state.msg_counter = 0
    if "messages" not in st.session_state:
        st.session_state.messages = [greeting_message()]
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None


def clear_chat() -> None:
    """Callback: reset the conversation back to the greeting."""
    st.session_state.messages = [greeting_message()]
    st.session_state.pending_query = None


def queue_question(question: str) -> None:
    """Callback: store a clicked FAQ question to be processed on rerun."""
    st.session_state.pending_query = question


def set_feedback(msg_id: int, value: str) -> None:
    """Callback: record thumbs up/down for a message."""
    for message in st.session_state.messages:
        if message["id"] == msg_id:
            message["feedback"] = value
            break


def build_transcript() -> str:
    """Turn the conversation into plain text for download."""
    lines = ["FAQ Assistant - Chat Transcript", "=" * 31, ""]
    for message in st.session_state.messages:
        who = "You" if message["role"] == "user" else "Assistant"
        lines.append(f"[{message['time']}] {who}:")
        lines.append(message["content"].replace("**", ""))
        lines.append("")
    return "\n".join(lines)


init_state()

# ----------------------------------------------------------------------------
# STYLING (small, safe tweaks)
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Full-width, left-aligned sidebar buttons */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stDownloadButton > button {
        width: 100%;
        justify-content: flex-start;
        text-align: left;
        border-radius: 10px;
    }
    /* Rounded suggestion / feedback buttons in the chat */
    [data-testid="stMain"] .stButton > button { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# HANDLE INPUT
# Done before the sidebar is drawn so the stats and download are up to date.
# (st.chat_input always sticks to the bottom of the page wherever it is called.)
# ----------------------------------------------------------------------------
# Get input: a clicked FAQ/suggestion takes priority, otherwise the chat box.
typed_input = st.chat_input("Type your question here...")
user_input = st.session_state.pending_query or typed_input
st.session_state.pending_query = None

if user_input and user_input.strip():
    user_input = user_input.strip()
    reply, faq_id, related = get_response(user_input)
    st.session_state.messages.append(new_message("user", user_input))
    st.session_state.messages.append(
        new_message("assistant", reply, faq_id, related, animate=True)
    )

# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚡ Quick FAQs")
    st.caption("Click a topic for an instant answer.")

    search = st.text_input(
        "Search topics",
        key="faq_search",
        placeholder="🔍 Search topics...",
        label_visibility="collapsed",
    ).strip().lower()

    shown = 0
    for i, faq in enumerate(FAQS):
        haystack = " ".join(
            [faq["label"], faq["question"]] + faq["keywords"]
        ).lower()
        if search and search not in haystack:
            continue
        shown += 1
        st.button(
            faq["label"],
            key=f"faq_btn_{i}",
            on_click=queue_question,
            args=(faq["question"],),
        )
    if shown == 0:
        st.caption("No matching topics. Try typing your question in the chat!")

    st.divider()
    st.subheader("⚙️ Options")
    st.toggle("Typing effect", value=True, key="typing_effect")

    # Session stats are calculated from the current conversation
    asked = sum(1 for m in st.session_state.messages if m["role"] == "user")
    helpful = sum(1 for m in st.session_state.messages if m["feedback"] == "up")
    col_a, col_b = st.columns(2)
    col_a.metric("Questions", asked)
    col_b.metric("Helpful 👍", helpful)

    st.divider()
    st.download_button(
        "⬇️ Download Chat",
        data=build_transcript(),
        file_name="faq_chat_transcript.txt",
        mime="text/plain",
        key="download_btn",
    )
    st.button("🗑️ Clear Chat History", key="clear_chat_btn", on_click=clear_chat)

# ----------------------------------------------------------------------------
# MAIN PAGE
# ----------------------------------------------------------------------------
st.title("💬 FAQ Assistant")
st.caption("Instant answers to your most common questions, available 24/7.")

# Render the conversation.
last_index = len(st.session_state.messages) - 1
for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # Typing effect plays once for a brand-new assistant reply.
        if message["animate"]:
            message["animate"] = False  # set first so a rerun never replays it
            if st.session_state.get("typing_effect", True) and hasattr(
                st, "write_stream"
            ):
                st.write_stream(stream_text(message["content"]))
            else:
                st.markdown(message["content"])
        else:
            st.markdown(message["content"])

        st.caption(message["time"])

        if message["role"] != "assistant":
            continue

        # Thumbs up/down feedback for real FAQ answers.
        if message["faq_id"]:
            if message["feedback"] is None:
                st.caption("Was this answer helpful?")
                col_up, col_down, _ = st.columns([1, 1, 6])
                col_up.button(
                    "👍",
                    key=f"up_{message['id']}",
                    help="Helpful",
                    on_click=set_feedback,
                    args=(message["id"], "up"),
                )
                col_down.button(
                    "👎",
                    key=f"down_{message['id']}",
                    help="Not helpful",
                    on_click=set_feedback,
                    args=(message["id"], "down"),
                )
            elif message["feedback"] == "up":
                st.caption("✅ Thanks for your feedback!")
            else:
                st.caption(
                    "🙏 Sorry about that. Please contact our support team "
                    "for more help."
                )

        # Related-question suggestions only under the latest message.
        if index == last_index and message["related"]:
            st.caption("You might also want to know:")
            for related_id in message["related"]:
                related_faq = FAQ_BY_ID[related_id]
                st.button(
                    related_faq["question"],
                    key=f"rel_{message['id']}_{related_id}",
                    on_click=queue_question,
                    args=(related_faq["question"],),
                )