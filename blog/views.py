from django.shortcuts import render,HttpResponse

from django.http import JsonResponse
from django.contrib import auth
from django import forms
from django.forms import widgets


class UserForm(forms.Form):
    user = forms.CharField(max_length=32,widget=widgets.TextInput(attrs={"class":"form-control"}),label="用户名")
    pwd = forms.CharField(max_length=32,widget=widgets.PasswordInput(attrs={"class":"form-control"}),label="密码")
    re_pwd = forms.CharField(max_length=32,widget=widgets.PasswordInput(attrs={"class":"form-control"}),label="确认密码")
    email = forms.EmailField(max_length=32,widget=widgets.EmailInput(attrs={"class":"form-control"}),label="邮箱")


def login(requset):
    if requset.method == "POST":
        response = {"user":None,"msg":None}
        user = requset.POST.get("user")
        pwd = requset.POST.get("pwd")
        valid_code = requset.POST.get("valid_code")

        valid_code_str = requset.session.get("valid_code_str")
        if valid_code.upper() == valid_code_str.upper():
            user = auth.authenticate(username=user,password=pwd)
            if user:
                auth.login(requset,user)
                response["user"]=user.username
            else:
                response["msg"] = "username or password error"
        else:
            response["msg"]="valid code error"

        return JsonResponse(response)
    return render(requset,'login.html')


def get_valid_Code_img(requset):
    """
    基于PIL模块动态生成相应状态码
    :param requset:
    :return:
    """
    from blog.utils.validCode import get_valid_Code_img
    data = get_valid_Code_img(requset)
    return HttpResponse(data)

def index(request):
    return render(request,"index.html")

def register(request):
    form = UserForm
    return render(request,"register.html",locals())