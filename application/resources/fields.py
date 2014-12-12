"""
Marshaling fields
"""
from flask.ext.restful import fields

# User model fields
user_fields = {
    'email': fields.String,
    'name': fields.String,
    'guc_id': fields.String,
    'id': fields.String,
    'created_at': fields.DateTime('iso8601'),
    'url': fields.Url(endpoint='user_ep')
}


# Public course fields.
public_course_fields = {
    "name": fields.String,
    "description": fields.String,
    "url": fields.Url(endpoint='course_ep')
}


course_fields = {
    "tas_url": fields.Url(endpoint='course_tas_ep'),
    "students_url": fields.Url(endpoint='course_students_ep'),
    "projects_url": fields.Url(endpoint='course_projects_ep'),
    "submissions_url": fields.Url(endpoint='course_submissions_ep'),
    "supervisor": fields.Nested(user_fields)

}

course_fields = dict(course_fields.items() + public_course_fields.items())


project_fields = {
    "name": fields.String,
    "course": fields.Nested(course_fields),
    "url": fields.Url(endpoint='project_ep'),
    'submission_url': fields.Url(endpoint='project_submission_ep')
}

test_case_fields = {
    "name": fields.String,
    "detail": fields.String,
    "pass": fields.String
}

test_result_fields = {
    "name": fields.String,
    "cases": fields.List(fields.Nested(test_case_fields)),
    "success": fields.String
}

submission_fields = {
    "id": fields.String,
    "url": fields.Url('submission_ep'),
    "submitter": fields.Nested(user_fields),
    "tests": fields.List(fields.Nested(test_result_fields)),
    "processed": fields.String,
    "project": fields.Nested(project_fields)
}