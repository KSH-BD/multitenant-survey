import functools
from django.shortcuts import render, redirect
from survey.models import Tenant

def unauthenticated_users(method):
    @functools.wraps(method)
    def wrapper(request, *args, **kwargs):   
        if request.user.username == "admin":
            return method(request, *args, **kwargs)
             
        if request.user.tenant.id != int(kwargs.get("id")):
            return redirect("tenant_details", id=request.user.tenant.id)  
        
        if request.user.role == "dashboard" and method.__name__ not in ["dashboard_list","tenant_details","dashboard"]:
            return redirect("tenant_details", id=request.user.tenant.id)  
            
        return method(request, *args, **kwargs)
    return wrapper

def adminonly(method):
    @functools.wraps(method)
    def wrapper(request, *args, **kwargs):   
        if request.user.username == "admin":
            return method(request, *args, **kwargs)
                     
        if request.user.role != "admin":
            return redirect("tenant_details", id=request.user.tenant.id)       
        else:
            return method(request, *args, **kwargs)
    return wrapper