from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from .models import SelectedCandidate, Candidate, Employee, TestResult, Question
import json
import docker
import os
import tempfile
import threading
import random 
from django.core.mail import send_mail

#Docker client instance
client = docker.from_env()

def welcome_view(request):
    """
    Renders the main welcome page.
    """
    return render(request, 'welcome.html')

@login_required
def candidate_dashboard_view(request):
    """
    Renders the dashboard for Candidate users.
    """
    if request.user.user_type != 'candidate' and not request.user.is_superuser:
        return redirect('dashboard_redirect')
    
    warning_message = request.session.pop('consent_denied', None)
    
    context = {'user': request.user}
    if warning_message:
        context['warning'] = warning_message
    
    return render(request, 'candidate_dashboard.html', context)

@login_required
def employee_dashboard_view(request):
    """
    Renders the dashboard for Employee users.
    """
    if request.user.user_type != 'employee' and not request.user.is_superuser:
        return redirect('dashboard_redirect')
    return render(request, 'employee_dashboard.html', {'user': request.user})

@login_required
def admin_dashboard_view(request):
    """
    Renders a simple dashboard for Admin users.
    """
    if request.user.user_type != 'admin' and not request.user.is_superuser:
        return redirect('dashboard_redirect')
    return render(request, 'admin_dashboard.html', {'user': request.user})

@login_required
def hr_dashboard_view(request):
    if request.user.user_type != 'hr' and not request.user.is_superuser:
        return redirect('dashboard_redirect')

    all_candidates_from_candidate_table = Candidate.objects.all()
    final_candidates = SelectedCandidate.objects.filter(status='final_selected')
    rejected_candidates = SelectedCandidate.objects.filter(status='rejected')

    context = {
        'user': request.user,
        'all_candidates_from_candidate_table': all_candidates_from_candidate_table,
        'final_candidates': final_candidates,
        'rejected_candidates': rejected_candidates, 
    }

    return render(request, 'hr_dashboard.html', context)

@login_required
def dashboard_redirect_view(request):
    if request.user.user_type == 'candidate':
        return redirect('test_consent')
    elif request.user.user_type == 'hr':
        return redirect('hr_dashboard')
    elif request.user.user_type == 'pm':
        return redirect('pm_dashboard')
    elif request.user.user_type == 'employee':
        return redirect('employee_dashboard')
    elif request.user.user_type == 'admin':
        return redirect('admin_dashboard')
    else:
        return render(request, 'generic_dashboard.html', {'user': request.user, 'message': 'Welcome to your generic dashboard!'})

@login_required
def test_consent_view(request):
    if request.user.user_type != 'candidate':
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        if request.POST.get('consent') == 'yes':
            all_question_ids = list(Question.objects.values_list('id', flat=True))
            selected_ids = random.sample(all_question_ids, 3)
            request.session['selected_questions'] = selected_ids
            request.session['current_question_index'] = 0
            return redirect('test_page', question_index=0)
        else:
            request.session['consent_denied'] = 'You must agree to the terms to take the exam.'
            return redirect('candidate_dashboard')

    return render(request, 'test_consent.html', {'user': request.user})

@login_required
def test_page_view(request, question_index):
    if request.user.user_type != 'candidate':
        return redirect('dashboard_redirect')

    selected_ids = request.session.get('selected_questions')
    if not selected_ids or question_index >= len(selected_ids):
        return redirect('submission_success')

    question_id = selected_ids[question_index]
    
    try:
        question_data = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return redirect('dashboard_redirect')

    context = {
        'user': request.user,
        'question_text': question_data.question_text,
        'question_number': question_id,
        'current_question_index': question_index,
        'test_case_text': question_data.test_case_display,
    }

    return render(request, 'test_page.html', context)

def execute_code_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        code = data.get('code', '')
        question_number = data.get('question_number', 1)

        try:
            question_data = Question.objects.get(pk=question_number)
        except Question.DoesNotExist:
            return JsonResponse({'status': 'Failed', 'output': 'Invalid question number.'})

        test_case = question_data.test_case
        expected_output = question_data.expected_output
        
        full_code = code + "\n" + test_case

        print(full_code)
        
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.py') as tmp_file:
            tmp_file.write(full_code)
            tmp_file_path = tmp_file.name

        try:
            output_bytes = client.containers.run(
                'python-compiler',
                command=['python', f'/usr/src/app/{os.path.basename(tmp_file_path)}'],
                volumes={tmp_file_path: {'bind': f'/usr/src/app/{os.path.basename(tmp_file_path)}', 'mode': 'ro'}},
                network_disabled=True,
                mem_limit='256m',
                cpu_period=100000,
                cpu_quota=50000,
                remove=True,
                detach=False
            )
            
            output = output_bytes.decode('utf-8')
            
            if output == expected_output:
                status = "Passed"
            else:
                status = "Failed"
            
            return JsonResponse({'status': status, 'output': output})

        except docker.errors.ContainerError as e:
            return JsonResponse({'status': 'Failed', 'output': e.stderr.decode('utf-8')})
        except Exception as e:
            return JsonResponse({'status': 'Failed', 'output': f"An error occurred: {str(e)}"})
        finally:
            os.remove(tmp_file_path)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def submission_success_view(request):
    if request.user.user_type != 'candidate':
        return redirect('dashboard_redirect')
    return render(request, 'submission_success.html')

