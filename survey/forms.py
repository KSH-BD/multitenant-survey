from django import forms
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from .models import Employee, Tenant, Week, Form, Question, QuestionOption, Answer, TYPE_CHOICES, Section, Division, Department, Company, JobTitle, AuthUser


class FormForm(forms.Form):

    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_item = []
        self.id = id
        self.form = Form.objects.get(id=self.id)

        q = self.form.tenant.question_set.filter(~Q(text="Any Other Note - اي ملاحظات اخري ?")).all()
        other_notes = self.form.tenant.question_set.filter(text="Any Other Note - اي ملاحظات اخري ?").first()
        for i in q:
            field_name = f'{i.text.replace(" ", "_").replace("?","")}'

            if i.type == "Text":
                if field_name in ["Longitude","Latitude"]:
                    if self.form.tenant.has_cords:
                        self.fields[field_name] = forms.CharField(
                            label=i.text, required=i.required)
                        self.fields[field_name].widget.attrs.update(
                            {"data-id": i.id, "readonly": "readonly"})
                else:
                    self.fields[field_name] = forms.CharField(
                        label=i.text, required=i.required)
                    self.fields[field_name].widget.attrs.update(
                        {"data-id": i.id})

            if i.type == "TextArea":
                self.fields[field_name] = forms.CharField(
                    label=i.text, required=i.required, widget=forms.Textarea)
                self.fields[field_name].widget.attrs.update({"data-id": i.id,"rows":2})

            elif i.type == "Email":
                self.fields[field_name] = forms.EmailField(
                    label=i.text, required=i.required)
                self.fields[field_name].widget.attrs.update({"data-id": i.id})

            elif i.type == "Number":
                self.fields[field_name] = forms.IntegerField(
                    label=i.text, required=i.required)
                self.fields[field_name].widget.attrs.update(
                    {"data-id": i.id})

            elif i.type == "List":                
                if i.questionoption_set.all():
                    if self.form.tenant.name == "FM" and field_name in ["Current_Zone_-_الزون_الحالي_","Company_-_الشركة_"]:
                        self.fields[field_name] = forms.CharField(label=i.text, required=i.required)
                        self.fields[field_name].widget.attrs.update({"data-id": i.id, "readonly": "readonly"})
                    else:
                        self.fields[field_name] = forms.ModelChoiceField(
                            queryset=i.questionoption_set.all(), label=i.text, required=i.required)
                        self.fields[field_name].widget.attrs.update(
                            {"data-id": i.id})
                        self.fields[field_name].widget.attrs['class'] = "ui dropdown"

            elif i.type == "Radio":
                if i.questionoption_set.all():
                    self.fields[field_name] = forms.ModelChoiceField(
                        queryset=i.questionoption_set.all(), label=i.text, required=i.required, widget=forms.RadioSelect)
                    self.fields[field_name].widget.attrs['class'] = "ui radio"
                    self.fields[field_name].widget.attrs.update(
                        {"data-id": i.id})
        if other_notes:      
            field_name = f'{other_notes.text.replace(" ", "_").replace("?","")}'
            self.fields[field_name] = forms.CharField(
                label=other_notes.text, required=other_notes.required, widget=forms.Textarea)
            self.fields[field_name].widget.attrs.update({"data-id": other_notes.id})
        
    def initialFormFields(self, employee):
        if self.form.tenant.form_set.count() < 2:
            return

        for i in Question.objects.filter(tenant=self.form.tenant).all():

            answer = i.answer_set.filter(
                employee=employee).order_by("-created_at").first()

            field_name = f'{i.text.replace(" ", "_").replace("?","")}'

            # if field_name == "Longitude" or field_name == "Latitude":
            #     if self.form.tenant.has_cords:
            #         self.initial[field_name] = forms.IntegerField(widget = forms.HiddenInput(),required=True)
            #     else:
            #         self.initial[field_name] = forms.IntegerField(label='',widget = forms.HiddenInput(),required=False)

            if answer:
                if i.type == "List" or i.type == "Radio":
                    # print(QuestionOption.objects.get(value=answer.answer))
                    self.initial[field_name] = QuestionOption.objects.filter(
                        value=answer.answer, question=i).first()
                else:
                    self.initial[field_name] = answer


