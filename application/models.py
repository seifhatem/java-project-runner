"""
Document definitions.
"""
from application import db, app
from flask.ext.bcrypt import generate_password_hash, check_password_hash
import datetime
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired, BadSignature


class User(db.DynamicDocument):

    """Base document for all users."""
    created_at = db.DateTimeField(
        default=datetime.datetime.utcnow, required=True)
    email = db.StringField(
        max_length=256, min_length=1, required=True, unique=True)
    name = db.StringField(max_length=512, min_length=1, required=True)
    password_hash = db.StringField(max_length=60, required=True)

    meta = {'allow_inheritance': True,
            "indexes": [
                {
                    "fields": ['email'],
                    "unique": True
                },
                {
                    "fields": ['name']
                }
            ]
            }

    @property
    def password(self):
        """Returns password hash, not actual password."""
        return self.password_hash

    @password.setter
    def password(self, value):
        """Hashes password."""
        self.password_hash = generate_password_hash(value, 12)

    def verify_pass(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expires_in):
        """Creates a token to uniquely identify this user."""
        seriliezer = TimedJSONWebSignatureSerializer(
            app.config['SECRET_KEY'], expires_in=expires_in)
        return seriliezer.dumps({'id': str(self.id)})

    @staticmethod
    def verify_auth_token(token):
        """
        Retrieves user who is identified by this token.
        Raises SignatureExpired, BadSignature if expired or malformed.
        """
        s = TimedJSONWebSignatureSerializer(app.config['SECRET_KEY'])
        data = s.loads(token)
        matches = User.objects(id=data['id'])
        if matches.count() != 1:
            return None
        return matches[0]

    def to_dict(self, **kwargs):
        return {
            "id": self.id,
            "created_at": self.created_at,
            "email": self.email,
            "password": self.password,
            "name": self.name
        }


class Student(User):
    guc_id = db.StringField(max_length=32, min_length=7, required=True)

    def to_dict(self, **kwargs):
        dic = User.to_dict(self)
        dic['guc_id'] = self.guc_id
        return dic


class Course(db.Document):
    created_at = db.DateTimeField(
        default=datetime.datetime.utcnow, required=True)
    projects = db.ListField(db.ReferenceField('Project'))
    name = db.StringField(
        max_length=256, min_length=4, unique=True, required=True)
    description = db.StringField(max_length=1024, min_length=10, required=True)
    supervisor = db.ReferenceField('User', reverse_delete_rule=db.PULL)
    teachers = db.ListField(
        db.ReferenceField('User', reverse_delete_rule=db.PULL))
    students = db.ListField(
        db.ReferenceField('Student', reverse_delete_rule=db.PULL))

    meta = {
        "indexes": [
            {
                "fields": ['name'],
                "unique": True
            }
        ]
    }

    def to_dict(self, **kwargs):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "supervisor": self.supervisor.to_dict()
        }


class Project(db.Document):

    """A course's Project."""
    LANGUAGES = [('J', 'Java Project')]
    created_at = db.DateTimeField(
        default=datetime.datetime.utcnow, required=True)
    name = db.StringField(max_length=256, min_length=5, required=True)
    tests = db.ListField(db.FileField())
    language = db.StringField(
        max_length=3, min_length=1, choices=LANGUAGES, required=True)
    test_timeout_seconds = db.LongField(
        default=600, max_value=1800, required=True)
    submissions = db.ListField(db.ReferenceField('Submission'))

    def to_dict(self, **kwargs):
        parent_course = kwargs.get('parent_course', None)
        dic = {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "created_at": self.created_at,
            "tests": [f.name for f in self.tests],
            "course": (parent_course.to_dict(**kwargs) if parent_course is not None
                       else Course.objects.get(projects=self).to_dict(**kwargs))
        }
        dic['course_name'] = dic['course']['name']
        return dic


class TestCase(db.EmbeddedDocument):

    """Single case of a TestResult."""
    name = db.StringField(max_length=512, min_length=1, required=True)
    detail = db.StringField(max_length=512, min_length=1, required=True)
    passed = db.BooleanField(default=False, required=True)

    def to_dict(self, **kwargs):
        return {
            "name": self.name,
            "detail": self.detail,
            "passed": self.passed
        }


class TestResult(db.EmbeddedDocument):

    """Results for a single test ran on a submission."""
    created_at = db.DateTimeField(
        default=datetime.datetime.utcnow, required=True)
    name = db.StringField(max_length=256, min_length=1, required=True)
    cases = db.ListField(db.EmbeddedDocumentField('TestCase'))
    success = db.BooleanField(default=False, required=True)

    def to_dict(self, **kwargs):
        return {
            "name": self.name,
            "created_at": self.created_at,
            "cases": [case.to_dict() for case in self.cases],
            "success": self.success
        }


class Submission(db.Document):

    """A student's submission."""
    created_at = db.DateTimeField(
        default=datetime.datetime.utcnow, required=True)
    test_results = db.ListField(db.EmbeddedDocumentField('TestResult'))
    processed = db.BooleanField(default=False, required=True)
    submitter = db.ReferenceField('Student', required=True)
    code = db.FileField(required=True)
    compile_status = db.BooleanField(default=False, required=True)
    compiler_out = db.StringField(max_length=2048)

    def to_dict(self, **kwargs):
        parent_project = kwargs.get('parent_project', None)
        dic = {
            "id": self.id,
            "created_at": self.created_at,
            "processed": self.processed,
            "submitter": self.submitter.to_dict(),
            "tests": [test.to_dict() for test in self.test_results],
            "project": (parent_project.to_dict(**kwargs) if parent_project is not None
                        else Project.objects.get(submissions=self).to_dict(**kwargs)),
            'compile_status': self.compile_status,
            'compiler_out': self.compiler_out
        }
        dic['project_name'] = dic['project']['name']
        dic['course_name'] = dic['project']['course_name']
        return dic