from flask_admin.contrib.sqla import ModelView
from flask_security import current_user

class SecurityModelView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')