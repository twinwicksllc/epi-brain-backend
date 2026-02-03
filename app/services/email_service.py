"""
Email Service
Send emails to internal team members and external recipients
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    # Internal team member mapping (from environment variables)
    TEAM_MEMBERS = {
        "tom": os.getenv("EMAIL_TOM", ""),
        "darrick": os.getenv("EMAIL_DARRICK", ""),
        "twinwicks": os.getenv("EMAIL_TWINWICKS", ""),
    }
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("SMTP_FROM_NAME", "EPI Assistant")
    
    def get_team_member_email(self, name: str) -> Optional[str]:
        """
        Get email address for a team member by name
        
        Args:
            name: Team member name (case-insensitive)
        
        Returns:
            Email address if found, None otherwise
        """
        normalized_name = name.lower().strip()
        email = self.TEAM_MEMBERS.get(normalized_name)
        
        if email:
            logger.info(f"Found team member email for '{name}': {email}")
        else:
            logger.warning(f"No email mapping found for team member: {name}")
        
        return email
    
    def send_internal_message(
        self,
        recipient_name: str,
        subject: str,
        message: str,
        sender_context: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send message to internal team member by name
        
        Args:
            recipient_name: Team member name (tom, darrick, etc.)
            subject: Email subject
            message: Email body/content
            sender_context: Optional context about who sent it (user email, etc.)
        
        Returns:
            Dict with success status and details
        """
        recipient_email = self.get_team_member_email(recipient_name)
        
        if not recipient_email:
            return {
                "success": False,
                "error": f"Unknown team member: {recipient_name}",
                "available_members": list(self.TEAM_MEMBERS.keys())
            }
        
        # Add sender context to message if provided
        full_message = message
        if sender_context:
            full_message = f"[From: {sender_context}]\n\n{message}"
        
        return self.send_email(
            to_email=recipient_email,
            subject=subject,
            body=full_message
        )
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send email to any recipient
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
        
        Returns:
            Dict with success status and details
        """
        try:
            # Validate SMTP configuration
            if not self.smtp_user or not self.smtp_password:
                logger.warning("SMTP credentials not configured - email not sent")
                return {
                    "success": False,
                    "error": "SMTP not configured",
                    "note": "Set SMTP_USER and SMTP_PASSWORD environment variables"
                }
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Attach plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            
            return {
                "success": True,
                "recipient": to_email,
                "subject": subject,
                "message": "Email sent successfully"
            }
        
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "recipient": to_email
            }
