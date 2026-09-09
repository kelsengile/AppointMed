"""
Base User class and the three kinds of users in the system:
Doctor, Nurse, and Admin. Each one behaves a little differently,
which is a simple example of inheritance and polymorphism.
"""


class User:
    """Base class for every person who can log into AppointMed."""

    def __init__(self, user_id, username, full_name, password_hash):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
        self._password_hash = password_hash  # leading underscore = "please don't touch this directly"

    def check_password(self, plain_password, verify_fn):
        return verify_fn(plain_password, self._password_hash)

    def dashboard_title(self):
        # Every subclass (Doctor, Nurse, Admin) has to fill this in.
        raise NotImplementedError("Subclasses must implement dashboard_title()")

    def permissions(self):
        # Every subclass (Doctor, Nurse, Admin) has to fill this in.
        raise NotImplementedError("Subclasses must implement permissions()")

    def __repr__(self):
        return "<" + self.__class__.__name__ + " " + self.username + ">"


class Doctor(User):
    def __init__(self, user_id, username, full_name, password_hash, specialization):
        super().__init__(user_id, username, full_name, password_hash)
        self.specialization = specialization

    def dashboard_title(self):
        return "Dr. " + self.full_name + " — " + self.specialization

    def permissions(self):
        return ["view_own_schedule", "view_patient_history", "update_diagnosis"]


class Nurse(User):
    """A Nurse/Secretary is always tied to exactly one Doctor."""

    def __init__(self, user_id, username, full_name, password_hash, assigned_doctor_id):
        super().__init__(user_id, username, full_name, password_hash)
        self.assigned_doctor_id = assigned_doctor_id

    def dashboard_title(self):
        return self.full_name + " — Secretary/Nurse"

    def permissions(self):
        return ["manage_assigned_doctor_schedule", "add_appointment", "edit_appointment"]


class Admin(User):
    def dashboard_title(self):
        return self.full_name + " — Administrator"

    def permissions(self):
        return ["manage_users", "view_all_records", "system_settings"]
