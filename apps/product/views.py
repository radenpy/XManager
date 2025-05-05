from django.shortcuts import render
from .forms import ProductForm, RawProductForm

from .models import Product


# def product_create_view(request):
#     my_form = RawProductForm()
#     if request.method == "POST":
#         my_form = RawProductForm(request.POST)
#         if my_form.is_valid():
#             print(my_form.cleaned_data)
#             Product.objects.create(my_form.cleaned_data)
#         else:
#             print(my_form.errors)
#     context = {
#         "form": my_form
#     }
#     return render(request, "product-create.html", context)


# def product_create_view(request):
#     if request.method == "POST":
#         my_new_title = request.POST.get('name')
#         print(my_new_title)

#     context = {}
#     return render(request, "product-create.html", context)

def product_create_view(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        form = ProductForm()

    context = {
        'form': form
    }

    return render(request, "product-create.html", context)


def product_list(request):
    return render(request, 'product-list.html')
