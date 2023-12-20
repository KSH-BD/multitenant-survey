import os
import re
import csv
import json
import folium
import string
import pandas as pd
from .models import *
from uuid import uuid4
from django import forms
import plotly.express as px
from django.conf import settings
from django.db.models import Count
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .decorators import unauthenticated_users, adminonly
from django.contrib.auth.decorators import login_required
from folium.plugins import FastMarkerCluster, MarkerCluster
from django.contrib.auth import authenticate, login, logout
from .forms import EmployeeForm, TenantForm, WeekForm, FormForm, QuestionForm, QuestionOptionForm, AnswerForm, SectionForm, DivisionForm, DepartmentForm, CompanyForm, JobTitleForm, LoginForm, RegisterForm, UserUpdateForm, SectionSelectForm

@login_required(login_url='/survey/login/')
@unauthenticated_users
def create_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success')
    else:
        form = EmployeeForm()
    return render(request, 'create_employee.html', {'form': form})

@login_required(login_url='/survey/login/')
def tenant_list(request):
    if request.user.username != "admin":
        return redirect("tenant_details",id=request.user.tenant.id)
    tenants = Tenant.objects.all()
    return render(request, 'survey/tenant_list.html', {'tenants': tenants})


@login_required(login_url='/survey/login/')
@unauthenticated_users
def tenant_details(request, id):
    tenant = Tenant.objects.get(id=id)
    return render(request, 'survey/tenant_details.html', {'tenant': tenant})


@login_required(login_url='/survey/login/')
@unauthenticated_users
def week_details(request, id):
    tenant = Tenant.objects.get(id=id)
    return render(request, 'survey/week_details.html', {'tenant': tenant})

@login_required(login_url='/survey/login/')
@unauthenticated_users
def create_tenant(request):
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tenant_list')
    else:
        form = TenantForm()
    return render(request, 'survey/create_tenant.html', {'form': form})

def lookahead(iterable):
    """Pass through all values from the given iterable, augmented by the
    information if there are more values to come after the current one
    (True), or if it is the last value (False).
    """
    # Get an iterator and pull the first value.
    it = iter(iterable)        
    try:
        last = next(it)
    except StopIteration:
        return
    # Run the iterator to exhaustion (starting from the second value).
    for val in it:
        # Report the *previous* value (more to come).        
        
        yield last, True        
        last = val
    # Report the last value.
    yield last, False

@login_required(login_url='/survey/login/')
@unauthenticated_users
def week_form_details(request, id, formid):
    tenant = Tenant.objects.prefetch_related(
        "employee_set__answer_set").get(id=id)
    form = tenant.form_set.get(id=formid)

    # print(Answer.objects.filter(form=form).all())
    # data = [{'emp': emp, 'data': [x for x in emp.answer_set.filter(
    #     form=form).all()]} for emp in tenant.employee_set.all()]
    data = []
    temp = []
    prev = None
    for curr,has_more in lookahead(form.answer_set.order_by("employee__name").all()):   
        if not has_more:
            temp.append(curr)
            data.append({"emp":prev.employee,"data":temp})            
            break            
        
        if not prev:
            prev = curr
            temp.append(curr)
        elif curr.employee.employee_id == prev.employee.employee_id:
            prev = curr
            temp.append(curr)
            # print(temp)        
        else:
            data.append({"emp":prev.employee,"data":temp})
            temp = []
            temp.append(curr)
            prev = curr
    # print(data)
        # if not prev or curr.employee.employee_id == prev.employee.employee_id:
        #     print(f"prev : {prev}")
        #     print(f"curr : {curr}")
        #     prev = curr
        #     temp.append(curr)            
        # else:
        #     print("here")
        #     data.append({"Employee":prev.employee,"data":temp})
        #     temp.clear()
        #     temp.append(curr)       
        #     prev = curr
    
    # print(data)
    
    # print(data1)

    return render(request, 'survey/week_form_details.html', {'form': form, "data": data, "tenant": tenant})

@login_required(login_url='/survey/login/')
@unauthenticated_users
def create_week(request, id):
    tenant = Tenant.objects.get(id=id)

    questions = tenant.question_set.all()
    if request.method == 'POST':
        form = WeekForm(request.POST)
        if form.is_valid():
            if tenant.week_set.filter(number=form.cleaned_data.get("number")).first():
                form.add_error('number', 'week id already existed')
                return render(request, 'survey/create_week.html', {'form': form})
            else:
                w = form.save()
                f = Form(title=f"{w.tenant.name}_Week_{form.cleaned_data['number']}_Form",
                         week=w, tenant=w.tenant)
                f.save()
                f.questions.add(*questions)
            return redirect('week_details', id=id)
    else:
        form = WeekForm()
        field = form.fields['tenant']
        field.initial = Tenant.objects.get(id=id)
        field.widget = field.hidden_widget()

    return render(request, 'survey/create_week.html', {'form': form})


