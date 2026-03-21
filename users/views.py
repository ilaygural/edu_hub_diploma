from django.http import HttpResponse


# Create your views here.
def login_user(request):
    return HttpResponse("login")


def logout_user(request):
    return HttpResponse("logout")