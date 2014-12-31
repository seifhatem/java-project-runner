from flask.ext.restful import Resource, abort, marshal_with, marshal
from application import api, db
from application.models import Course, Project, Submission, Student
from decorators import student_required, login_required
from fields import submission_fields, project_fields
from flask import g, request
from werkzeug import secure_filename
from application.tasks import junit_task
from application.resources import allowed_code_file


class ProjectSubmissions(Resource):

    @student_required
    def post(self, course_name, name):
        """Creates a new submission."""
        course = Course.objects.get_or_404(name=course_name)
        project = Project.objects.get_or_404(name=name)
        if not g.user in course.students:
            abort(403)  # Must be a course student to submit
        if not project in course.projects:
            abort(404)
        if course.name != course_name:
            abort(404)
        if len(request.files.values()) == 1:
            subm = Submission(submitter=g.user)
            for file in request.files.values():
                if allowed_code_file(file.filename):
                    grid_file = db.GridFSProxy()
                    grid_file.put(
                        file, filename=secure_filename(file.filename))
                    subm.code = grid_file
                else:
                    abort(400)
            subm.save()
            project.submissions.append(subm)
            project.save()
            junit_task.delay(str(subm.id))
            return marshal(subm.to_dict(parent_course=course, parent_project=project), submission_fields), 201
        else:
            abort(400)  # Bad request

    @login_required
    @marshal_with(submission_fields)
    def get(self, course_name, name):
        course = Course.objects.get_or_404(name=course_name)
        project = Project.objects.get_or_404(name=name)
        submissions = [subm.to_dict(parent_course=course, parent_project=project)
                       for subm in project.submissions]

        if isinstance(g.user, Student):
            return [subm for subm in submissions if subm['submitter']['id'] == g.user.id]
        elif g.user in course.teachers:
            return submissions
        else:
            abort(403)  # not a student and not a course teacher


class ProjectResource(Resource):

    @login_required
    @marshal_with(project_fields)
    def get(self, id):
        """
        Returns a single project if g.user is a student in the parent course 
        or g.user is a teacher in parent course.
        return 500 if parent course not found.
        """
        proj = Project.objects.get_or_404(id=id)
        try:
            course = next(
                course for course in Course.objects if proj in course.projects)
            if g.user in course.teachers or g.user in course.students:
                return proj.to_dict(parent_course=course)
            else:
                abort(403)
        except StopIteration:
            abort(
                500, message="Found project with no parent course, Quick call an adult!")


class ProjectsResource(Resource):

    @login_required
    @marshal_with(project_fields)
    def get(self):
        """
        Projects of courses user teaches if teacher, only those registered for if student.
        """
        if isinstance(g.user, Student):
            courses = Course.objects(students=g.user)
            return [[project.to_dict(parent_course=c) for project in c.projects]
                    for c in courses]
        else:
            courses = Course.objects(teachers=g.user)
            return [[project.to_dict(parent_course=c) for project in c.projects]
                    for c in courses]

api.add_resource(ProjectSubmissions, '/course/<string:course_name>/projects/<string:name>/submissions',
                 endpoint='project_submissions_ep')

api.add_resource(
    ProjectResource, '/project/<string:id>', endpoint='project_ep')

api.add_resource(ProjectsResource, '/projects', endpoint='projects_ep')