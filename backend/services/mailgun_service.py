"""
Mailgun Service - Email automation and management for agents
Provides email sending, template management, and delivery tracking
"""

import base64
import hashlib
import hmac
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Union

import requests

# Import BaseService for proper service registration
from ..utils.service_utils import BaseService, ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)

@dataclass
class EmailMessage:
    """Represents an email message"""
    to: List[str]
    subject: str
    text_content: str
    html_content: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EmailTemplate:
    """Represents an email template"""
    name: str
    subject: str
    text_content: str
    html_content: Optional[str] = None
    variables: Optional[List[str]] = None
    description: Optional[str] = None

@dataclass
class EmailDeliveryStatus:
    """Represents email delivery status"""
    message_id: str
    status: str  # queued, sent, delivered, failed, bounced, complained
    timestamp: str
    recipient: str
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class MailgunService(BaseService):
    """Service for email automation using Mailgun API"""
    
    def __init__(
        self,
        api_key: str,
        domain: str,
        webhook_signing_key: str = None,
        base_url: str = "https://api.mailgun.net/v3",
    ):
        # Initialize BaseService with service name
        super().__init__("mailgun")
        
        self.api_key = api_key
        self.domain = domain
        self.webhook_signing_key = webhook_signing_key
        self.base_url = base_url.rstrip("/")
        self.auth = ("api", api_key)
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("Mailgun API key is required")
        
        if not self.domain:
            raise ValueError("Mailgun domain is required")
        
        # Email templates storage
        self.templates = {}
        self._load_default_templates()
        
        logger.info(f"✅ Mailgun service initialized for domain: {self.domain}")
    
    def _load_default_templates(self):
        """Load default email templates"""
        self.templates = {
            "welcome": EmailTemplate(
                name="welcome",
                subject="Welcome to Swarm Multi-Agent System",
                text_content="""
Hello {name},

Welcome to the Swarm Multi-Agent System! Your account has been successfully created.

You can now access your personalized AI agents and start collaborating with them to accomplish your tasks.

Best regards,
The Swarm Team
""".strip(),
                html_content="""
<html>
<body>
<h2>Welcome to Swarm Multi-Agent System</h2>
<p>Hello <strong>{name}</strong>,</p>
<p>Welcome to the Swarm Multi-Agent System! Your account has been successfully created.</p>
<p>You can now access your personalized AI agents and start collaborating with them to accomplish your tasks.</p>
<p>Best regards,<br>The Swarm Team</p>
</body>
</html>
""".strip(),
                variables=["name"],
                description="Welcome email for new users"
            ),
            "agent_notification": EmailTemplate(
                name="agent_notification",
                subject="Agent Task Completed - {task_type}",
                text_content="""
Hello {user_name},

Your {agent_name} agent has completed the following task:

Task: {task_description}
Status: {status}
Completed at: {completion_time}

{results}

Best regards,
Your AI Assistant Team
""".strip(),
                html_content="""
<html>
<body>
<h2>Agent Task Completed</h2>
<p>Hello <strong>{user_name}</strong>,</p>
<p>Your <strong>{agent_name}</strong> agent has completed the following task:</p>
<ul>
<li><strong>Task:</strong> {task_description}</li>
<li><strong>Status:</strong> {status}</li>
<li><strong>Completed at:</strong> {completion_time}</li>
</ul>
<div style="background-color: #f5f5f5; padding: 15px; margin: 10px 0;">
<h3>Results:</h3>
<p>{results}</p>
</div>
<p>Best regards,<br>Your AI Assistant Team</p>
</body>
</html>
""".strip(),
                variables=["user_name", "agent_name", "task_description", "status", "completion_time", "results"],
                description="Notification when agent completes a task"
            ),
            "error_notification": EmailTemplate(
                name="error_notification",
                subject="System Alert - {error_type}",
                text_content="""
System Administrator,

An error has occurred in the Swarm Multi-Agent System:

Error Type: {error_type}
Timestamp: {timestamp}
Component: {component}
User: {user_id}

Error Details:
{error_details}

Please investigate and take appropriate action.

System Monitoring
""".strip(),
                variables=["error_type", "timestamp", "component", "user_id", "error_details"],
                description="System error notification for administrators"
            )
        }
    
    def send_email(self, message: EmailMessage) -> Dict[str, Any]:
        """Send an email message"""
        try:
            # Prepare email data
            data = {
                "from": f"{message.from_name or 'Swarm System'} <{message.from_email or f'noreply@{self.domain}'}>",
                "to": message.to,
                "subject": message.subject,
                "text": message.text_content
            }
            
            if message.html_content:
                data["html"] = message.html_content
            
            if message.reply_to:
                data["h:Reply-To"] = message.reply_to
            
            if message.cc:
                data["cc"] = message.cc
            
            if message.bcc:
                data["bcc"] = message.bcc
            
            if message.tags:
                for tag in message.tags:
                    data[f"o:tag"] = tag
            
            if message.metadata:
                for key, value in message.metadata.items():
                    data[f"v:{key}"] = str(value)
            
            # Handle attachments
            files = []
            if message.attachments:
                for attachment in message.attachments:
                    if "content" in attachment and "filename" in attachment:
                        files.append(("attachment", (attachment["filename"], attachment["content"])))
            
            logger.info(f"📧 Sending email to {', '.join(message.to)}: {message.subject}")
            
            # Send email via Mailgun API
            response = requests.post(
                f"{self.base_url}/{self.domain}/messages",
                auth=self.auth,
                data=data,
                files=files if files else None
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Email sent successfully: {result.get('id')}")
                return {
                    "success": True,
                    "message_id": result.get("id"),
                    "message": result.get("message", "Queued. Thank you.")
                }
            else:
                logger.error(f"❌ Failed to send email: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Mailgun API error: {response.status_code}",
                    "details": response.text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error sending email: {e}")
            return {
                "success": False,
                "error": "Network error",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {e}")
            return {
                "success": False,
                "error": "Unexpected error",
                "details": str(e)
            }
    
    def send_template_email(
        self, 
        template_name: str, 
        to: List[str], 
        variables: Dict[str, str], 
        **kwargs
    ) -> Dict[str, Any]:
        """Send email using a template"""
        
        if template_name not in self.templates:
            return {
                "success": False,
                "error": f"Template '{template_name}' not found",
                "available_templates": list(self.templates.keys())
            }
        
        template = self.templates[template_name]
        
        try:
            # Replace variables in template
            subject = template.subject.format(**variables)
            text_content = template.text_content.format(**variables)
            html_content = template.html_content.format(**variables) if template.html_content else None
            
            # Create email message
            message = EmailMessage(
                to=to,
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                tags=[template_name],
                metadata={"template": template_name, **variables},
                **kwargs
            )
            
            return self.send_email(message)
            
        except KeyError as e:
            return {
                "success": False,
                "error": f"Missing template variable: {e}",
                "required_variables": template.variables or []
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Template processing error",
                "details": str(e)
            }
    
    def add_template(self, template: EmailTemplate) -> Dict[str, Any]:
        """Add or update an email template"""
        try:
            self.templates[template.name] = template
            logger.info(f"✅ Template '{template.name}' added/updated")
            return {
                "success": True,
                "message": f"Template '{template.name}' added successfully"
            }
        except Exception as e:
            logger.error(f"❌ Error adding template: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get all available email templates"""
        return [asdict(template) for template in self.templates.values()]
    
    def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get delivery status for a message"""
        try:
            response = requests.get(
                f"{self.base_url}/{self.domain}/events",
                auth=self.auth,
                params={"message-id": message_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                events = data.get("items", [])
                
                if events:
                    latest_event = events[0]  # Most recent event
                    return {
                        "success": True,
                        "status": latest_event.get("event"),
                        "timestamp": latest_event.get("timestamp"),
                        "recipient": latest_event.get("recipient"),
                        "details": latest_event
                    }
                else:
                    return {
                        "success": True,
                        "status": "unknown",
                        "message": "No events found for this message ID"
                    }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting delivery status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_webhook_signature(self, token: str, timestamp: str, signature: str) -> bool:
        """Verify Mailgun webhook signature"""
        if not self.webhook_signing_key:
            logger.warning("⚠️ Webhook signing key not configured")
            return False
        
        try:
            hmac_digest = hmac.new(
                key=self.webhook_signing_key.encode(),
                msg=f"{timestamp}{token}".encode(),
                digestmod=hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, hmac_digest)
            
        except Exception as e:
            logger.error(f"❌ Error verifying webhook signature: {e}")
            return False
    
    async def _health_check(self) -> ServiceHealth:
        """Implement health check for BaseService abstract method"""
        try:
            # Use existing test_connection logic for health check
            response = requests.get(
                f"{self.base_url}/{self.domain}",
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                return ServiceHealth(
                    status=ServiceStatus.HEALTHY,
                    message="Mailgun service is healthy and responsive",
                    details={
                        "domain": self.domain,
                        "api_endpoint": self.base_url,
                        "templates_count": len(self.templates),
                        "webhook_configured": bool(self.webhook_signing_key)
                    },
                    last_check=datetime.now(timezone.utc).isoformat()
                )
            else:
                return ServiceHealth(
                    status=ServiceStatus.UNHEALTHY,
                    message=f"Mailgun API returned status {response.status_code}",
                    details={
                        "status_code": response.status_code,
                        "response_text": response.text[:200]  # Limit response text
                    },
                    last_check=datetime.now(timezone.utc).isoformat()
                )
                
        except requests.exceptions.Timeout:
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY,
                message="Mailgun API connection timeout",
                details={"error": "Connection timeout after 10 seconds"},
                last_check=datetime.now(timezone.utc).isoformat()
            )
        except requests.exceptions.RequestException as e:
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY,
                message="Mailgun API connection failed",
                details={"error": str(e)},
                last_check=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            return ServiceHealth(
                status=ServiceStatus.ERROR,
                message="Unexpected error during health check",
                details={"error": str(e)},
                last_check=datetime.now(timezone.utc).isoformat()
            )

    def test_connection(self) -> bool:
        """Test the Mailgun API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/{self.domain}",
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Mailgun connection test successful")
                return True
            else:
                logger.error(f"❌ Mailgun connection test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Mailgun connection test failed: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        try:
            is_connected = self.test_connection()
            
            return {
                "status": "healthy" if is_connected else "unhealthy",
                "connected": is_connected,
                "domain": self.domain,
                "api_endpoint": self.base_url,
                "templates_count": len(self.templates),
                "webhook_configured": bool(self.webhook_signing_key)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
    
    def send_welcome_email(self, user_email: str, user_name: str) -> Dict[str, Any]:
        """Send welcome email to new user"""
        return self.send_template_email(
            template_name="welcome",
            to=[user_email],
            variables={"name": user_name}
        )
    
    def send_agent_notification(
        self, 
        user_email: str, 
        user_name: str, 
        agent_name: str, 
        task_description: str, 
        status: str, 
        results: str
    ) -> Dict[str, Any]:
        """Send agent task completion notification"""
        return self.send_template_email(
            template_name="agent_notification",
            to=[user_email],
            variables={
                "user_name": user_name,
                "agent_name": agent_name,
                "task_description": task_description,
                "status": status,
                "completion_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "results": results
            }
        )
    
    def send_error_notification(
        self, 
        admin_emails: List[str], 
        error_type: str, 
        component: str, 
        user_id: str, 
        error_details: str
    ) -> Dict[str, Any]:
        """Send system error notification to administrators"""
        return self.send_template_email(
            template_name="error_notification",
            to=admin_emails,
            variables={
                "error_type": error_type,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "component": component,
                "user_id": user_id,
                "error_details": error_details
            }
        )


# Global Mailgun service instance
mailgun_service: Optional[MailgunService] = None

def initialize_mailgun(
    api_key: str, 
    domain: str, 
    webhook_signing_key: str = None
) -> MailgunService:
    """Initialize Mailgun service"""
    global mailgun_service
    mailgun_service = MailgunService(api_key, domain, webhook_signing_key)
    return mailgun_service

def get_mailgun_service() -> Optional[MailgunService]:
    """Get the global Mailgun service instance"""
    return mailgun_service

