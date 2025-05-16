# Importy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib.messages.views import SuccessMessageMixin

from .models import Product, ProductCategory, Brand, ProductImage
from .forms import ProductForm, ProductCategoryForm, BrandForm

# Widoki dla produktów


class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.all()
        context['brands'] = Brand.objects.all()

        # Dodaj domyślny rozmiar strony i inne zmienne używane w szablonie
        context['default_page_size'] = self.paginate_by

        # Zmienne dla aktywnych filtrów
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_categories'] = self.request.GET.getlist(
            'category', [])
        context['selected_brands'] = self.request.GET.getlist('brand', [])
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_featured'] = self.request.GET.get('featured', '')
        context['selected_page_size'] = self.request.GET.get(
            'page_size', str(self.paginate_by))

        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrowanie po kategorii
        category_slugs = self.request.GET.getlist('category')
        if category_slugs:
            queryset = queryset.filter(category__slug__in=category_slugs)

        # Filtrowanie po marce
        brand_slugs = self.request.GET.getlist('brand')
        if brand_slugs:
            queryset = queryset.filter(brand__slug__in=brand_slugs)

        # Filtrowanie po statusie aktywności
        status = self.request.GET.get('status')
        if status == '1':
            queryset = queryset.filter(is_active=True)
        elif status == '0':
            queryset = queryset.filter(is_active=False)

        # Filtrowanie po statusie wyróżnienia
        featured = self.request.GET.get('featured')
        if featured == '1':
            queryset = queryset.filter(is_featured=True)
        elif featured == '0':
            queryset = queryset.filter(is_featured=False)

        # Wyszukiwanie
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(ean__icontains=search_query) |
                Q(altum_id__icontains=search_query)
            )

        # Ustaw rozmiar strony (paginacja)
        page_size = self.request.GET.get('page_size')
        if page_size:
            self.paginate_by = int(page_size)

        return queryset


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = self.object.images.all().order_by('order',
                                                              '-is_primary')
        return context


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_create_update.html'
    success_url = reverse_lazy('product:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj nowy produkt'
        context['action'] = 'Dodaj'

        # Dodaj hierarchiczne kategorie do szablonu
        context['hierarchical_categories'] = self.get_hierarchical_categories()

        return context

    def get_hierarchical_categories(self):
        """
        Zwraca listę obiektów kategorii z dodanym atrybutem level
        określającym poziom zagnieżdżenia.
        """
        # Pobierz kategorie główne (bez rodzica)
        root_categories = ProductCategory.objects.filter(
            parent=None).order_by('name')

        # Lista wynikowa
        result = []

        # Rekurencyjnie dodaj kategorie i ich dzieci
        for category in root_categories:
            # Zamiast tworzyć słownik, dodaj atrybut level do obiektu kategorii
            category.level = 0
            result.append(category)

            # Rekurencyjnie dodaj dzieci
            self._add_subcategories(category, result, 1)

        return result

    def _add_subcategories(self, parent, result_list, level):
        """
        Rekurencyjnie dodaje podkategorie do listy wynikowej,
        ustawiając odpowiedni poziom zagnieżdżenia.
        """
        children = parent.children.all().order_by('name')
        for child in children:
            # Zamiast tworzyć słownik, dodaj atrybut level do obiektu kategorii
            child.level = level
            result_list.append(child)

            # Rekurencyjnie dodaj dzieci
            self._add_subcategories(child, result_list, level + 1)

    def form_valid(self, form):
        messages.success(self.request, "Produkt został pomyślnie utworzony.")
        return super().form_valid(form)


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_create_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj produkt: {self.object.name}'
        context['action'] = 'Zapisz zmiany'
        context['images'] = self.object.images.all().order_by('order',
                                                              '-is_primary')

        # Dodaj hierarchiczne kategorie do szablonu
        context['hierarchical_categories'] = self.get_hierarchical_categories()

        return context

    def get_hierarchical_categories(self):
        """
        Zwraca listę obiektów kategorii z dodanym atrybutem level
        określającym poziom zagnieżdżenia.
        """
        # Pobierz kategorie główne (bez rodzica)
        root_categories = ProductCategory.objects.filter(
            parent=None).order_by('name')

        # Lista wynikowa
        result = []

        # Rekurencyjnie dodaj kategorie i ich dzieci
        for category in root_categories:
            # Zamiast tworzyć słownik, dodaj atrybut level do obiektu kategorii
            category.level = 0
            result.append(category)

            # Rekurencyjnie dodaj dzieci
            self._add_subcategories(category, result, 1)

        return result

    def _add_subcategories(self, parent, result_list, level):
        """
        Rekurencyjnie dodaje podkategorie do listy wynikowej,
        ustawiając odpowiedni poziom zagnieżdżenia.
        """
        children = parent.children.all().order_by('name')
        for child in children:
            # Zamiast tworzyć słownik, dodaj atrybut level do obiektu kategorii
            child.level = level
            result_list.append(child)

            # Rekurencyjnie dodaj dzieci
            self._add_subcategories(child, result_list, level + 1)

    def form_valid(self, form):
        messages.success(
            self.request, "Produkt został pomyślnie zaktualizowany.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('product:product_detail', kwargs={'pk': self.object.pk})


class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product/product_confirm_delete.html'
    success_url = reverse_lazy('product:product_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Produkt został pomyślnie usunięty.")
        return super().delete(request, *args, **kwargs)


# Widoki dla kategorii
class CategoryListView(ListView):
    model = ProductCategory
    context_object_name = 'categories'
    template_name = 'product/category_list.html'

    def get_queryset(self):
        """
        Pobierz wszystkie kategorie i posortuj je tak, aby kategorie nadrzędne 
        były przed ich dziećmi.
        """
        # Najpierw pobierz kategorie główne
        root_categories = list(ProductCategory.objects.filter(
            parent=None).order_by('name'))

        # Następnie dodaj wszystkie dzieci w odpowiedniej kolejności
        ordered_categories = []

        for root_category in root_categories:
            ordered_categories.append(root_category)
            # Dodaj wszystkie podkategorie
            self._add_subcategories(root_category, ordered_categories)

        return ordered_categories

    def _add_subcategories(self, parent_category, categories_list):
        """
        Rekurencyjnie dodaje podkategorie do listy.
        """
        children = parent_category.children.all().order_by('name')
        for child in children:
            categories_list.append(child)
            self._add_subcategories(child, categories_list)


class CategoryCreateView(SuccessMessageMixin, CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'product/category_create_update.html'
    success_url = reverse_lazy('product:category_list')
    success_message = "Kategoria %(name)s została pomyślnie utworzona."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj nową kategorię'
        context['action'] = 'Dodaj'
        return context


class CategoryUpdateView(SuccessMessageMixin, UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'product/category_create_update.html'
    success_url = reverse_lazy('product:category_list')
    success_message = "Kategoria %(name)s została pomyślnie zaktualizowana."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj kategorię: {self.object.name}'
        context['action'] = 'Zapisz zmiany'
        return context


class CategoryDeleteView(DeleteView):
    model = ProductCategory
    template_name = 'product/category_confirm_delete.html'
    success_url = reverse_lazy('product:category_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Kategoria została pomyślnie usunięta.")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sprawdź, czy kategoria ma produkty lub podkategorie
        context['products_count'] = self.object.products.count(
        ) if hasattr(self.object, 'products') else 0
        context['subcategories_count'] = self.object.children.count(
        ) if hasattr(self.object, 'children') else 0
        return context


# Widoki dla marek
class BrandListView(ListView):
    model = Brand
    context_object_name = 'brands'
    template_name = 'product/brand_list.html'

    def get_queryset(self):
        return Brand.objects.all().order_by('name')


class BrandCreateView(SuccessMessageMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'product/brand_create_update.html'
    success_url = reverse_lazy('product:brand_list')
    success_message = "Marka %(name)s została pomyślnie utworzona."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj nową markę'
        context['action'] = 'Dodaj'
        return context


class BrandUpdateView(SuccessMessageMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'product/brand_create_update.html'
    success_url = reverse_lazy('product:brand_list')
    success_message = "Marka %(name)s została pomyślnie zaktualizowana."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj markę: {self.object.name}'
        context['action'] = 'Zapisz zmiany'
        return context


class BrandDeleteView(DeleteView):
    model = Brand
    template_name = 'product/brand_confirm_delete.html'
    success_url = reverse_lazy('product:brand_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Marka została pomyślnie usunięta.")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sprawdź, czy marka ma produkty
        context['products_count'] = self.object.products.count(
        ) if hasattr(self.object, 'products') else 0
        return context


@require_POST
def product_bulk_action(request):
    """Widok do obsługi masowych akcji na produktach"""
    product_ids = request.POST.getlist('product_ids')
    bulk_action = request.POST.get('bulk_action')

    if not product_ids:
        messages.error(request, "Nie wybrano żadnych produktów.")
        return redirect('product:product_list')

    # Pobierz produkty
    products = Product.objects.filter(id__in=product_ids)

    # Wykonaj odpowiednią akcję
    if bulk_action == 'delete':
        # Opcjonalnie: dodatkowe sprawdzenie potwierdzenia
        if request.POST.get('confirm_delete') == 'yes':
            count = products.count()
            products.delete()
            messages.success(request, f"Pomyślnie usunięto {count} produktów.")

    elif bulk_action == 'status_active':
        products.update(is_active=True)
        messages.success(
            request, f"Pomyślnie zaktualizowano status {len(product_ids)} produktów na 'Aktywny'.")

    elif bulk_action == 'status_inactive':
        products.update(is_active=False)
        messages.success(
            request, f"Pomyślnie zaktualizowano status {len(product_ids)} produktów na 'Nieaktywny'.")

    elif bulk_action == 'featured_yes':
        products.update(is_featured=True)
        messages.success(
            request, f"Pomyślnie oznaczono {len(product_ids)} produktów jako 'Wyróżnione'.")

    elif bulk_action == 'featured_no':
        products.update(is_featured=False)
        messages.success(
            request, f"Pomyślnie usunięto oznaczenie 'Wyróżnione' dla {len(product_ids)} produktów.")

    elif bulk_action == 'set_category':
        category_ids = request.POST.getlist('category_ids')
        if category_ids:
            category = ProductCategory.objects.filter(
                id=category_ids[0]).first()
            if category:
                products.update(category=category)
                messages.success(
                    request, f"Pomyślnie ustawiono kategorię '{category.name}' dla {len(product_ids)} produktów.")
            else:
                messages.error(request, "Wybrana kategoria nie istnieje.")
        else:
            messages.error(request, "Nie wybrano żadnej kategorii.")

    elif bulk_action == 'set_brand':
        brand_ids = request.POST.getlist('brand_ids')
        if brand_ids:
            brand = Brand.objects.filter(id=brand_ids[0]).first()
            if brand:
                products.update(brand=brand)
                messages.success(
                    request, f"Pomyślnie ustawiono markę '{brand.name}' dla {len(product_ids)} produktów.")
            else:
                messages.error(request, "Wybrana marka nie istnieje.")
        else:
            messages.error(request, "Nie wybrano żadnej marki.")

    return redirect('product:product_list')


@require_POST
def product_bulk_edit(request):
    """Widok do obsługi masowej edycji produktów"""
    selected_ids = request.POST.get('selected_ids', '')

    if not selected_ids:
        messages.error(request, "Nie wybrano żadnych produktów do edycji.")
        return redirect('product:product_list')

    # Tutaj możesz przekierować do specjalnego formularza edycji zbiorczej
    # lub zaimplementować logikę edycji zbiorczej

    # Na razie przekierujmy z powrotem do listy z komunikatem
    messages.info(
        request, "Funkcja masowej edycji jeszcze nie została zaimplementowana.")
    return redirect('product:product_list')
