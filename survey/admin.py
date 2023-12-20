from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from survey import models

class EmployeeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    ...


admin.site.register(models.Employee,EmployeeAdmin)
admin.site.register(
    [models.Tenant,models.Week,models.Form, models.Question, models.Answer,models.QuestionOption,models.Section,models.Division,models.Department,models.Company,models.JobTitle,models.AuthUser,models.CompanyJson])

