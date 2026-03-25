import asyncio
from outreach.email_operator import EmailOperator
from core.database import init_db

async def test_send():
    print("Initializing DB...")
    await init_db()
    
    op = EmailOperator()
    if not op.accounts:
        print("ERROR: No SMTP accounts found in .env!")
        return

    print(f"Testing send via {op.accounts[0]['user']}...")
    # Send to the user's own email for verification
    to_email = "pixartualstudio@gmail.com" 
    subject = "Status: ColdMailer Production Test"
    body = "This is a live test from the Pixartual Studio outreach system. If you see this, the SMTP relay is 100% operational. 🤝"
    
    success = await op.send(to_email, subject, body)
    if success:
        print("SUCCESS! Email sent. Check your inbox.")
    else:
        print("FAILED. Check logs/outreach.log for details.")

if __name__ == "__main__":
    asyncio.run(test_send())
