import uuid
from django.db import models
from django.db.models import JSONField
from django.contrib.auth.models import AbstractUser

TYPE_CHOICES = (
    ('Number', 'Number'),
    ('Text', 'Text'),
    ('TextArea', 'TextArea'),
    ('Email', 'Email'),
    ('List', 'List'),
    ('Radio', 'Radio'),
)
FORM_CHOICES = (
    ('o', 'Open'),
    ('c', 'Close'),
)
ROLE_CHOICES = (
    ('user', 'User'),
    ('admin', 'Admin'),
    ('dashboard', 'Dashboard'),
)

class Section(models.Model):
    name = models.CharField(max_length=50)
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name

class Division(models.Model):
    name = models.CharField(max_length=50)
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=50)
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=50)
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class CompanyJson(models.Model):
    data = JSONField("Company")
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    def __str__(self):
        return str(self.data.get("city"))
    

class JobTitle(models.Model):
    name = models.CharField(max_length=50)
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    def __str__(self):
        return self.name


class AuthUser(AbstractUser): 
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE,null=True,blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL,null=True,blank=True)
    role = models.CharField(choices=ROLE_CHOICES,
                              max_length=220, default='user') 

class Employee(models.Model):
    employee_id = models.IntegerField()
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True,blank=True)
    phone_number = models.CharField(max_length=50,null=True,blank=True)
    job_type = models.CharField(max_length=50,null=True,blank=True)
    job_title = models.CharField(max_length=100,null=True,blank=True)
    section = models.CharField(max_length=50,null=True,blank=True)
    division = models.CharField(max_length=50,null=True,blank=True)
    actual_zone = models.CharField(max_length=50,null=True,blank=True)
    department = models.CharField(max_length=50,null=True,blank=True)
    company = models.CharField(max_length=50,null=True,blank=True)        
    emergency_number = models.CharField(max_length=50,null=True,blank=True)
    emergency_email = models.EmailField(null=True,blank=True)
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
       indexes = [
           models.Index(fields=['name',]),
           models.Index(fields=['section',]),
           models.Index(fields=['company',]),
           models.Index(fields=['employee_id',]),
                ]
       
    def __str__(self):
        return self.name


class Tenant(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100,blank=True,null=True)
    image_url = models.TextField(null=True,blank=True)
    has_cords = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Week(models.Model):
    number = models.CharField(max_length=100)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.number


class Form(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    week = models.OneToOneField(Week, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    status = models.CharField(choices=FORM_CHOICES,
                              max_length=200, default='o')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    questions = models.ManyToManyField("Question") 
    
    class Meta:
       indexes = [models.Index(fields=['id',])]
    
    def __str__(self):
        return self.title
    


class Question(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    type = models.CharField(choices=TYPE_CHOICES, max_length=200)
    dashboard = models.BooleanField(default=False)
    basicquestion = models.BooleanField(default=False)
    required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
       indexes = [
           models.Index(fields=['text',]),
                ]
    def __str__(self):
        return self.text


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
       indexes = [models.Index(fields=['value'])]
    def __str__(self):
        return self.value


class Answer(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    form = models.ForeignKey(Form, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
       indexes = [
           models.Index(fields=['answer',]),
                ]
    def __str__(self):
        return str(self.answer)
