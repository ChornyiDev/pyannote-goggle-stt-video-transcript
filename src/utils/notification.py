import requests
import os
from ..utils.logger import logger

def send_notification(firestore_ref):
    """Send notification webhook after transcription completion."""
    notification_url = os.getenv('NOTIFICATION_SERVICE_URL')
    
    if not notification_url:
        logger.error("NOTIFICATION_SERVICE_URL is not set in environment variables")
        return False
    
    payload = {
        "firestore_ref": firestore_ref
    }
    
    try:
        logger.info(f"[{firestore_ref}] Sending notification to {notification_url}")
        response = requests.post(
            notification_url,
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        logger.info(f"[{firestore_ref}] Notification sent successfully. Response status: {response.status_code}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[{firestore_ref}] Failed to send notification: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"[{firestore_ref}] Unexpected error sending notification: {e}", exc_info=True)
        return False
