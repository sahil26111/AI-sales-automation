import os
from getpass import getpass

os.environ["GEMINI_API_KEY"] = getpass(
    "Paste your Gemini API key (input is hidden): "
)

print("Gemini key loaded for this Colab session.")

import os
from google import genai

# Connect using your Google AI Studio API key
gemini_client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

# Generate a response using the updated model
response = gemini_client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Classify this complaint in one sentence: My parcel arrived late."
)

print(response.text)
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "/content/customer_support.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                email TEXT,
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                summary TEXT NOT NULL,
                reply TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

init_db()
print("Database created successfully.")
def analyze_ticket(message):
    prompt = f"""
You are an AI customer support assistant.

Analyze the customer complaint below.

CUSTOMER MESSAGE:
{message}

Return ONLY a valid JSON object with these fields:
{{
  "category": "Billing, Delivery, Technical, Refund,
               Account, Product, or Other",
  "priority": "Low, Medium, High, or Urgent",
  "summary": "A short summary of the issue",
  "sentiment": "Positive, Neutral, or Negative",
  "suggested_response": "A polite and professional reply"
}}

Rules:
- Do not invent order details, refund approvals, or delivery dates.
- Never claim that an action has already been completed.
- If details are missing, ask the customer for them.
- Use only information provided in the complaint.
- Keep the suggested response concise.
"""

    response = gemini_client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )

    result = json.loads(response.text)

    allowed_categories = {
        "Billing", "Delivery", "Technical", "Refund",
        "Account", "Product", "Other"
    }
    allowed_priorities = {"Low", "Medium", "High", "Urgent"}
    allowed_sentiments = {"Positive", "Neutral", "Negative"}

    if result.get("category") not in allowed_categories:
        result["category"] = "Other"

    if result.get("priority") not in allowed_priorities:
        result["priority"] = "Medium"

    if result.get("sentiment") not in allowed_sentiments:
        result["sentiment"] = "Neutral"

    for field in ("summary", "suggested_response"):
        if not isinstance(result.get(field), str) or not result[field].strip():
            raise ValueError(f"Missing or invalid field: {field}")

    return result

print("AI ticket analysis function is ready.")
def create_ticket(message):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Please enter a customer message.")

    analysis = analyze_ticket(message.strip())
    created_at = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO tickets (
                customer_message, category, priority, summary,
                sentiment, suggested_response, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message.strip(),
            analysis["category"],
            analysis["priority"],
            analysis["summary"],
            analysis["sentiment"],
            analysis["suggested_response"],
            "Pending Review",
            created_at
        ))

        ticket_id = cursor.lastrowid

    return {"ticket_id": ticket_id, **analysis}

print("Ticket creation function is ready.")
import sqlite3


def get_connection():
    return sqlite3.connect(DB_PATH)

def load_tickets():
    with get_connection() as conn:
        
        return pd.read_sql_query(
            "SELECT * FROM tickets ORDER BY id DESC",
            conn
        )

def show_dashboard():
    df = load_tickets()

    if df.empty:
        print("No tickets found. Add a customer complaint first.")
        return

    print("===== CUSTOMER SUPPORT DASHBOARD =====")
    print("Total tickets:", len(df))
    print("Pending review:", (df["status"] == "Pending Review").sum())
    print("Approved:", (df["status"] == "Approved").sum())
    print("Rejected:", (df["status"] == "Rejected").sum())

    print("\nPriority breakdown:")
    display(df["priority"].value_counts().rename_axis("Priority").to_frame("Count"))

    print("\nCategory breakdown:")
    display(df["category"].value_counts().rename_axis("Category").to_frame("Count"))

    print("\nRecent tickets:")
    # Displaying 'id' instead of 'ticket_id'
    display(df[[
        "id", "category", "priority",
        "status", "created_at"
    ]].head(20))

show_dashboard()
MODEL_NAME = "gemini-3.8-flash"
import json


