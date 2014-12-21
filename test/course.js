var request = require('supertest');
var should = require('should');
var utils = require('./utils');

request = request(utils.host);

describe('Courses', function() {
    teacher_one = {
            name: 'Login Teacher One',
            email: 'teacher.login@guc.edu.eg',
            password: 'pass'
        }
    teacher_two = {
            name: 'Login Teacher Two',
            email: 'teacher2.login@guc.edu.eg',
            password: 'pass'
        }
    student_one = {
            name: 'Login Student One',
            email: 'student1.login@student.guc.edu.eg',
            password: 'pass',
            guc_id: '22-1111'
        }

    student_two = {
            name: 'Login Student Two',
            email: 'student2.login@student.guc.edu.eg',
            password: 'pass',
            guc_id: '22-1112'
        }
    before(function(done) {
        request.get(utils.drop_ep)
        .end(function(err, res){
            should.not.exist(err);
            res.status.should.be.eql(200);
            done(); 
        });
    });

    before(function(done) {
            request.post(utils.users_ep)
            .send(teacher_one).end(function(err, res) {
                res.status.should.be.eql(201);
                teacher_one.id = res.body.id;
                teacher_one.url = res.body.url;
                done();
            });
        });

        before(function(done) {
            request.post(utils.users_ep)
            .send(teacher_two).end(function(err, res) {
                res.status.should.be.eql(201);
                teacher_two.id = res.body.id;
                teacher_two.url = res.body.url;
                done();
            });
        });

        before(function(done) {
            request.post(utils.users_ep)
            .send(student_one).end(function(err, res) {
                res.status.should.be.eql(201);
                student_one.id = res.body.id;
                student_one.url = res.body.url;
                done();
            });
        });
        before(function(done) {
            request.post(utils.users_ep)
            .send(student_two).end(function(err, res) {
                res.status.should.be.eql(201);
                student_two.id = res.body.id;
                student_two.url = res.body.url;
                done();
            });
        });

        before(function(done) {
            request.post(utils.token_ep)
            .set('Authorization', 
                utils.auth_header_value(teacher_one.email,
                    teacher_one.password))
            .end(function(err, res) {
                res.status.should.be.eql(201);
                teacher_one.token = res.body.token;
                done();    
            });                
        });

        before(function(done) {
            request.post(utils.token_ep)
            .set('Authorization', 
                utils.auth_header_value(teacher_two.email,
                    teacher_two.password))
            .end(function(err, res) {
                res.status.should.be.eql(201);
                teacher_two.token = res.body.token;
                done();    
            });                
        });

        before(function(done) {
            request.post(utils.token_ep)
            .set('Authorization', 
                utils.auth_header_value(student_one.email,
                    student_one.password))
            .end(function(err, res) {
                res.status.should.be.eql(201);
                student_one.token = res.body.token;
                done();    
            });                
        });

        before(function(done) {
            request.post(utils.token_ep)
            .set('Authorization', 
                utils.auth_header_value(student_two.email,
                    student_two.password))
            .end(function(err, res) {
                res.status.should.be.eql(201);
                student_two.token = res.body.token;
                done();    
            });                
        });

        course_one = {
            name: 'CSEN 4XX',
            description: 'This is a very exciting course, people love it!'
        }

        course_three = {
            name: 'CSEN 9XX',
            description: 'A terrible course, just terrible!'
        }
        

        describe('Creation', function() {
            it('As a teacher I can create a course', function(done) {
                request.post(utils.courses_ep)
                .set('X-Auth-Token', teacher_one.token)
                .send(course_one)
                .end(function(err, res){
                    should.not.exist(err);
                    res.status.should.be.eql(201);
                    res.body.should.be.an.instanceOf(Object);
                    res.body.should.have.properties({
                        name: course_one.name,
                        description: course_one.description
                    }).and.have.properties(
                        ['url', 'tas_url', 'students_url',
                        'submissions_url', 'supervisor']);
                    // update
                    course_one = res.body;
                    done();
                });
            });

            it('As a student I can not create a course', function(done) {
                request.post(utils.courses_ep)
                .set('X-Auth-Token', student_one.token)
                .send(course_three)
                .end(function(err, res) {
                    should.not.exist(err);
                    res.status.should.be.eql(403);
                    done();
                });
            });

            describe('Initial Status', function() {
                course_two = {
                    name: 'CSEN 6XX',
                    description: 'An Even better course if you can believe it!'
                }
                before(function(done) {
                    request.post(utils.courses_ep)
                    .set('X-Auth-Token', teacher_one.token)
                    .send(course_two)
                    .end(function(err, res){
                        should.not.exist(err);
                        res.status.should.be.eql(201);
                        course_two = res.body;
                        done();
                    });
                });

                it('Should have restricted public view', function(done){
                    request.get(course_two.url)
                    .end(function(err, res) {
                        should.not.exist(err);
                        res.status.should.be.eql(200);
                        res.body.should.have.properties({
                            name: course_two.name,
                            description: course_two.description,
                            url: course_two.url
                        }).and.not.have.properties(
                            ['tas_url','students_url', 'projects_url',
                            'submissions_url', 'supervisor']);
                        done();
                    });

                });

                it('Should have creator as supervisor', function(done) {
                    request.get(course_two.url)
                    .set('X-Auth-Token', teacher_one.token)
                    .end(function(err, res){
                        should.not.exist(err);
                        res.status.should.be.eql(200);
                        res.body.should.containDeep({
                            supervisor: {
                              email: teacher_one.email,
                              name: teacher_one.name,
                              id: teacher_one.id,
                              url: teacher_one.url  
                            }
                        });
                        done();
                    });
                });

                it('Should have exactly one TA', function(done) {
                    request.get(course_two.tas_url)
                    .set('X-Auth-Token', student_one.token)
                    .end(function(err, res){
                        should.not.exist(err);
                        res.status.should.be.eql(200);
                        res.body.should.have.a.lengthOf(1)
                        .and.matchEach(
                            function(it) {
                                it.should.eql(course_two.supervisor);
                            });
                        done();
                    });
                });

                it('Should have zero students', function(done) {
                    request.get(course_two.students_url)
                    .set('X-Auth-Token', student_one.token)
                    .end(function(err, res){
                        should.not.exist(err);
                        res.status.should.be.eql(200);
                        res.body.should.be.empty;
                        done();
                    });
                });

            }); // Initial Describe
        });// Creation descrive
}); // Courses Describe
