import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from .models import Employee, Recruiter, Job, Application

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker('email')
    name = factory.Faker('name')
    role = 'employee'  # Default role as employee
    password = factory.PostGenerationMethodCall('set_password', 'password123')


class RecruiterFactory(DjangoModelFactory):
    class Meta:
        model = Recruiter

    user = factory.SubFactory(UserFactory, role='recruiter')
    company_name = factory.Faker('company')
    website = factory.Faker('url')


class JobFactory(DjangoModelFactory):
    class Meta:
        model = Job

    title = factory.Faker('job')
    description = factory.Faker('text')
    recruiter = factory.SubFactory(RecruiterFactory)
    location = factory.Faker('city')
    job_type = 'full_time'
    salary = factory.Faker('random_number', digits=5)
    application_deadline = factory.Faker('future_datetime')


class EmployeeFactory(DjangoModelFactory):
    class Meta:
        model = Employee

    user = factory.SubFactory(UserFactory, role='employee')
    phone_number = factory.Faker('bothify', text='##########')
    location = factory.Faker('city')


class ApplicationFactory(DjangoModelFactory):
    class Meta:
        model = Application

    employee = factory.SubFactory(EmployeeFactory)
    job = factory.SubFactory(JobFactory)
    cover_letter = factory.Faker('paragraph')
