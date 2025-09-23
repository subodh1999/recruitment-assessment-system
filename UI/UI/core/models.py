from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('candidate', 'Candidate'),
        ('employee', 'Employee'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='admin')

    def __str__(self):
        return self.username

class Candidate(models.Model):
    id = models.IntegerField(primary_key=True)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255) 

    class Meta:
        managed = False 
        db_table = 'candidate'

    def __str__(self):
        return self.email

class Employee(models.Model):
    id = models.IntegerField(primary_key=True) 
    designation = models.CharField(max_length=100)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255) 

    class Meta:
        managed = False 
        db_table = 'employee' 

    def __str__(self):
        return self.email
    
class SelectedCandidate(models.Model):
    candidate_email = models.CharField(max_length=255, unique=True)
    status_choices = (
        ('selected', 'Selected'),
        ('final_selected', 'Final Selected'),
        ('rejected', 'Rejected'), 
    )
    status = models.CharField(max_length=20, choices=status_choices, default='selected')

    def __str__(self):
        return f"{self.candidate_email} - {self.status}"
    
class TestResult(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    # Question 1
    q1_code = models.TextField(blank=True)
    q1_output = models.TextField(blank=True)
    q1_status = models.CharField(max_length=20, blank=True)

    # Question 2
    q2_code = models.TextField(blank=True)
    q2_output = models.TextField(blank=True)
    q2_status = models.CharField(max_length=20, blank=True)

    # Question 3
    q3_code = models.TextField(blank=True)
    q3_output = models.TextField(blank=True)
    q3_status = models.CharField(max_length=20, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Test Result for {self.candidate.email}"

class Question(models.Model):
    question_text = models.TextField()
    test_case = models.TextField()
    expected_output = models.TextField()
    test_case_display = models.TextField(blank=True)
    
    def __str__(self):
        return f"Question {self.pk}"