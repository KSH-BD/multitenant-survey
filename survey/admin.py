from django.contrib import admin
from survey import models


admin.site.register(
    [models.Tenant,models.Week,models.Form, models.Question, models.Answer,models.QuestionOption,models.Section,models.Division,models.Department,models.Company,models.JobTitle,models.AuthUser,models.CompanyJson])

