from django.test import TestCase
from django.urls import reverse
from .models import User, Application, Job
from .factories import UserFactory, RecruiterFactory, JobFactory, EmployeeFactory, ApplicationFactory


class UserFactoryTest(TestCase):

    def test_create_employee_user(self):
        user = UserFactory(role='employee')
        self.assertEqual(user.role, 'employee')
        self.assertTrue(user.check_password('password123'))

    def test_create_recruiter_user(self):
        user = UserFactory(role='recruiter')
        self.assertEqual(user.role, 'recruiter')


class RecruiterFactoryTest(TestCase):

    def test_create_recruiter(self):
        recruiter = RecruiterFactory()
        self.assertEqual(recruiter.user.role, 'recruiter')
        self.assertIsNotNone(recruiter.company_name)
        self.assertIsNotNone(recruiter.website)


class JobFactoryTest(TestCase):

    def test_create_job(self):
        job = JobFactory()
        self.assertIsInstance(job, Job)
        self.assertIsNotNone(job.title)
        self.assertIsNotNone(job.recruiter)
        self.assertEqual(job.job_type, 'full_time')


class EmployeeFactoryTest(TestCase):

    def test_create_employee(self):
        employee = EmployeeFactory()
        self.assertIsNotNone(employee.user)
        self.assertEqual(employee.user.role, 'employee')
        self.assertIsNotNone(employee.phone_number)
        self.assertIsNotNone(employee.location)


class ApplicationFactoryTest(TestCase):

    def test_create_application(self):
        application = ApplicationFactory()
        self.assertEqual(application.status, 'submitted')
        self.assertIsNotNone(application.employee)
        self.assertIsNotNone(application.job)

    def test_application_status_update(self):
        application = ApplicationFactory()
        application.update_status('interview')
        self.assertEqual(application.status, 'interview')


class JobListingViewTest(TestCase):

    def setUp(self):
        self.recruiter = RecruiterFactory()
        self.job1 = JobFactory(recruiter=self.recruiter, title='Backend Developer')
        self.job2 = JobFactory(recruiter=self.recruiter, title='Frontend Developer')
        self.employee = EmployeeFactory()
        self.client.login(email=self.employee.user.email, password='password123')

    def test_job_listing_view(self):
        response = self.client.get(reverse('job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.job1, response.context['page_obj'])
        self.assertIn(self.job2, response.context['page_obj'])
        self.assertTemplateUsed(response, 'jobs/job_list.html')


class JobApplicationSubmissionTest(TestCase):

    def setUp(self):
        self.employee = EmployeeFactory()
        self.job = JobFactory()
        self.client.login(email=self.employee.user.email, password='password123')

    def test_prevent_duplicate_application(self):
        # Create an application first
        ApplicationFactory(employee=self.employee, job=self.job)
        
        # Try to apply again
        response = self.client.post(reverse('apply_job', kwargs={'job_id': self.job.id}), {
            'cover_letter': 'This is my second attempt to apply.'
        })
        self.assertRedirects(response, reverse('application_list'))  # Expect redirect to application list
        self.assertEqual(Application.objects.filter(employee=self.employee, job=self.job).count(), 1)  # Ensure only one application exists
