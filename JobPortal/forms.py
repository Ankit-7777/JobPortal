from django import forms
from .models import Job, Application, User, Employee, Recruiter

# Signup Form for creating new users (with role selection)
class SignupForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['email','name', 'password1', 'password2', 'role']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Hash the password
        if commit:
            user.save()

            # Create an Employee or Recruiter instance based on the user's role
            if user.role == 'employee':
                Employee.objects.create(user=user)  # Create Employee
            elif user.role == 'recruiter':
                Recruiter.objects.create(user=user)  # Create Recruiter

        return user


# Form for job creation and updating
class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description',  'location', 'job_type', 'salary', 'application_deadline']

    # recruiter = forms.ModelChoiceField(queryset=Recruiter.objects.all(), empty_label="Select a Recruiter")


# Form for submitting job applications

class ApplicationForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=20, required=True, label='Phone Number')
    resume = forms.FileField(required=False, label='Resume')
    
    class Meta:
        model = Application
        fields = ['cover_letter', 'phone_number', 'resume']  # Include cover letter, phone number, and resume

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.role == 'employee':
            try:
                employee = Employee.objects.get(user=user)
                self.initial['phone_number'] = employee.phone_number  # Pre-fill phone number
                self.initial['name'] = user.name 
                # If you want to show existing resume, consider adding that to the form context
                if employee.resume:
                    self.initial['resume'] = employee.resume  # Pre-fill resume if exists
            except Employee.DoesNotExist:
                pass


# Form for updating employee profile
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['resume', 'phone_number', 'location']


# Form for updating recruiter profile
class RecruiterForm(forms.ModelForm):
    class Meta:
        model = Recruiter
        fields = ['company_name', 'website', 'logo']


# Form for updating User (admin form to update role, etc.)
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email','name', 'role', 'is_staff', 'is_superuser', 'is_active']
