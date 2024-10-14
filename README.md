# TalentHunt

**TalentHunt** is a recruiter and jobseeker management application that allows recruiters to manage job postings and applications while providing jobseekers with a platform to apply for jobs and receive notifications about their application status.

## Features

### For Recruiters

- **User Management**: Recruiters can register and manage their profiles.
- **Job Management**: Create, read, update, and delete job postings.
- **Application Tracking**: View applications from jobseekers and update their status.
- **Role-Based Access Control**: Recruiters can only manage their own job postings.
- **Email Notifications**: Automatic email alerts to jobseekers when they apply and to recruiters when application statuses change.
- **Dashboard**: A tailored dashboard for recruiters shows self-created job applications as cards and allows management of these applications.
- **Application List**: Recruiters can view a list of applications for their own job postings.

### For Jobseekers(Employee)

- **User Management**: Register and manage jobseeker(Employee) profiles.
- **Job Applications**: Apply for jobs and track application status.
- **Job Listings**: Browse and filter job listings by title, location, and company.
- **Email Notifications**: Receive notifications about application statuses.
- **Dashboard**: Jobseekers have a dedicated dashboard displaying their job applications.

### Job Search

Jobseekers can search for jobs based on the following criteria:

- **Company Name**
- **Job Title**
- **Job Type**
- **Location**
- **Minimum Salary**
- **Posted After**
- **Deadline Before**

### General Features

- **User Authentication**: Secure login and registration using Django Session-based authentication.
- **Unauthenticated User Access**: Unauthenticated users can view only the job post list but cannot apply for jobs or not see job details without logging in.
- **Security**: Password hashing with bcrypt, and protection against common security attacks such as SQL Injection and XSS.
- **Error Handling**: Proper error messages and HTTP status codes (e.g., 401 Unauthorized, 404 Not Found).
- **Background Task Queue**: Celery is used to handle email notifications asynchronously.
- **Django Forms**: Utilizes Django forms for templating to create dynamic and interactive user interfaces.
- **Application List**: Displays applications for both recruiters and jobseekers(Employee), with filters allowing recruiters to see only applications for their own job postings.

### Technologies Used

- **Backend**: Django
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: MYSQL
- **Task Queue**: Celery
- **Email Service**: SMTP

### Set up a Virtual Environment

```bash
python -m venv myenv 
```

### Activate the Virtual Environment

```bash
# On Linux and macOS
source myenv/bin/activate   
# On Windows use
myenv\Scripts\activate
# deactivate
deactivate
```

## Installation

To set up the project locally, follow these steps:

### 1. Clone the Repository

```bash
git clone https://github.com/Ankit-7777/TalentHunt.git
cd TalentHunt
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python manage.py runserver
```

### 4. Run the makemigrations and migrate commands

```bash
python manage.py makemigrations
python manage.py migrate
```

### Install Redis For Windows Ubuntu

```bash
wsl --install

curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

sudo apt-get update

sudo apt-get install redis-server

sudo service redis-server start

sudo service redis-server status

# Start Celery on Windows
celery -A TalentHunt worker --loglevel=info --pool=solo
```
