from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from .forms import SignupForm, EmployeeForm, RecruiterForm, JobForm, ApplicationForm
from .models import Employee, Recruiter, Job, Application
from django.core.paginator import Paginator
from .tasks import send_application_notification, send_application_status_update_notification, send_welcome_email


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            send_welcome_email.delay(user.email, user.name, user.role)

            return redirect('recruiter_profile_update' if user.role == 'recruiter' else 'employee_profile_update')
    else:
        form = SignupForm()
    return render(request, 'userflow/signup.html', {'form': form})


@login_required
def employee_profile_update(request):
    employee, _ = Employee.objects.get_or_create(user=request.user)
    form = EmployeeForm(request.POST or None, request.FILES or None, instance=employee)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('employee_dashboard')
    return render(request, 'userflow/profile_update.html', {'form': form, 'role': 'employee'})


@login_required
def recruiter_profile_update(request):
    recruiter, _ = Recruiter.objects.get_or_create(user=request.user)
    form = RecruiterForm(request.POST or None, instance=recruiter)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('recruiter_dashboard')
    return render(request, 'userflow/profile_update.html', {'form': form, 'role': 'recruiter'})


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            if user.role == 'recruiter':
                return redirect('recruiter_dashboard')
            elif user.role == 'employee':
                return redirect('employee_dashboard')
            elif user.role == 'superadmin':
                return redirect('superadmin_dashboard') 
        messages.error(request, 'Invalid email or password.')
    return render(request, 'userflow/login.html')



@login_required
def superadmin_dashboard_view(request):
    if request.user.role != 'superadmin':
        return redirect('login')  # Redirect if not a superadmin

    # Count all users based on roles
    employees_count = Employee.objects.count()
    recruiters_count = Recruiter.objects.count()
    jobs_count = Job.objects.count()

    # Assuming there is a Guest model
    # guest_users_count = Guest.objects.count()

    # Active and deactivated recruiters and employees
    active_recruiters_count = Recruiter.objects.filter(user__is_active=True).count()
    deactivated_recruiters_count = Recruiter.objects.filter(user__is_active=False).count()

    active_employees_count = Employee.objects.filter(user__is_active=True).count()
    deactivated_employees_count = Employee.objects.filter(user__is_active=False).count()

    # Job posts (assuming jobs have active/deactivated statuses)
    active_jobs_count = Job.objects.filter(is_active=True).count()
    deactivated_jobs_count = Job.objects.filter(is_active=False).count()

    # Render superadmin dashboard
    return render(request, 'dashboard/superadmin_dashboard.html', {
        'employees_count': employees_count,
        'recruiters_count': recruiters_count,
        'jobs_count': jobs_count,
        # 'guest_users_count': guest_users_count,
        'active_recruiters_count': active_recruiters_count,
        'deactivated_recruiters_count': deactivated_recruiters_count,
        'active_employees_count': active_employees_count,
        'deactivated_employees_count': deactivated_employees_count,
        'active_jobs_count': active_jobs_count,
        'deactivated_jobs_count': deactivated_jobs_count,
        'message': 'Welcome to the Superadmin Dashboard!',
    })



@login_required
def recruiter_list_view(request):
    if request.user.role != 'superadmin':
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('login')

    recruiters = Recruiter.objects.all() 
    paginator = Paginator(recruiters, 10) 
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/recruiter_list.html', {'page_obj': page_obj})


