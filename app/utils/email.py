from flask import current_app
from flask_mail import Mail, Message
import logging

mail = Mail()


def init_mail(app):
    """Initialize mail with app"""
    mail.init_app(app)


def send_email(to, subject, body, html_body=None):
    """Send email notification"""
    try:
        if not current_app.config.get('MAIL_SERVER'):
            logging.warning("Mail server not configured, skipping email notification")
            return False
        
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            body=body,
            html=html_body
        )
        
        mail.send(msg)
        logging.info(f"Email sent successfully to {to}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email to {to}: {e}")
        return False


def notify_new_experiment(experiment, researchers):
    """Notify researchers about new experiment upload"""
    try:
        subject = f"New experiment uploaded for {experiment.test.name}"
        
        body = f"""
A new experiment has been uploaded to PsySuite Web Manager.

Test: {experiment.test.name}
Subject: {experiment.subject_label or 'N/A'}
Upload Date: {experiment.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if experiment.uploaded_at else 'N/A'}
Status: {experiment.get_completion_status_display()}
Trials: {experiment.get_trial_count()}

You can view the experiment details at: [Your Web Manager URL]/experiment/{experiment.id}

Best regards,
PsySuite Web Manager
        """
        
        html_body = f"""
<h3>New Experiment Uploaded</h3>
<p>A new experiment has been uploaded to PsySuite Web Manager.</p>

<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Test:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{experiment.test.name}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Subject:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{experiment.subject_label or 'N/A'}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Upload Date:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{experiment.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if experiment.uploaded_at else 'N/A'}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Status:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{experiment.get_completion_status_display()}</td></tr>
    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Trials:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{experiment.get_trial_count()}</td></tr>
</table>

<p><a href="[Your Web Manager URL]/experiment/{experiment.id}">View Experiment Details</a></p>

<p>Best regards,<br>PsySuite Web Manager</p>
        """
        
        success_count = 0
        for researcher in researchers:
            if send_email(researcher.email, subject, body, html_body):
                success_count += 1
        
        logging.info(f"Sent experiment notification to {success_count}/{len(researchers)} researchers")
        return success_count > 0
        
    except Exception as e:
        logging.error(f"Error sending experiment notifications: {e}")
        return False