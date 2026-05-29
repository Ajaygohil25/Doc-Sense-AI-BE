from fastapi_mail import FastMail, MessageSchema, MessageType

from app.config.mail_config import get_mail_config


def build_email_template(subject: str, content: str, client_name: str = "Our Application") -> str:
    """
    Build a reusable HTML email template with red & white theme and black font.
    """
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, Helvetica, sans-serif;
                background-color: #ffffff;
                color: #000000;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                border-radius: 8px;
                background-color: #ffffff;
                border: 1px solid #ddd;
            }}
            .header {{
                text-align: center;
                padding: 20px;
                background-color: #cc0000;
                color: #ffffff;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                padding: 20px;
                font-size: 16px;
                line-height: 1.5;
            }}
            .footer {{
                text-align: center;
                font-size: 14px;
                color: #555;
                padding: 15px;
                border-top: 1px solid #eee;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{client_name}</h2>
            </div>
            <div class="content">
                <p><strong>Subject:</strong> {subject}</p>
                <p>{content}</p>
                <p>Thank you for being with us!</p>
            </div>
            <div class="footer">
                &copy; 2025 {client_name}. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """

async def send_mail(email: str, subject: str, content: str, client_name: str = "Our Application"):
    """
    Send an email using FastMail with a reusable HTML template.
    """
    template = build_email_template(subject, content, client_name)

    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=template,
        subtype=MessageType.html,
    )
    # TODO: Replace credentials in the env and uncomment this code to enable email sending
    # fm = FastMail(get_mail_config())
    # await fm.send_message(message)
    # print("mail sent")
