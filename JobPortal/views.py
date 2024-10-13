from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignupForm, EmployeeForm, RecruiterForm, JobForm, ApplicationForm
from .models import User, Employee, Recruiter, Job, Application
from django.contrib.auth import logout, login, authenticate
from .serializers import UserRegisterSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from .tasks import send_application_notification, send_application_status_update_notification



def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save() 
            login(request, user)  
            if user.role == 'recruiter':
                return redirect('recruiter_profile_update')
            elif user.role == 'employee':
                return redirect('employee_profile_update') 
    else:
        form = SignupForm()
    return render(request, 'userflow/signup.html', {'form': form})


@login_required
def employee_profile_update(request):
    employee, created = Employee.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employee_dashboard')  
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'userflow/profile_update.html', {'form': form, 'role': 'employee'})


@login_required
def recruiter_profile_update(request):
    recruiter, created = Recruiter.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = RecruiterForm(request.POST, instance=recruiter)
        if form.is_valid():
            form.save()
            return redirect('recruiter_dashboard') 
    else:
        form = RecruiterForm(instance=recruiter)
    return render(request, 'userflow/profile_update.html', {'form': form, 'role': 'recruiter'})


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'recruiter':
                return redirect('recruiter_dashboard')  
            elif user.role == 'employee':
                return redirect('employee_dashboard') 
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'userflow/login.html', {})


@login_required
def employee_dashboard_view(request):
    employee = Employee.objects.get(user=request.user)
    applications = Application.objects.filter(employee=employee)

    context = {
        'applications': applications
    }
    return render(request, 'dashboard/employee_dashboard.html', context)


@login_required
def recruiter_dashboard_view(request):
    recruiter = get_object_or_404(Recruiter, user=request.user)

    jobs = Job.objects.filter(recruiter=recruiter).order_by('-posted_date')
    
    context = {
        'jobs': jobs, 
        'user': request.user,
        'message': 'Welcome to the Recruiter Dashboard!',
    }
    
    return render(request, 'dashboard/recruiter_dashboard.html', context)


def job_search(request):
    search_params = {
        'company_name': request.GET.get('company_name', '').strip(),
        'job_title': request.GET.get('job_title', '').strip(),
        'job_type': request.GET.get('job_type', ''),
        'location': request.GET.get('location', '').strip(),
        'min_salary': request.GET.get('min_salary', ''),
        'posted_after': request.GET.get('posted_after', ''),
        'deadline_before': request.GET.get('deadline_before', ''),
    }

    jobs = Job.objects.all()

    if search_params['company_name']:
        jobs = jobs.filter(recruiter__company_name__icontains=search_params['company_name'])

    if search_params['job_title']:
        jobs = jobs.filter(title__icontains=search_params['job_title'])

    if search_params['job_type']:
        jobs = jobs.filter(job_type=search_params['job_type'])

    if search_params['location']:
        jobs = jobs.filter(location__icontains=search_params['location'])

    if search_params['min_salary'].isdigit():
        jobs = jobs.filter(salary__gte=int(search_params['min_salary']))

    if search_params['posted_after']:
        jobs = jobs.filter(posted_date__gte=search_params['posted_after'])

    if search_params['deadline_before']:
        jobs = jobs.filter(application_deadline__lte=search_params['deadline_before'])

    context = {
        'jobs': jobs,
        **search_params, 
    }

    return render(request, 'jobs/job_search.html', context)


def job_list_view(request):
    if request.user.is_authenticated and request.user.role == 'recruiter':
        jobs = Job.objects.filter(recruiter__user=request.user) 
    else:
        jobs = Job.objects.all()

    page_number = request.GET.get('page')

    paginator = Paginator(jobs, 10)
    page_obj = paginator.get_page(page_number)

    applied_job_ids = []
    if request.user.is_authenticated and request.user.role == 'employee':
        employee = Employee.objects.get(user=request.user)
        applied_job_ids = Application.objects.filter(employee=employee).values_list('job_id', flat=True)

    return render(request, 'jobs/job_list.html', {
        'page_obj': page_obj,
        'applied_job_ids': applied_job_ids
    })


@login_required
def job_detail_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    already_applied = False
    if request.user.is_authenticated and request.user.role == 'employee':
        try:
            employee = Employee.objects.get(user=request.user)
            already_applied = Application.objects.filter(employee=employee, job=job).exists()
        except Employee.DoesNotExist:
            already_applied = False

    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'already_applied': already_applied 
    })