def check_employee_id(request):
    if request.method == 'POST':
        messages.error(request, "employee with thids id already submited")

    return render(request, 'survey/employee_id_form.html')


def change_form_status(request):
    id = request.POST.get('id')
    form = Form.objects.get(id=id)
    if form:
        form.status = 'c' if form.status == 'o' else 'o'
        form.save()
    return render(request, 'survey/week_details.html', {"tenant": form.tenant})

def get_company_zone(request,id,formid):
    tenant = Tenant.objects.get(id=id)
    f = Form.objects.get(id=formid)
    cityid = request.POST.get("Current_City__-_المدينة_الحالية")
    initdata = ""
    if cityid:
        city = QuestionOption.objects.get(id=cityid)    
        initdata = CompanyJson.objects.filter(data__city=city.value).first()
    form = FormForm(id=formid)
    for f in form.fields.copy():        
        if f not in ["Company_-_الشركة_","Current_Zone_-_الزون_الحالي_"]:
            form.fields.pop(f)
    if initdata:
        form.initial["Company_-_الشركة_"] = initdata.data.get("company")
        form.initial["Current_Zone_-_الزون_الحالي_"] = initdata.data.get("zone")    
    
    return render(request,"survey/company_zone.html",{"companyform":form})

def survey_form(request, id,formid):
    tenant = Tenant.objects.get(id=id)
    f = Form.objects.get(id=formid)
    if f.tenant != tenant:
        return render(request,"survey/not_found.html")
    
    if f.status == "c":
        return render(request, "survey/formclosed.html")

    if "Hx-Request" in request.headers:
        employeeid = request.POST.get("employeeid")
        employee = Employee.objects.filter(
            employee_id=employeeid, tenant=f.tenant).first()
        if not employee:
            messages.error(request, "no employee with this ID found")
            return render(request, 'survey/form.html', {'f': f})

        if Answer.objects.filter(form=f, employee=employee):
            messages.error(
                request, "employee with this ID already submited for this week")
            return render(request, 'survey/form.html', {'f': f})

        form = FormForm(id=formid)
        if tenant.name == "FM":            
            city = "Current City  - المدينة الحالية?"
            cityname = f'{city.replace(" ", "_").replace("?","")}'            
            form.fields[cityname].widget.attrs.update({"hx-post": f"/survey/tenant/{tenant.id}/get_company_zone/{form.id}/","hx-target":"#company_zone","hx-swap":"innerHTML","hx-trigger":"load, change"})
            # data = 
            x = "Company - الشركة ?"
            y = "Current Zone - الزون الحالي ?"
            field_name = f'{x.replace(" ", "_").replace("?","")}'
            field_name1 = f'{y.replace(" ", "_").replace("?","")}'
            form.fields.pop(field_name)
            form.fields.pop(field_name1)
        form.initialFormFields(employee)
        return render(request, 'survey/survey_form.html', {'form': form, 'f': f, "employee": employee})

    return render(request, 'survey/employee_id_form.html', {'f': f})

def submit_survey_form(request, id,formid):
    tenant = Tenant.objects.get(id=id)
    f = Form.objects.get(id=formid)
    employee = Employee.objects.filter(employee_id=int(
        request.POST.get("employeeid")), tenant=f.tenant).first()

    # if Answer.objects.filter(form=f, employee=employee):
    #     messages.error(request, "employee with thids id already submited")
    #     return render(request, 'survey/employee_id_form.html', {'id': formid})
    
    if request.method == 'POST':
        form = FormForm(formid, request.POST)            
        if form.is_valid():
            for x, y in form.cleaned_data.items():
                dataid = form.fields[x].widget.attrs['data-id']
                q = Question.objects.get(id=dataid)
                answer = Answer(employee=employee, form=f,
                                question=q, answer=y)
                answer.save()
            return render(request, "survey/success.html")
        else:         
            if tenant.name == "FM":            
                city = "Current City  - المدينة الحالية?"
                cityname = f'{city.replace(" ", "_").replace("?","")}'            
                form.fields[cityname].widget.attrs.update({"hx-post": f"/survey/tenant/{tenant.id}/get_company_zone/{f.id}/","hx-target":"#company_zone","hx-swap":"innerHTML","hx-trigger":"load, change"})
                # data = 
                x = "Company - الشركة ?"
                y = "Current Zone - الزون الحالي ?"
                field_name = f'{x.replace(" ", "_").replace("?","")}'
                field_name1 = f'{y.replace(" ", "_").replace("?","")}'
                form.fields.pop(field_name)
                form.fields.pop(field_name1)  
            return render(request, "survey/survey_form.html", {'form': form, 'f': f, "employee": employee})

        return render(request, "survey/success.html")


def login_page(request):
    if request.user.is_authenticated:
        if request.user.username == "admin":
            return redirect("tenant_list")            
        return redirect("tenant_details", id=request.user.tenant.id)
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:            
            login(request, user)
            if request.user.username == "admin":
                return redirect("tenant_list") 
            return redirect("tenant_details", id=request.user.tenant.id)
    form = LoginForm()
    return render(request, "survey/login.html", {"form": form})

