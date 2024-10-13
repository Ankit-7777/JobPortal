from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import (
    job_search,
    application_list,
    apply_job,
    signup_view,
    job_list_view,
    job_detail_view,
    create_job_view,
    update_job_view,
    delete_job_view,
    employee_dashboard_view,
    recruiter_dashboard_view,
    user_logout,
    login_view,
    employee_profile_update,
    recruiter_profile_update,
    application_detail_view,
)


urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('employee/profile-update/', employee_profile_update, name='employee_profile_update'),
    path('recruiter/profile-update/', recruiter_profile_update, name='recruiter_profile_update'),
    path('', job_list_view, name='job_list'),
    path('jobs/search/', job_search, name='job_search'),
    path('jobs/<int:job_id>/', job_detail_view, name='job_detail'),
    path('jobs/<int:job_id>/apply/', apply_job, name='apply_job'),
    path('applications/', application_list, name='application_list'),
    path('applications/<int:application_id>/', application_detail_view, name='application_detail'),
 
    path('employee/dashboard/', employee_dashboard_view, name='employee_dashboard'),
    path('recruiter/dashboard/', recruiter_dashboard_view, name='recruiter_dashboard'),
    path('jobs/create/', create_job_view, name='create_job'),
    path('jobs/<int:job_id>/update/', update_job_view, name='job_update'),
    path('jobs/<int:job_id>/delete/', delete_job_view, name='job_delete'),
    # path('applications/<int:application_id>/update-status/', update_application_status_view, name='update_application_status'),
    
    path('logout/', views.user_logout, name='logout'),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


