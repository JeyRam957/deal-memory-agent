import json
import os

from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

BANK_ID = "deal-memory-agent"

hindsight = Hindsight(
    base_url=os.getenv("HINDSIGHT_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

with open("data/deal_data.json", "r", encoding="utf-8") as f:
    deals = json.load(f)

for deal in deals:

    for conversation in deal["conversations"]:

        memory = f"""
Deal ID: {deal['deal_id']}
Company: {deal['company']}
Contact: {deal['contact']}
Role: {deal['role']}
Industry: {deal['industry']}
Deal Stage: {deal['deal_stage']}
Competitor: {deal['competitor']}

Conversation Date: {conversation['date']}

Conversation Summary:
{conversation['summary']}

Customer Statement:
{conversation['customer_statement']}

Objections:
{', '.join(conversation['objections'])}

Next Action:
{deal['next_action']}
"""

        hindsight.retain(
            bank_id=BANK_ID,
            content=memory
        )

        print(
            f"Stored {deal['company']} conversation "
            f"from {conversation['date']}"
        )

print("\nAll historical conversations stored successfully!")