from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def rdio(request):
    return render(request,'rdio/hello.html')

def test(request):
    return render(request,'rdio/test.html')
    