def change_password(request,id,userid):
    tenant = Tenant.objects.get(id=id)
    user = AuthUser.objects.get(id=userid)
    # if user.tenant != tenant:
    #     return redirect("users_list", id=tenant.id)
    if request.method == "POST":
        passwd = request.POST.get("change_password")
        user.set_password(passwd)
        user.save()
        return redirect("users_list", id=tenant.id)
    return render(request,'survey/change_password.html',{"tenant":tenant,"user":user})

@login_required(login_url='/survey/login/')
@unauthenticated_users
@adminonly
def users_register(request, id):
    tenant = Tenant.objects.get(id=id)
    form = RegisterForm()

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            # print(form.cleaned_data)
            form.save()
            return redirect("users_list", id=tenant.id)
    if tenant.name != "FM":
        form.fields.pop('company')
        
    form.initial['tenant'] = tenant
    return render(request, "survey/users_register.html", {"form": form,"tenant":tenant})


@login_required(login_url='/survey/login/')
@unauthenticated_users
@adminonly
def users_edit(request, id, userid):
    tenant = Tenant.objects.get(id=id)
    user = AuthUser.objects.get(id=userid)
    form = UserUpdateForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        return redirect("users_list", id=tenant.id)

    form.initial['tenant'] = tenant
    return render(request, "survey/users_edit.html", {"form": form,"tenant":tenant})

@login_required(login_url='/survey/login/')
@unauthenticated_users
def dashboard_list(request,id):
    tenant = Tenant.objects.get(id=id)
    
    return render(request,"survey/dashboard_list.html",{"tenant":tenant})

@login_required(login_url='/survey/login/')
@unauthenticated_users
@adminonly
def users_list(request, id):
    tenant = Tenant.objects.get(id=id)
    return render(request, "survey/users_list.html", {"tenant": tenant})


def logout_page(request):
    logout(request)
    return redirect("login_page")


def data(request,id):
    # city = ["Madani", "Kenana", "Shandi", "Kassala", "Atbara", "Karima", "Marawi", "Nori", "Sinnar", "Obied", "Alnihood", "Umrawaba", "Managil", "New Halfa", "Port Sudan", "Sinkat", "KTM", "Dubai / UAE", "Dongola", "Cairo / Egypt", "Kamlin", "Kosti", "Alhaj Abdalla", "Rahad", "Dewaim", "Gazira", "Gitena", "Hasahisa", "Jabalain", "Genina", "Zalingy", "Adre / Tchad", "Mershing",
    #         "Murne", "Nyala", "OMD", "Deain", "Tulus", "Fashir", "Umkdada", "Dalang", "Babanosa", "Foula", "Kadogly", "Abu Jebaiha", "Gadarif", "Al Faw", "Doha / Qatar", "Barbar", "Wadi Halfa", "KSA", "KTN", "Singa", "Unknown ", "Palastine", "Al Damar", "Karma", "Kagbar", "Addis Ababa / Ethiopia", "Damazin", "Al Rahad", "Rabak", "Darfur ", "DONGOLA ", "Kass", "Libya", "Tandalty"]
    # q = Question.objects.get(text="Current City ?")
    # QuestionOption.objects.bulk_create([QuestionOption(question=q,value=x) for x in city])
    tenant = Tenant.objects.get(id=id)
    
    # tenant.employee_set.all().delete()
    
    with open('survey/utils/fm_users1.csv') as f:
        empdata = csv.reader(f.readlines())        
        # tenant.companyjson_set.bulk_create([CompanyJson(data={"city":i[0],"company":i[1],"zone":i[2]},tenant=tenant) for i in empdata])
        
        # tenant.employee_set.bulk_create([
        # Employee(employee_id=i[0], name=i[1], email=i[3], section=i[5], company="KSHC", job_title=i[2],
        #                         phone_number=i[4],division="Call Center",department="Call Center", tenant=tenant) for i in empdata
        # ])
        
        # tenant.employee_set.bulk_create([Employee(
        #             employee_id=i[0], name=i[1], email=i[8], section=i[2], company=i[3], job_title=i[4],job_type=i[5],
        #             phone_number=i[6],actual_zone=i[9], tenant=tenant) for i in empdata])
        # for i in empdata:            
        #     employee = Employee(employee_id=i[0], name=i[1], email=i[3], section=i[5], company="KSHC", job_title=i[2],
        #                         phone_number=i[4],division="Call Center",department="Call Center", tenant=tenant)
        #     # print(employee)
        #     employee.save()
            # break

    
    context = {"employee": tenant.employee_set.all()}
    return render(request, "survey/data.html", context)

@login_required(login_url='/survey/login/')
@unauthenticated_users
def employeelist(request, id):
    tenant = Tenant.objects.get(id=id)
    context = {"tenant": tenant}
    return render(request, "survey/employeelist.html", context)

