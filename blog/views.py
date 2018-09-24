from django.shortcuts import render, HttpResponse,redirect
from blog.models import *
from django.http import JsonResponse
from django.contrib import auth
from blog.Myforms import UserForm
from django.db.models import Count
import json
from django.db.models import F
from django.contrib.auth.decorators import login_required
import os
from cnblog import settings
from django.db import transaction

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
    article_list = Article.objects.all()
    return render(request, "index.html",locals())


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
            user_obj = UserInfo.objects.create_user(username=user, password=pwd, email=email, **extra)

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

def home_site(request,username,**kwargs):
    """
    个人站点视图函数
    :param requset:
    :return:
    """
    # print(username)
    user = UserInfo.objects.filter(username=username).first()
    if not user:
        return render(request,"not_found.html")
    # 查询当前站点对象
    blog = user.blog
    # 当前用户或站点对应的所有文章
    #article_list = user.article_set.all()
    article_list = Article.objects.filter(user=user)
    if kwargs:
        condition = kwargs.get("condition")
        param = kwargs.get("param")  # 2012-12

        if condition == "category":
            article_list = article_list.filter(category__title=param)
        elif condition == "tag":
            article_list = article_list.filter(tags__title=param)
        else:
            year, month = param.split("/")
            article_list = article_list.filter(create_time__year=year, create_time__month=month)

    # 每一个后的表模型.objects.values("pk").annotate(聚合函数(关联表__统计字段)).values("表模型的所有字段以及统计字段")

    # 查询每一个分类名称以及对应的文章数

    # ret=Category.objects.values("pk").annotate(c=Count("article__title")).values("title","c")
    # print(ret)

    # 查询当前站点的每一个分类名称以及对应的文章数

    # cate_list=Category.objects.filter(blog=blog).values("pk").annotate(c=Count("article__title")).values_list("title","c")
    # print(cate_list)

    # 查询当前站点的每一个标签名称以及对应的文章数

    # tag_list=Tag.objects.filter(blog=blog).values("pk").annotate(c=Count("article")).values_list("title","c")
    # print(tag_list)

    # 查询当前站点每一个年月的名称以及对应的文章数

    # ret=Article.objects.extra(select={"is_recent":"create_time > '2018-09-05'"}).values("title","is_recent")
    # print(ret)

    # 方式1:
    # date_list=Article.objects.filter(user=user).extra(select={"y_m_date":"date_format(create_time,'%%Y/%%m')"}).values("y_m_date").annotate(c=Count("nid")).values_list("y_m_date","c")
    # print(date_list)

    # 方式2:

    # from django.db.models.functions import TruncMonth
    #
    # ret=Article.objects.filter(user=user).annotate(month=TruncMonth("create_time")).values("month").annotate(c=Count("nid")).values_list("month","c")
    # print("ret----->",ret)
    print(user)
    return render(request, "home_site.html", locals())


def get_classification_data(username):
    user = UserInfo.objects.filter(username=username).first()
    blog = user.blog

    cate_list = Category.objects.filter(blog=blog).values("pk").annotate(c=Count("article__title")).values_list(
        "title", "c")

    tag_list = Tag.objects.filter(blog=blog).values("pk").annotate(c=Count("article")).values_list("title", "c")

    date_list = Article.objects.filter(user=user).extra(
        select={"y_m_date": "date_format(create_time,'%%Y/%%m')"}).values("y_m_date").annotate(
        c=Count("nid")).values_list("y_m_date", "c")

    return {"blog": blog, "cate_list": cate_list, "date_list": date_list, "tag_list": tag_list}

def article_detail(request, username, article_id):
    """
    文章详情页
    :param request:
    :param username:
    :param article_id:
    :return:
    """
    user = UserInfo.objects.filter(username=username).first()
    blog = user.blog
    article_obj = Article.objects.filter(pk=article_id).first()

    comment_list = Comment.objects.filter(article_id=article_id)

    return render(request, "article_detail.html", locals())