def create_ticket(message):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Please enter a customer message.")

    analysis = analyze_ticket(message.strip())
    created_at = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO tickets (
                created_at, customer_name, email, message, category,
                priority, summary, reply, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            created_at,
            "Valued Customer",
            "customer@example.com",
            message.strip(),
            analysis["category"],
            analysis["priority"],
            analysis["summary"],
            analysis["suggested_response"],
            "Pending Review"
        ))
        ticket_id = cursor.lastrowid

    return {"ticket_id": ticket_id, **analysis}

# Run the function with a sample message to avoid the missing argument error
test_message = "My payment was deducted, but my order was not confirmed."
result = create_ticket(test_message)
print("Ticket Created Successfully!")
print("Ticket ID:", result["ticket_id"])
print("AI Summary:", result["summary"])
from IPython.display import display
import ipywidgets as widgets

message_box = widgets.Textarea(
    value="My payment was deducted, but my order was not confirmed.",
    placeholder="Enter a customer complaint...",
    description="Complaint:",
    layout=widgets.Layout(width="100%", height="120px")
)

submit_button = widgets.Button(
    description="Analyze Ticket",
    button_style="primary",
    icon="check"
)

output_box = widgets.Output()

def on_submit_clicked(button):
    with output_box:
        output_box.clear_output()

        try:
            result = create_ticket(message_box.value)

            print("Ticket ID:", result["ticket_id"])
            print("Category:", result["category"])
            print("Priority:", result["priority"])
            print("Sentiment:", result["sentiment"])
            print("Summary:", result["summary"])
            print("\nSuggested response:")
            print(result["suggested_response"])
            print("\nStatus: Pending Review")
        except Exception as e:
            print("Error:", str(e))

submit_button.on_click(on_submit_clicked)

display(message_box, submit_button, output_box)
def review_ticket(ticket_id, decision, edited_response=None):
    decision = decision.strip().lower()

    if decision not in {"approve", "reject"}:
        raise ValueError("Decision must be approve or reject.")

    with get_connection() as conn:
        # Updated to use the correct database columns: 'reply' instead of 'suggested_response' and 'id' instead of 'ticket_id'
        row = conn.execute("""
            SELECT reply, status
            FROM tickets
            WHERE id = ?
        """, (ticket_id,)).fetchone()

        if row is None:
            raise ValueError("Ticket ID not found.")

        if row[1] != "Pending Review":
            raise ValueError("This ticket has already been reviewed.")

        if decision == "approve":
            final_response = (
                edited_response.strip()
                if edited_response and edited_response.strip()
                else row[0]
            )
            # We update 'reply' directly and change the status
            conn.execute("""
                UPDATE tickets
                SET status = 'Approved', reply = ?
                WHERE id = ?
            """, (final_response, ticket_id))
        else:
            conn.execute("""
                UPDATE tickets
                SET status = 'Rejected'
                WHERE id = ?
            """, (ticket_id,))

    print(f"Ticket {ticket_id}: {decision.upper()}")

# Example: inspect pending tickets before deciding using the correct schema columns
pending = load_tickets()
display(pending.loc[
    pending["status"] == "Pending Review",
    ["id", "message", "reply"]
])
review_ticket(ticket_id=1, decision="approve")
from google.colab import files

export_df = load_tickets()

csv_path = "/content/customer_support_tickets.csv"
export_df.to_csv(csv_path, index=False)

print("Exported", len(export_df), "tickets.")
files.download(csv_path)
show_dashboard()

print("\n===== FINAL PROJECT STATUS =====")
final_df = load_tickets()

if not final_df.empty:
    print("Tickets classified:", len(final_df))
    print("Average tickets per category:")
    display(final_df.groupby("category").size().reset_index(
        name="Ticket Count"
    ))

    print("\nReview status:")
    display(final_df["status"].value_counts().to_frame("Tickets"))
    