# @login_required
# def apply_job(request, job_id):
#     job = get_object_or_404(Job, id=job_id)

#     if request.method == 'POST':
#         form = ApplicationForm(request.POST, user=request.user) 
#         if form.is_valid():
#             application = form.save(commit=False)
#             application.job = job
#             application.employee = get_object_or_404(Employee, user=request.user)
#             application.save()
#             messages.success(request, 'Your application has been submitted successfully!')
#             return redirect('application_list') 
#     else:
#         form = ApplicationForm(user=request.user)  

#     return render(request, 'jobs/job_apply.html', {'job': job, 'form': form})


@login_required
def apply_job(request, job_id):
    # Ensure only employees can apply for jobs
    if request.user.role != 'employee':
        messages.error(request, 'Only employees can apply for jobs.')
        return redirect('job_list')

    # Fetch the job and employee
    job = get_object_or_404(Job, id=job_id)
    employee = get_object_or_404(Employee, user=request.user)

    # Check if the employee has already applied for this job
    if Application.objects.filter(employee=employee, job=job).exists():
        messages.error(request, 'You have already applied for this job.')
        return redirect('application_list')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, user=request.user)  # Pass the user to prepopulate form fields
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.employee = employee
            application.save()

            # Send an email notification to the recruiter using Celery
            recruiter_email = job.recruiter.user.email
            applicant_name = request.user.name
            # Pass job_id as a parameter to the Celery task
            send_application_notification.delay(recruiter_email, job.title, applicant_name, job_id)

            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('application_list')
    else:
        form = ApplicationForm(user=request.user)  # Prepopulate form with user data

    return render(request, 'jobs/job_apply.html', {'job': job, 'form': form})



@login_required
def application_list(request):
    user = request.user

    if user.role == 'employee':
        employee = get_object_or_404(Employee, user=user)
        applications = Application.objects.filter(employee=employee).order_by('-submitted_at')
    elif user.role == 'recruiter':
        recruiter = get_object_or_404(Recruiter, user=user)
        applications = Application.objects.filter(job__recruiter=recruiter).order_by('-submitted_at')

    paginator = Paginator(applications, 5)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj, 
    }
    return render(request, 'applications/application_list.html', context)


@login_required
def application_detail_view(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    is_employee = application.employee.user == request.user
    is_recruiter = application.job.recruiter.user == request.user

    if not is_employee and not is_recruiter:
        return render(request, '403.html')

    if request.method == 'POST' and is_recruiter:
        new_status = request.POST.get('status')
        application.update_status(new_status, request.user) 
        
        # Send notification to the employee about the status update
        employee_email = application.employee.user.email
        job_title = application.job.title
        
        # Pass the application_id to the notification task
        send_application_status_update_notification.delay(employee_email, new_status, job_title, application.id)

        messages.success(request, 'Application status updated successfully!')
        return redirect('application_list')  # Redirect to the application list after updating status


    return render(request, 'applications/application_detail.html', {
        'application': application,
        'is_employee': is_employee,
        'is_recruiter': is_recruiter,
    })


@login_required
def create_job_view(request):
    recruiter = get_object_or_404(Recruiter, user=request.user)
    
    if request.method == 'POST':
        job_form = JobForm(request.POST)
        
        if job_form.is_valid():
            job = job_form.save(commit=False)
            job.recruiter = recruiter 
            job.save() 
            messages.success(request, 'Job created successfully!')
            return redirect('recruiter_dashboard') 
        else:
            messages.error(request, 'Error creating the job. Please correct the form.')
    else:
        job_form = JobForm() 

    return render(request, 'jobs/job_post_form.html', {'job_form': job_form, 'is_update': False})


@login_required
def update_job_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        job_form = JobForm(request.POST, instance=job) 
        
        if job_form.is_valid():
            job_form.save()  
            messages.success(request, 'Job updated successfully!')
            return redirect('recruiter_dashboard') 

    else:
        job_form = JobForm(instance=job) 

    return render(request, 'jobs/job_post_form.html', {'job_form': job_form, 'is_update': True})


@login_required
def delete_job_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully!')
        return redirect('recruiter_dashboard')

    return render(request, 'jobs/delete_job.html', {'job': job})


def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('login')
