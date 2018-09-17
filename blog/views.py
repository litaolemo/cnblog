from django.shortcuts import render, HttpResponse,redirect
from blog.models import UserInfo
from django.http import JsonResponse
from django.contrib import auth
from blog.Myforms import UserForm



def login(requset):
    if requset.method == "POST":
        response = {"user": None, "msg": None}
        user = requset.POST.get ("user")
        pwd = requset.POST.get ("pwd")
        valid_code = requset.POST.get ("valid_code")

        valid_code_str = requset.session.get ("valid_code_str")
        if valid_code.upper() == valid_code_str.upper ():
            user = auth.authenticate (username=user, password=pwd)
            if user:
                auth.login(requset, user)
                response["user"] = user.username
            else:
                response["msg"] = "username or password error"
        else:
            response["msg"] = "valid code error"

        return JsonResponse (response)
    return render (requset, 'login.html')


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
    return render(request, "index.html")


def register(request):
    if request.is_ajax():
        # print (request.POST)
        form = UserForm(request.POST)
        response = {"user": None, 'msg': None}
        if form.is_valid():
            response["user"] = form.cleaned_data.get("user")
            user = form.cleaned_data.get("user")
            pwd = form.cleaned_data.get("pwd")
            email = form.cleaned_data.get("email")
            file_obj = request.FILES.get("avatar")
            extra = {}
            if file_obj:
                extra["avatar"] = file_obj
            user_obj = UserInfo.objects.create_user(username=user, password=pwd, email=email, avatar=file_obj, **extra)

        else:
            print(form.cleaned_data)
            print(form.error_class)
            response["msg"] = form.errors
        return JsonResponse (response)
    form = UserForm
    return render(request, "register.html", locals())


def logout(request):
    auth.logout(request)
    #request.session.flush()
    return redirect("/index/")