def digg(request):
    """
    点赞功能
    :param request:
    :return:
    """
    print(request.POST)

    article_id = request.POST.get("article_id")
    is_up = json.loads(request.POST.get("is_up"))  # "true"
    # 点赞人即当前登录人
    user_id = request.user.pk
    obj = ArticleUpDown.objects.filter(user_id=user_id, article_id=article_id).first()

    response = {"state": True}
    if not obj:
        ard = ArticleUpDown.objects.create(user_id=user_id, article_id=article_id, is_up=is_up)

        queryset = Article.objects.filter(pk=article_id)
        if is_up:
            queryset.update(up_count=F("up_count") + 1)
        else:
            queryset.update(down_count=F("down_count") + 1)
    else:
        response["state"] = False
        response["handled"] = obj.is_up

    return JsonResponse(response)

def digg(request):
    """
    点赞功能
    :param request:
    :return:
    """
    print(request.POST)

    article_id = request.POST.get("article_id")
    is_up = json.loads(request.POST.get("is_up"))  # "true"
    # 点赞人即当前登录人
    user_id = request.user.pk
    obj = ArticleUpDown.objects.filter(user_id=user_id, article_id=article_id).first()

    response = {"state": True}
    if not obj:
        ard = ArticleUpDown.objects.create(user_id=user_id, article_id=article_id, is_up=is_up)

        queryset = Article.objects.filter(pk=article_id)
        if is_up:
            queryset.update(up_count=F("up_count") + 1)
        else:
            queryset.update(down_count=F("down_count") + 1)
    else:
        response["state"] = False
        response["handled"] = obj.is_up

    return JsonResponse(response)


def comment(request):
    """
    提交评论视图函数
    功能:
    1 保存评论
    2 创建事务
    3 发送邮件
    :param request:
    :return:
    """
    print(request.POST)

    article_id = request.POST.get("article_id")
    pid = request.POST.get("pid")
    content = request.POST.get("content")
    user_id = request.user.pk

    article_obj = Article.objects.filter(pk=article_id).first()

    # 事务操作
    with transaction.atomic():
        comment_obj = Comment.objects.create(user_id=user_id, article_id=article_id, content=content,
                                                    parent_comment_id=pid)
        Article.objects.filter(pk=article_id).update(comment_count=F("comment_count") + 1)

    response = {}

    response["create_time"] = comment_obj.create_time.strftime("%Y-%m-%d %X")
    response["username"] = request.user.username
    response["content"] = content

    # 发送邮件

    from django.core.mail import send_mail
    from cnblog import settings

    # send_mail(
    #     "您的文章%s新增了一条评论内容"%article_obj.title,
    #     content,
    #     settings.EMAIL_HOST_USER,
    #     ["916852314@qq.com"]
    # )

    import threading
    """t = threading.Thread(target=send_mail, args=("您的文章%s新增了一条评论内容" % article_obj.title,
                                                 content,
                                                 settings.EMAIL_HOST_USER,
                                                 ["916852314@qq.com"])
                         )
    t.start()
    """
    return JsonResponse(response)


def get_comment_tree(request):
    article_id = request.GET.get("article_id")
    response = list(Comment.objects.filter(article_id=article_id).order_by("pk").values("pk", "content",
                                                                                               "parent_comment_id"))

    return JsonResponse(response, safe=False)


@login_required
def cn_backend(request):
    """
    后台管理的首页
    :param request:
    :return:
    """
    article_list = Article.objects.filter(user=request.user)

    return render(request, "backend/backend.html", locals())


from bs4 import BeautifulSoup


@login_required
def add_article(request):
    """
    后台管理的添加书籍视图函数
    :param request:
    :return:
    """
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")

        # 防止xss攻击,过滤script标签
        soup=BeautifulSoup(content,"html.parser")
        for tag in soup.find_all():

            print(tag.name)
            if tag.name=="script":
                tag.decompose()

        # 构建摘要数据,获取标签字符串的文本前150个符号

        desc=soup.text[0:150]+"..."

        Article.objects.create(title=title,desc=desc,content=str(soup), user=request.user)
        return redirect("/cn_backend/")

    return render(request, "backend/add_article.html")


def upload(request):
    """
    编辑器上传文件接受视图函数
    :param request:
    :return:
    """

    print(request.FILES)
    img_obj=request.FILES.get("upload_img")
    print(img_obj.name)

    path=os.path.join(settings.MEDIA_ROOT,"add_article_img",img_obj.name)

    with open(path,"wb") as f:

        for line in img_obj:
            f.write(line)
    response={
        "error":0,
        "url":"/media/add_article_img/%s"%img_obj.name
    }
    import json
    return HttpResponse(json.dumps(response))