@login_required
def submit_test_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_email = request.user.email

        try:
            candidate_instance = Candidate.objects.get(email=user_email)
            TestResult.objects.create(
                candidate=candidate_instance,
                q1_code=data['q1']['code'],
                q1_output=data['q1']['output'],
                q1_status=data['q1']['status'],
                q2_code=data['q2']['code'],
                q2_output=data['q2']['output'],
                q2_status=data['q2']['status'],
                q3_code=data['q3']['code'],
                q3_output=data['q3']['output'],
                q3_status=data['q3']['status']
            )
            return JsonResponse({'status': 'success'})
        except Candidate.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Candidate not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def pm_dashboard_view(request):
    if request.user.user_type != 'pm' and not request.user.is_superuser:
        return redirect('dashboard_redirect')

    confirmed_emails = SelectedCandidate.objects.values_list('candidate_email', flat=True)
    test_results = TestResult.objects.exclude(candidate__email__in=confirmed_emails)
    context = {
        'user': request.user,
        'test_results': test_results,
    }

    return render(request, 'pm_dashboard.html', context)

@login_required
def pm_candidate_results_view(request, candidate_id):
    if request.user.user_type != 'pm' and not request.user.is_superuser:
        return redirect('dashboard_redirect')

    result = get_object_or_404(TestResult, pk=candidate_id)

    context = {
        'user': request.user,
        'result': result,
    }

    return render(request, 'pm_candidate_results.html', context)

@login_required
def confirm_candidate_view(request, candidate_id):
    if request.user.user_type != 'pm':
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        try:
            test_result = get_object_or_404(TestResult, pk=candidate_id)
            candidate_email = test_result.candidate.email
            SelectedCandidate.objects.update_or_create(
                candidate_email=candidate_email,
                defaults={'status': 'final_selected'}
            )
            return JsonResponse({'status': 'success'})
        except TestResult.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Test result not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

def send_offer_email_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email', None)

        if not email:
            return JsonResponse({'status': 'error', 'message': 'Email address not provided.'}, status=400)

        subject = 'Congratulations! You have been hired!'
        message = f"Dear Candidate,\n\nCongratulations! We are pleased to offer you a position at our company. We were impressed with your coding skills and believe you would be a great fit for our team.\n\nWe will be in touch shortly with more details.\n\nSincerely,\nThe Hiring Team"
        from_email = 'sstjgpt@gmail.com'
        try:
            send_mail(subject, message, from_email, [email])
            return JsonResponse({'status': 'success', 'message': 'Email sent successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to send email: {str(e)}'}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

def send_exam_email_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email', None)
        password = data.get('password', None)
        
        if not email or not password:
            return JsonResponse({'status': 'error', 'message': 'Email or password not provided.'}, status=400)

        login_url = request.build_absolute_uri('/login/')

        subject = 'Invitation to Our Coding Exam'
        message = f"""Dear Candidate,

We are pleased to invite you to take our coding exam. Please use the following credentials to log in and access the test:

Login Link: {login_url}
Email: {email}
Password: {password}

Best of luck!

Sincerely,
The Hiring Team
"""
        from_email = 'sstjgpt@gmail.com'
        
        try:
            send_mail(subject, message, from_email, [email])
            return JsonResponse({'status': 'success', 'message': 'Email sent successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to send email: {str(e)}'}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

def send_all_exam_emails_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        emails = data.get('emails', [])

        if not emails:
            return JsonResponse({'status': 'error', 'message': 'No email addresses provided.'}, status=400)

        candidates = Candidate.objects.filter(email__in=emails)
        login_url = request.build_absolute_uri('/login/')
        from_email = 'sstjgpt@gmail.com'
        
        for candidate in candidates:
            subject = 'Invitation to Our Coding Exam'
            message = f"""Dear Candidate,

We are pleased to invite you to take our coding exam. Please use the following credentials to log in and access the test:

Login Link: {login_url}
Email: {candidate.email}
Password: {candidate.password}

Best of luck!

Sincerely,
The Hiring Team
"""
            try:
                send_mail(subject, message, from_email, [candidate.email])
            except Exception as e:
                print(f"Failed to send email to {candidate.email}: {e}")

        return JsonResponse({'status': 'success', 'message': 'Emails sent successfully.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@login_required
def reject_candidate_view(request, candidate_id):
    if request.user.user_type != 'pm':
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        try:
            test_result = get_object_or_404(TestResult, pk=candidate_id)
            candidate_email = test_result.candidate.email
            SelectedCandidate.objects.update_or_create(
                candidate_email=candidate_email,
                defaults={'status': 'rejected'}
            )
            return JsonResponse({'status': 'success', 'message': 'Candidate rejected.'})
        except TestResult.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Test result not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


def send_rejection_email_view(request, candidate_id):
    if request.method == 'POST':
        try:
            test_result = get_object_or_404(TestResult, pk=candidate_id)
            candidate_email = test_result.candidate.email
            hr_email = 'sstjgpt@gmail.com'
            
            subject = 'Update on Your Application'
            message = f"Dear Candidate,\n\nThank you for your interest in our company and for taking the time to complete our coding exam. After careful consideration, we regret to inform you that we will not be moving forward with your application at this time.\n\nWe wish you the best.\n\nSincerely,\nThe Hiring Team"
            from_email = hr_email
            
            send_mail(subject, message, from_email, [candidate_email])
            return JsonResponse({'status': 'success', 'message': 'Rejection email sent successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to send email: {str(e)}'}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)