@login_required(login_url='/survey/login/')
@unauthenticated_users
def employeedetails(request, id, employeeid):
    tenant = Tenant.objects.get(id=id)
    employee = tenant.employee_set.filter(employee_id=employeeid).first()

    formsdata = [[{"week": form.week, "question": x, "answer": x.answer_set.filter(employee=employee, form=form).first(
    )} for x in tenant.question_set.order_by("created_at").all()] for form in tenant.form_set.all()]
    context = {"employee": employee, "data": formsdata}
    return render(request, "survey/employeedetails.html", context)

@login_required(login_url='/survey/login/')
@unauthenticated_users
def createemployee(request, id):
    tenant = Tenant.objects.get(id=id)
    form = EmployeeForm()

    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            empid = form.cleaned_data.get("employee_id")
            email = form.cleaned_data.get("email")
            if tenant.employee_set.filter(employee_id=empid).first():
                form.add_error(
                    'employee_id', 'user with this id already exist')
                # form.add_error('email', 'user with this email already exist')            
            else:
                i = form.save(commit=False)
                i.section = form.cleaned_data.get('section').name if form.cleaned_data.get('section') else ""
                i.division = form.cleaned_data.get('division').name if form.cleaned_data.get('division') else ""
                i.department = form.cleaned_data.get('department').name if form.cleaned_data.get('department') else ""
                i.company = form.cleaned_data.get('company').name if form.cleaned_data.get('company') else ""
                i.job_title = form.cleaned_data.get('job_title').name if form.cleaned_data.get('job_title') else ""
                i.save()
                return redirect('employeelist', id=tenant.id)

    form.initial['tenant'] = tenant
    form.fields['section'].queryset = tenant.section_set
    form.fields['division'].queryset = tenant.division_set
    form.fields['department'].queryset = tenant.department_set
    form.fields['company'].queryset = tenant.company_set
    form.fields['job_title'].queryset = tenant.jobtitle_set

    return render(request, 'survey/employee_create.html', {"form": form, "tenant": tenant})


@login_required(login_url='/survey/login/')
@unauthenticated_users
def updateemployee(request, id, empid):
    tenant = Tenant.objects.get(id=id)
    employee = Employee.objects.get(id=empid)
    form = EmployeeForm(request.POST or None, instance=employee)
    # if request.method == "POST":
    #     form = EmployeeForm(request.POST)
    if form.is_valid():
        empid = form.cleaned_data.get("employee_id")
        email = form.cleaned_data.get("email")

        # if tenant.employee_set.filter(employee_id=empid).first() or tenant.employee_set.filter(email=email).first():
        #     form.add_error('employee_id','user with this id already exist')
        #     form.add_error('email','user with this email already exist')
        # else:
        i = form.save(commit=False)
        i.section = form.cleaned_data.get('section').name if form.cleaned_data.get('section') else ""
        i.division = form.cleaned_data.get('division').name if form.cleaned_data.get('division') else ""
        i.department = form.cleaned_data.get('department').name if form.cleaned_data.get('department') else ""
        i.company = form.cleaned_data.get('company').name if form.cleaned_data.get('company') else ""
        i.job_title = form.cleaned_data.get('job_title').name if form.cleaned_data.get('job_title') else ""
        i.save()
        return redirect('employeelist', id=tenant.id)
        # if form.is_valid():

        #     # empid = form.cleaned_data.get("employee_id")
        #     # email = form.cleaned_data.get("email")
        #     # if tenant.employee_set.filter(employee_id=empid).first():
        #     #     form.add_error('employee_id','user with this id already exist')
        #     # if tenant.employee_set.filter(email=email).first():
        #     #     form.add_error('email','user with this email already exist')
        #     # else:
        #     # employee.employee_id = form.cleaned_data.get("employee_id")
        #     employee.name = form.cleaned_data.get("name")
        #     employee.email = form.cleaned_data.get("email")
        #     employee.section = form.cleaned_data.get("section")
        #     employee.division = form.cleaned_data.get("division")
        #     employee.department = form.cleaned_data.get("department")
        #     employee.company = form.cleaned_data.get("company")
        #     employee.job_title = form.cleaned_data.get("job_title")
        #     employee.job_type = form.cleaned_data.get("job_type")
        #     employee.phone_number = form.cleaned_data.get("phone_number")
        #     employee.emergency_number = form.cleaned_data.get("emergency_number")
        #     employee.emergency_email = form.cleaned_data.get("emergency_email")
        #     employee.tenant = form.cleaned_data.get("tenant")
        #     employee.save()
        # return redirect('employeelist', id=tenant.id)

    # form.initial['employee_id'] = employee.employee_id
    # form.initial['name'] = employee.name
    # form.initial['email'] = employee.email
    form.initial['tenant'] = tenant
    form.fields['section'].queryset = tenant.section_set
    form.fields['division'].queryset = tenant.division_set
    form.fields['department'].queryset = tenant.department_set
    form.fields['company'].queryset = tenant.company_set
    form.fields['job_title'].queryset = tenant.jobtitle_set

    form.initial['section'] = tenant.section_set.filter(
        name=employee.section).first()
    form.initial['division'] = tenant.division_set.filter(
        name=employee.division).first()
    form.initial['department'] = tenant.department_set.filter(
        name=employee.department).first()
    form.initial['company'] = tenant.company_set.filter(
        name=employee.company).first()
    form.initial['job_title'] = tenant.jobtitle_set.filter(
        name=employee.job_title).first()
    # form.initial['job_type'] = employee.job_type
    # form.initial['phone_number'] = employee.phone_number
    # form.initial['emergency_number'] = employee.emergency_number
    # form.initial['emergency_email'] = employee.emergency_email
    form.initial['tenant'] = tenant

    form.fields['employee_id'].widget.attrs.update({"readonly": True})
    # form.fields['section'].widget.attrs['class'] = "ui dropdown"
    return render(request, 'survey/employee_update.html', {"form": form, "tenant": tenant, "employee": employee})

