from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.welcome_view, name='welcome'),
    path('dashboard/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('candidate/dashboard/', views.candidate_dashboard_view, name='candidate_dashboard'),
    path('employee/dashboard/', views.employee_dashboard_view, name='employee_dashboard'),
    path('hr/dashboard/', views.hr_dashboard_view, name='hr_dashboard'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('pm/dashboard/', views.pm_dashboard_view, name='pm_dashboard'),
    path('pm/candidates/<int:candidate_id>/', views.pm_candidate_results_view, name='pm_candidate_results'),
    path('test/consent/', views.test_consent_view, name='test_consent'),
    path('test/<int:question_index>/', views.test_page_view, name='test_page'),
    path('api/execute-code/', views.execute_code_view, name='execute_code'),
    path('api/confirm-candidate/<int:candidate_id>/', views.confirm_candidate_view, name='confirm_candidate'),
    path('api/submit-test/', views.submit_test_view, name='submit_test'),
    path('submission/success/', views.submission_success_view, name='submission_success'),
    path('logout/', auth_views.LogoutView.as_view(next_page='welcome'), name='logout'),
    path('api/send-exam-email/', views.send_exam_email_view, name='send_exam_email'),
    path('api/send-offer-email/', views.send_offer_email_view, name='send_offer_email'),
    path('api/send-all-exam-emails/', views.send_all_exam_emails_view, name='send_all_exam_emails'),
    path('api/reject-candidate/<int:candidate_id>/', views.reject_candidate_view, name='reject_candidate'),
    path('api/send-rejection-email/<int:candidate_id>/', views.send_rejection_email_view, name='send_rejection_email'),

]