@login_required
def employee_list_view(request):
    if request.user.role != 'superadmin':
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('login') 

    employees = Employee.objects.all() 
    paginator = Paginator(employees, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/employee_list.html', {'page_obj': page_obj})






@login_required
def recruiter_detail_view(request, recruiter_id):
    recruiter = get_object_or_404(Recruiter, id=recruiter_id)

    # Only superadmins can view recruiter details
    if request.user.role != 'superadmin':
        messages.error(request, 'You do not have permission to view this page.')
        return render(request, '403.html')

    if request.method == 'POST':
        # Directly update the 'is_active' status based on checkbox
        is_active = request.POST.get('is_active') == 'on'  # Checkbox value
        recruiter.user.is_active = is_active  # Update the active status of the recruiter
        recruiter.user.save()  # Save the changes
        messages.success(request, 'Recruiter status updated successfully.')
        return redirect('recruiter_detail', recruiter_id=recruiter.id)

    return render(request, 'dashboard/recruiter_detail.html', {'recruiter': recruiter})




@login_required
def employee_detail_view(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    # Only superadmins can view employee details
    if request.user.role != 'superadmin':
        messages.error(request, 'You do not have permission to view this page.')
        return render(request, '403.html')

    if request.method == 'POST':
        # Check if the 'is_active' checkbox was submitted
        is_active = request.POST.get('is_active') == 'on'  # Checkbox value
        employee.user.is_active = is_active  # Update the active status
        employee.user.save()  # Save the changes
        messages.success(request, 'Employee status updated successfully.')
        return redirect('employee_detail', employee_id=employee.id)

    return render(request, 'dashboard/employee_detail.html', {'employee': employee})


@login_required
def employee_dashboard_view(request):
    employee = Employee.objects.get(user=request.user)
    applications = Application.objects.filter(employee=employee)
    return render(request, 'dashboard/employee_dashboard.html', {'applications': applications})


@login_required
def recruiter_dashboard_view(request):
    recruiter = get_object_or_404(Recruiter, user=request.user)
    jobs = Job.objects.filter(recruiter=recruiter).order_by('-posted_date')
    return render(request, 'dashboard/recruiter_dashboard.html', {'jobs': jobs, 'message': 'Welcome to the Recruiter Dashboard!'})


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

    return render(request, 'jobs/job_search.html', {'jobs': jobs, **search_params})


def job_list_view(request):
    jobs = Job.objects.filter(recruiter__user=request.user) if request.user.is_authenticated and request.user.role == 'recruiter' else Job.objects.all()

    paginator = Paginator(jobs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    applied_job_ids = []
    if request.user.is_authenticated and request.user.role == 'employee':
        employee = Employee.objects.get(user=request.user)
        applied_job_ids = Application.objects.filter(employee=employee).values_list('job_id', flat=True)

    return render(request, 'jobs/job_list.html', {'page_obj': page_obj, 'applied_job_ids': applied_job_ids})


@login_required
def job_detail_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    already_applied = Application.objects.filter(employee__user=request.user, job=job).exists() if request.user.role == 'employee' else False
    return render(request, 'jobs/job_detail.html', {'job': job, 'already_applied': already_applied})


@login_required
def apply_job(request, job_id):
    if request.user.role != 'employee':
        messages.error(request, 'Only employees can apply for jobs.')
        return redirect('job_list')

    job = get_object_or_404(Job, id=job_id)
    employee = get_object_or_404(Employee, user=request.user)

    if Application.objects.filter(employee=employee, job=job).exists():
        messages.error(request, 'You have already applied for this job.')
        return redirect('application_list')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.employee = employee
            application.save()

            send_application_notification.delay(job.recruiter.user.email, job.title, request.user.name, job_id)

            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('application_list')
    else:
        form = ApplicationForm(user=request.user)

    return render(request, 'jobs/job_apply.html', {'job': job, 'form': form})


@login_required
def application_list(request):
    applications = Application.objects.filter(employee__user=request.user) if request.user.role == 'employee' else Application.objects.filter(job__recruiter__user=request.user)

    paginator = Paginator(applications, 5)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'applications/application_list.html', {'page_obj': page_obj})


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
    form = JobForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        job = form.save(commit=False)
        job.recruiter = recruiter
        job.save()
        messages.success(request, 'Job created successfully!')
        return redirect('recruiter_dashboard')
    return render(request, 'jobs/job_post_form.html', {'job_form': form, 'is_update': False})


@login_required
def update_job_view(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    form = JobForm(request.POST or None, instance=job)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Job updated successfully!')
        return redirect('recruiter_dashboard')
    return render(request, 'jobs/job_post_form.html', {'job_form': form, 'is_update': True})


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