@login_required(login_url='/survey/login/')
@unauthenticated_users
def questionoptions(request, id, qid):
    question = Question.objects.get(id=qid)
    if request.method == "POST":
        data = request.POST.getlist("tags")
        if data:
            for tag in json.loads(data[0]):
                qo = QuestionOption(question=question, value=tag.get('value'))
                qo.save()
            # return redirect('create_question', id=id)

    return render(request, "survey/questionoptions.html", {"question": question})

@login_required(login_url='/survey/login/')
@unauthenticated_users
def delete_question(request,id, qid):
    tenant = Tenant.objects.get(id=id)
    q = Question.objects.get(id=qid)    
    q.delete()
    
    return render(request, 'survey/create_question.html', {"tenant": tenant, "questions": tenant.question_set.all()})

    
@login_required(login_url='/survey/login/')
@unauthenticated_users
def questionoptionsdelete(request,id, qoid):
    qo = QuestionOption.objects.get(id=qoid)
    question = qo.question
    qo.delete()
    
    return render(request, "survey/questionoptions.html", {"question": question})

def edit_question(request,id,qid):
    tenant = Tenant.objects.get(id=id)
    question = Question.objects.get(id=qid)
    form = QuestionForm()    
    form.fields['datatype'].widget.attrs['class'] = "ui dropdown"
    form.fields['required'].widget.attrs['class'] = "ui dropdown"

    if request.method == "POST":
        text = request.POST.get("text")
        datatype = request.POST.get("datatype")
        required = request.POST.get("required")
        dashboard = request.POST.get("dashboard")
        
        question.text = text
        question.type = datatype
        question.required = True if required == "Yes" else False
        question.dashboard = True if dashboard == "on" else False 
        question.save()
        return redirect("create_question",id=tenant.id)
    
    form.initial["text"] = question.text
    form.initial["datatype"] = question.type
    form.initial["required"] = ("Yes","Yes") if question.required else ("No","No")
    form.initial["dashboard"] = question.dashboard
    form.initial["tenant"] = question.tenant
    
    return render(request,"survey/question_edite.html",{"form":form,"tenant":tenant,"question":question})

