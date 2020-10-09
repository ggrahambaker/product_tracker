from app import create_app, db
from app.models import User, FinAsset, FinComment, Notification, Message, Task

app = create_app()
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'FinAsset': FinAsset, 'FinComment': FinComment, 'Message': Message,
            'Notification': Notification, 'Task': Task}