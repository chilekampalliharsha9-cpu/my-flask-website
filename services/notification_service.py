from models.models import Notification
from extensions import db

def create_notification(title, message, level='info', user_id=None):
    """
    Create an in-app notification. If user_id is None, it is a broadcast notification.
    """
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        level=level,
        read=False
    )
    db.session.add(notif)
    db.session.commit()
    return notif

def get_user_notifications(user_id=None, limit=10):
    """
    Fetch unread and recent notifications for a user, including broadcast messages.
    """
    query = Notification.query.filter(
        (Notification.user_id == user_id) | (Notification.user_id == None)
    ).order_by(Notification.created_at.desc()).limit(limit)
    return query.all()