def cords_status(request, id):
    tenant = Tenant.objects.get(id=id)
    lat = tenant.question_set.filter(text="Latitude").first()
    lon = tenant.question_set.filter(text="Longitude").first()
    current_city = tenant.question_set.filter(text="Current City - المدينة الحالية?").first()
    company = tenant.question_set.filter(text="Company - الشركة ?").first()
    staff_situation = tenant.question_set.filter(text="Staff/Family Situation - حالة الموظف/الاسرة ?").first()
    laptop_situation = tenant.question_set.filter(text="Laptop Status - حالة الكمبيوتر المحمول ?").first()
    mobile_situation = tenant.question_set.filter(text="Mobile Status - حالة الهاتف ?").first()
    other_notes = tenant.question_set.filter(text="Any Other Note - اي ملاحظات اخري ?").first()
    network_availability = tenant.question_set.filter(text="Network Availability - توافر الشبكة ?").first()
    
    if staff_situation:
        staff_situation.questionoption_set.all().delete()
        staff_situation.delete() 
    
    else:
        ss = tenant.question_set.create(
        text="Staff/Family Situation - حالة الموظف/الاسرة ?", type="List",dashboard=True,basicquestion=True, required=True)        
        ss.questionoption_set.bulk_create([
            QuestionOption(question=ss,value="Intact/well"),
            QuestionOption(question=ss,value="Unsafe"),
            QuestionOption(question=ss,value="Injured/Harmed"),
            QuestionOption(question=ss,value="Emigrant/Refugee"),
        ]) 
    
    if network_availability:
        network_availability.questionoption_set.all().delete()
        network_availability.delete() 
    
    else:
        ss = tenant.question_set.create(
        text="Network Availability - توافر الشبكة ?", type="List",dashboard=True,basicquestion=True, required=True)        
        ss.questionoption_set.bulk_create([
            QuestionOption(question=ss,value="Stable"),
            QuestionOption(question=ss,value="Unavailable"),
            QuestionOption(question=ss,value="Unstable"),
            QuestionOption(question=ss,value="VPN Issues"),
            QuestionOption(question=ss,value="Weak Coverage"),
        ]) 
        
    current_city.delete() if current_city else tenant.question_set.create(
        text="Current City - المدينة الحالية?", type="List",dashboard=True,basicquestion=True, required=True)
    
    company.delete() if company else tenant.question_set.create(
        text="Company - الشركة ?", type="List",dashboard=True,basicquestion=True,  required=True) 
        
    if mobile_situation:
        mobile_situation.questionoption_set.all().delete()
        mobile_situation.delete()        
    else:        
        ms =  tenant.question_set.create(
            text="Mobile Status - حالة الهاتف ?", type="List",dashboard=True,basicquestion=True, required=True)            
        ms.questionoption_set.bulk_create([
            QuestionOption(question=ms,value="Good"),
            QuestionOption(question=ms,value="Lost"),
            QuestionOption(question=ms,value="Stolen"),
        ])
        
    if laptop_situation:
        tenant.has_cords = False
        laptop_situation.questionoption_set.all().delete()
        laptop_situation.delete() 
    else:        
        tenant.has_cords = True
        ls = tenant.question_set.create(
            text="Laptop Status - حالة الكمبيوتر المحمول ?", type="List",dashboard=True,basicquestion=True, required=True)     
        ls.questionoption_set.bulk_create([
            QuestionOption(question=ls,value="Good"),
            QuestionOption(question=ls,value="Lost"),
            QuestionOption(question=ls,value="Stolen"),
        ])
                                  
    lon.delete() if lon else tenant.question_set.create(
        text="Longitude", type="Text",dashboard=False,basicquestion=True, required=True)
    lat.delete() if lat else tenant.question_set.create(
        text="Latitude", type="Text",dashboard=False,basicquestion=True, required=True)    
    other_notes.delete() if other_notes else tenant.question_set.create(
        text="Any Other Note - اي ملاحظات اخري ?", type="TextArea",dashboard=False,basicquestion=True, required=False)    
    
                
    tenant.save()
    return render(request, 'survey/create_question.html', {"tenant": tenant, "questions": tenant.question_set.all()})

@login_required(login_url='/survey/login/')
@unauthenticated_users
@adminonly
def create_question(request, id):
    tenant = Tenant.objects.get(id=id)
    if "Hx-Request" in request.headers:
        form = QuestionForm()
        form.fields['datatype'].widget.attrs['class'] = "ui dropdown"
        form.fields['required'].widget.attrs['class'] = "ui dropdown"
        form.fields['dashboard'].widget.attrs['class'] = "ui dropdown"

        return render(request, 'survey/questionfragment.html', {'form': form})

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            text = request.POST.getlist("text")
            datatype = request.POST.getlist("datatype")
            required = request.POST.getlist("required")
            dashboard = request.POST.getlist("dashboard")
            data = list(zip(text, datatype, required, dashboard))
            for i in data:
                question = Question(
                    tenant=tenant, text=i[0], type=i[1], required=True if i[2] == "Yes" else False,dashboard=True if i[3] == "Yes" else False)
                question.save()

    return render(request, 'survey/create_question.html', {"tenant": tenant, "questions": tenant.question_set.all()})


def section_create_view(request, id):
    tenant = Tenant.objects.get(id=id)
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            form.save()
            form1 = EmployeeForm()
            form1.fields['section'] = forms.ModelChoiceField(
                label='Section', queryset=tenant.section_set)
            form1.initial['section'] = tenant.section_set.last()

            return render(request, "survey/employee_create.html", {"form": form1, "tenant": tenant})
    else:
        form = SectionForm()
        form.initial['tenant'] = tenant

    return render(request, 'survey/section_form.html', {'form': form, "tenant": tenant})


def division_create_view(request, id):
    tenant = Tenant.objects.get(id=id)
    if request.method == 'POST':
        form = DivisionForm(request.POST)
        if form.is_valid():
            form.save()
            form1 = EmployeeForm()
            form1.fields['division'] = forms.ModelChoiceField(
                label='Division', queryset=tenant.division_set)
            form1.initial['division'] = tenant.division_set.last()

            return render(request, "survey/employee_create.html", {"form": form1, "tenant": tenant})
    else:
        form = DivisionForm()
        form.initial['tenant'] = tenant

    return render(request, 'survey/division_form.html', {'form': form, "tenant": tenant})