class EmployeeForm(forms.ModelForm):
    tenant = forms.ModelChoiceField(label='', queryset=Tenant.objects.all(
    ), widget=forms.HiddenInput(), required=False)
    section = forms.ModelChoiceField(label='Section', queryset=Section.objects.all(
    ), widget=forms.Select(attrs={'class': 'ui dropdown'}), required=False)
    division = forms.ModelChoiceField(label='Division', queryset=Division.objects.all(
    ), widget=forms.Select(attrs={'class': 'ui dropdown'}), required=False)
    department = forms.ModelChoiceField(label='Department', queryset=Department.objects.all(
    ), widget=forms.Select(attrs={'class': 'ui dropdown'}), required=False)
    company = forms.ModelChoiceField(label='Company', queryset=Company.objects.all(
    ), widget=forms.Select(attrs={'class': 'ui dropdown'}), required=False)
    job_title = forms.ModelChoiceField(label='Job Title', queryset=JobTitle.objects.all(
    ), widget=forms.Select(attrs={'class': 'ui dropdown'}), required=False)

    class Meta:
        model = Employee
        fields = '__all__'
        widgets = {
            'emergency_number': forms.DateInput(attrs={'required': False}),
            'emergency_email': forms.DateInput(attrs={'required': False}),
            'job_type': forms.DateInput(attrs={'required': False}),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    tenant = forms.ModelChoiceField(label='', queryset=Tenant.objects.all(
    ), widget=forms.HiddenInput(), required=True)

    class Meta:
        model = AuthUser
        fields = ["username", "email", "password1", "password2","role","company", "tenant"]


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    tenant = forms.ModelChoiceField(label='', queryset=Tenant.objects.all(
    ), widget=forms.HiddenInput(), required=True)

    class Meta:
        model = AuthUser
        fields = ["username", "email","role","company", "tenant"]

# class RegisterForm(forms.ModelForm):
#     tenant = forms.ModelChoiceField(label='',queryset=Tenant.objects.all(),required=True)
#     class Meta:
#         model = AuthUser
#         fields = ['username','password','tenant']


class LoginForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = AuthUser
        fields = ['username', 'password']


class TenantForm(forms.ModelForm):    
    has_cords = forms.BooleanField(label= "", required=False, widget=forms.HiddenInput())
    class Meta:
        model = Tenant
        fields = '__all__'


class WeekForm(forms.ModelForm):
    tenant = forms.ModelChoiceField(label='', queryset=Tenant.objects.all(
    ), widget=forms.HiddenInput(), required=False)
    number = forms.CharField(
        label='Number', widget=forms.TextInput(attrs={'type': 'number'}))

    class Meta:
        model = Week
        fields = '__all__'

class QuestionForm(forms.Form):
    # tenant = forms.CharField(label="Tenant",required=True)
    text = forms.CharField(label="Text", required=True)
    datatype = forms.ChoiceField(
        label="Type", choices=TYPE_CHOICES, required=False)
    required = forms.ChoiceField(label="Required", choices=[(
        "Yes", "Yes"), ("NO", "NO")], initial="NO", required=False)
    dashboard = forms.ChoiceField(label="Dashboard", choices=[(
        "Yes", "Yes"), ("NO", "NO")], initial="NO", required=False)    


class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = '__all__'


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = '__all__'
 
class SectionSelectForm(forms.Form):
    section = forms.ModelChoiceField(label='Section',queryset=Section.objects.all())
                                           
    
class SectionForm(forms.ModelForm):
    tenant = forms.ModelChoiceField(
        label='', queryset=Tenant.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Section
        fields = ['name', 'tenant']


class DivisionForm(forms.ModelForm):
    tenant = forms.ModelChoiceField(
        label='', queryset=Tenant.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Division
        fields = ['name', 'tenant']


class DepartmentForm(forms.ModelForm):
    tenant = forms.ModelChoiceField(
        label='', queryset=Tenant.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Department
        fields = ['name', 'tenant']


class CompanyForm(forms.ModelForm):
    tenant = forms.ModelChoiceField(
        label='', queryset=Tenant.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Company
        fields = ['name', 'tenant']


class JobTitleForm(forms.ModelForm):
    tenant = forms.ModelChoiceField(
        label='', queryset=Tenant.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = JobTitle
        fields = ['name', 'tenant']
