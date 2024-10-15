from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator


# Custom user manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'superadmin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


# Custom user model
class User(AbstractUser):
    username = None 
    email = models.EmailField(unique=True) 
    name = models.CharField(max_length=255, blank=True, null=True)
    
    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('recruiter', 'Recruiter'),
        ('superadmin', 'Superadmin'),
        ('subadmin', 'Subadmin'),
    ]
    
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='employee')  # Increased max_length
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if self.role == 'superadmin':
            self.is_superuser = True
            self.is_staff = True
        elif self.role == 'subadmin':
            self.is_superuser = False
            self.is_staff = True
        else:
            self.is_superuser = False
            self.is_staff = False
        
        super().save(*args, **kwargs)  # Call the real save method

    def clean(self):
        super().clean()
        if self.role not in dict(self.ROLE_CHOICES):
            raise ValidationError('Invalid role assigned.')

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['email']

# Recruiter model (includes company-related fields)
class Recruiter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)  # Company name
    website = models.URLField(blank=True, null=True)  # Company website
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)  # Company logo
    created_at = models.DateTimeField(auto_now_add=True)  # Creation date
    updated_at = models.DateTimeField(auto_now=True)  # Update date

    def __str__(self):
        return f"{self.user.email if self.user and self.user.email else 'Unknown Recruiter'} from {self.company_name}"

    class Meta:
        verbose_name_plural = 'Recruiters'


# Job model representing job postings by companies (posted by recruiters)
class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE, related_name='jobs')
    location = models.CharField(max_length=255)
    job_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ])
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    posted_date = models.DateTimeField(auto_now_add=True)
    application_deadline = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} at {self.recruiter.company_name}"

    class Meta:
        ordering = ['-posted_date']
        verbose_name_plural = 'Jobs'


# Employee model representing additional data for employees
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.user.email if self.user and self.user.email else "Unknown Employee"

    class Meta:
        verbose_name_plural = 'Employees'


# Application model representing job applications by employees
class Application(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('interview', 'Interview'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
    ], default='submitted')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.user.email} applied for {self.job.title}"
    def update_status(self, new_status, user=None):
        if new_status in dict(Application.status.field.choices):
            self.status = new_status
            self.changed_by = user  
            self.save()