def department_create_view(request, id):
    tenant = Tenant.objects.get(id=id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            form1 = EmployeeForm()
            form1.fields['department'] = forms.ModelChoiceField(
                label='Department', queryset=tenant.department_set)
            form1.initial['department'] = tenant.department_set.last()

            return render(request, "survey/employee_create.html", {"form": form1, "tenant": tenant})
    else:
        form = DepartmentForm()
        form.initial['tenant'] = tenant

    return render(request, 'survey/department_form.html', {'form': form, "tenant": tenant})


def company_create_view(request, id):
    tenant = Tenant.objects.get(id=id)
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            form1 = EmployeeForm()
            form1.fields['company'] = forms.ModelChoiceField(
                label='Company', queryset=tenant.company_set)
            form1.initial['company'] = tenant.company_set.last()

            return render(request, "survey/employee_create.html", {"form": form1, "tenant": tenant})
    else:
        form = CompanyForm()
        form.initial['tenant'] = tenant

    return render(request, 'survey/company_form.html', {'form': form, "tenant": tenant})


def job_title_create_view(request, id):
    tenant = Tenant.objects.get(id=id)
    if request.method == 'POST':
        form = JobTitleForm(request.POST)
        if form.is_valid():
            form.save()
            form1 = EmployeeForm()
            form1.fields['job_title'] = forms.ModelChoiceField(
                label='Job Title', queryset=tenant.jobtitle_set)
            form1.initial['job_title'] = tenant.jobtitle_set.last()

            return render(request, "survey/employee_create.html", {"form": form1, "tenant": tenant})
    else:
        form = JobTitleForm()
        form.initial['tenant'] = tenant

    return render(request, 'survey/job_title_form.html', {'form': form, "tenant": tenant})

@login_required(login_url='/survey/login/')
@unauthenticated_users
def section_list_view(request, id):
    tenant = Tenant.objects.get(id=id)
    sections = Section.objects.filter(tenant=tenant).all()
    return render(request, 'survey/section_list.html', {'sections': sections})

@login_required(login_url='/survey/login/')
@unauthenticated_users
def dashboard(request, id, formid):
    tenant = Tenant.objects.prefetch_related("employee_set").get(id=id)
    form = Form.objects.prefetch_related(
        "answer_set", "answer_set__question").get(id=formid)
    
    tiles = 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png'
    attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">Humanitarian OpenStreetMap Team</a> hosted by <a href="https://openstreetmap.fr/" target="_blank">OpenStreetMap France</a>'
    m = folium.Map(location=[15.6191, 32.5258], zoom_start=4,
                   tiles=tiles, attr=attr)
    mcluster = MarkerCluster(name="test").add_to(m)

    cords = []
    data = []
    
    tenant_question = tenant.question_set.first()
    
    lat = tenant.question_set.filter(text="Latitude").first()
    lon = tenant.question_set.filter(text="Longitude").first()
    longitude = []
    latitude = []
    
    allemp = set(x for x in tenant.employee_set.all())
    submited = set(x.employee for x in form.answer_set.all())    
    not_submited = allemp.difference(submited)    
        
    e_p_c = pd.DataFrame(list(form.tenant.employee_set.values(
        "company").order_by().annotate(nums_of_employess=Count("id"))))
    emp_pre_comapny = {"title": "number of employees per company", "label": e_p_c.company.values.tolist(
    ), "value": e_p_c.nums_of_employess.values.tolist()}

    for q in form.tenant.question_set.filter(dashboard=True).all():
        df = ""
        if "Hx-Request" in request.headers:
            section = request.POST.get("section")
            company = request.POST.get("company")

            allemp = set(x for x in tenant.employee_set.filter(section=section,company=company).all())
            submited = set(x.employee for x in form.answer_set.filter(employee__section=section,employee__company=company).all())    
            not_submited = allemp.difference(submited) 
    
            if section and company:
                df = pd.DataFrame(list(form.answer_set.filter(question__text=q.text, employee__section=section, employee__company=company).values(
                    "answer").order_by("question__id").annotate(nums_of_employess=Count("employee__id"))))
                idlist = [x.employee.employee_id for x in tenant_question.answer_set.filter(
                    form=form, employee__section=section, employee__company=company).order_by("employee_id").all()]
                namelist = [x.employee.name for x in tenant_question.answer_set.filter(
                    form=form, employee__section=section, employee__company=company).order_by("employee_id").all()]
                
                try:
                    latitude = [x.answer for x in lat.answer_set.filter(
                        form=form, employee__section=section, employee__company=company).order_by("employee_id").all()]
                    longitude = [x.answer for x in lon.answer_set.filter(
                        form=form, employee__section=section, employee__company=company).order_by("employee_id").all()]
                except:
                    print("no lat/lon")
                
                cords = list(zip(idlist, namelist, latitude, longitude))
            elif section:
                df = pd.DataFrame(list(form.answer_set.filter(question__text=q.text, employee__section=section).values(
                    "answer").order_by("question__id").annotate(nums_of_employess=Count("employee__id"))))
                idlist = [x.employee.employee_id for x in tenant_question.answer_set.filter(
                    form=form, employee__section=section).order_by("employee_id").all()]
                namelist = [x.employee.name for x in tenant_question.answer_set.filter(
                    form=form, employee__section=section).order_by("employee_id").all()]
                try:
                    latitude = [x.answer for x in lat.answer_set.filter(
                        form=form, employee__section=section).order_by("employee_id").all()]
                    longitude = [x.answer for x in lon.answer_set.filter(
                        form=form, employee__section=section).order_by("employee_id").all()]
                except:
                    print("no lat/lon")
                    
            elif company:
                df = pd.DataFrame(list(form.answer_set.filter(question__text=q.text, employee__company=company).values(
                    "answer").order_by("question__id").annotate(nums_of_employess=Count("employee__id"))))
                idlist = [x.employee.employee_id for x in tenant_question.answer_set.filter(
                    form=form, employee__company=company).order_by("employee_id").all()]
                namelist = [x.employee.name for x in tenant_question.answer_set.filter(
                    form=form, employee__company=company).order_by("employee_id").all()]
                try:
                    latitude = [x.answer for x in lat.answer_set.filter(
                        form=form, employee__company=company).order_by("employee_id").all()]
                    longitude = [x.answer for x in lon.answer_set.filter(
                        form=form, employee__company=company).order_by("employee_id").all()]
                except:
                    print("no lat/lon")
            else:
                df = pd.DataFrame(list(form.answer_set.filter(question__text=q.text).values(
                    "answer").order_by("question__id").annotate(nums_of_employess=Count("employee__id"))))
                
        elif tenant.name == "FM" and request.user.role == "dashboard" and request.user.company:            
            df = pd.DataFrame(list(form.answer_set.filter(question__text=q.text,employee__company=request.user.company).values(
                "answer").order_by("question__id").annotate(nums_of_employess=Count("employee__id"))))

            idlist = [x.employee.employee_id for x in tenant_question.answer_set.filter(
                form=form,employee__company=request.user.company).order_by("employee_id").all()]
            namelist = [x.employee.name for x in tenant_question.answer_set.filter(
                form=form,employee__company=request.user.company).order_by("employee_id").all()]
            try:
                latitude = [x.answer for x in lat.answer_set.filter(
                    form=form,employee__company=request.user.company).order_by("employee_id").all()]
                longitude = [x.answer for x in lon.answer_set.filter(
                    form=form,employee__company=request.user.company).order_by("employee_id").all()]
            except:
                print("no lat/lon")
                    
            cords = list(zip(idlist, namelist, latitude, longitude))
            allemp = set(x for x in tenant.employee_set.filter(company=request.user.company).all())
            submited = set(x.employee for x in form.answer_set.filter(employee__company=request.user.company).all())    
            not_submited = allemp.difference(submited) 
        
        else:
            df = pd.DataFrame(list(form.answer_set.filter(question__text=q.text).values(
                "answer").order_by("question__id").annotate(nums_of_employess=Count("employee__id"))))

            idlist = [x.employee.employee_id for x in tenant_question.answer_set.filter(
                form=form).order_by("employee_id").all()]
            namelist = [x.employee.name for x in tenant_question.answer_set.filter(
                form=form).order_by("employee_id").all()]
            try:                
                latitude = [x.answer for x in lat.answer_set.filter(
                    form=form).order_by("employee_id").all()]
                longitude = [x.answer for x in lon.answer_set.filter(
                    form=form).order_by("employee_id").all()]
            except:
                print("no lat/lon")
                    
            cords = list(zip(idlist, namelist, latitude, longitude))

        try:
            for i in cords:
                folium.Marker(location=[i[2], i[3]], popup=f'{i[1]}').add_to(m)
            folium.LayerControl().add_to(m)

        except ValueError:
            print("no cords")
        except TypeError:
            print("no cords")
        m.get_root().height = "500px"

        if len(df) > 0:
            data.append({"question": q.text,"cleanname":filterenglish(q.text), "label": [filterenglish(x) for x in df.answer.values.tolist()], "value": df.nums_of_employess.values.tolist(),"ziped":list(zip([filterenglish(x) for x in df.answer.values.tolist()],df.nums_of_employess.values.tolist()))})

    return render(request, "survey/dashboard.html", {"data": data, "form": form, "emp_pre_comapny": emp_pre_comapny, "map": m._repr_html_(),"submitted":list(submited),"not_submitted":list(not_submited)})


def download(request):
    d = pd.DataFrame(data)
    d.columns = ["Employee Name","Employee ID","Employee Type","Department","Divsion","Email","Position","Phone Number","Section"]
    filename = f"employees{datetime.datetime.now()}.csv"
    export_path = os.path.join(app.root_path,"export")
    fullpath = os.path.join(export_path,filename)        
    d.to_csv(fullpath,index=False)
    # file_path = os.path.join(settings.MEDIA_ROOT, "survey/export")
    # if os.path.exists(file_path):
    #     with open(file_path, 'rb') as fh:
    #         response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
    #         response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
    #         return response
    # raise Http404


def filterenglish(text):
    return re.sub(r'[^\x00-\x7f\W+]', r'', ''.join(filter(str.isalnum, text)))
    