from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, FormView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.subscriber import views
from django.db import models
from apps.partner.models import Partner, PartnerEmail


from .models import Subscriber, SubscriberGroup
from .forms import SubscriberForm, SubscriberGroupForm

# At the top of your views.py file
DEFAULT_PAGE_SIZE = 100

# Subscriber views


# class SubscriberListView(LoginRequiredMixin, ListView):
#     """Lista subskrybentów"""
#     model = Subscriber
#     template_name = 'subscriber/subscriber_list.html'
#     context_object_name = 'subscribers'
#     paginate_by = 20

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         search_query = self.request.GET.get('search', '')
#         consent = self.request.GET.get('consent', '')
#         first_name = self.request.GET.get('first_name', '')
#         last_name = self.request.GET.get('last_name', '')
#         common_name = self.request.GET.get('common_name', '')
#         partnered_with_name = self.request.GET.get('name')
#         partnered_with_vat = self.request.GET.get('vat_number')

#         if search_query:
#             queryset = queryset.filter(
#                 models.Q(email__icontains=search_query) |
#                 models.Q(first_name__icontains=search_query) |
#                 models.Q(last_name__icontains=search_query) |
#                 models.Q(common_name__icontains=search_query) |
#                 models.Q(partnered_with__name__icontains=search_query) |
#                 models.Q(group_affiliation__group_name__icontains=search_query) |
#                 models.Q(partnered_with__vat_number__icontains=search_query)
#             )

#         if consent != '':
#             queryset = queryset.filter(newsletter_consent=(consent == '1'))

#         if first_name:
#             queryset = queryset.filter(first_name__icontains=first_name)

#         if last_name:
#             queryset = queryset.filter(last_name__icontains=last_name)

#         if common_name:
#             queryset = queryset.filter(common_name__icontains=common_name)

#         if partnered_with_name:
#             queryset = queryset.filter(
#                 partnered_with_name__icontains=partnered_with_name)

#         if partnered_with_vat:
#             queryset = queryset.filter(
#                 partnered_with_vat__icontains=partnered_with_vat)

#         return queryset.distinct()

#     def get_context_data(self, **kwargs):
#         """Dodatkowe dane kontekstowe"""
#         context = super().get_context_data(**kwargs)
#         context['search_query'] = self.request.GET.get('search', '')
#         context['common_name_query'] = self.request.GET.get(
#             'common_name', '')  # Dodane dla formularza filtrowania
#         context['first_name_query'] = self.request.GET.get(
#             'first_name', '')   # Dodane dla spójności
#         context['last_name_query'] = self.request.GET.get(
#             'last_name', '')     # Dodane dla spójności
#         context['subscriber_groups'] = SubscriberGroup.objects.all().order_by(
#             'group_name')
#         context['all_partners'] = Partner.objects.all().order_by('name')
#         return context

#     def get_paginate_by(self, queryset):
#         page_size = self.request.GET.get('page_size', self.paginate_by)
#         try:
#             return int(page_size)
#         except ValueError:
#             return self.paginate_by

class SubscriberListView(LoginRequiredMixin, ListView):
    """Lista subskrybentów"""
    model = Subscriber
    template_name = 'subscriber/subscriber_list.html'
    context_object_name = 'subscribers'
    paginate_by = DEFAULT_PAGE_SIZE

    # def get_paginate_by(self, queryset):
    #     """Get the number of items to paginate by, or use default"""
    #     page_size = self.request.GET.get('page_size', self.paginate_by)
    #     return int(page_size) if page_size.isdigit() else self.paginate_by
    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size', str(DEFAULT_PAGE_SIZE))
        try:
            return int(page_size)
        except ValueError:
            return DEFAULT_PAGE_SIZE

    def get_queryset(self):
        """Filtrowanie wyników"""
        queryset = super().get_queryset()

        # Get filter parameters
        search_query = self.request.GET.get('search', '')
        group_id = self.request.GET.get('group', '')
        partner_id = self.request.GET.get('partner', '')
        consent = self.request.GET.get('consent', '')

        # Apply search filter
        if search_query:
            queryset = queryset.filter(
                models.Q(email__icontains=search_query) |
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query) |
                models.Q(common_name__icontains=search_query) |
                models.Q(partnered_with__name__icontains=search_query) |
                models.Q(group_affiliation__group_name__icontains=search_query) |
                models.Q(partnered_with__vat_number__icontains=search_query)
            )

        # Apply group filter
        if group_id:
            queryset = queryset.filter(group_affiliation__id=group_id)

        # Apply partner filter
        if partner_id:
            queryset = queryset.filter(partnered_with__id=partner_id)

        # Apply consent filter
        if consent in ['0', '1']:
            queryset = queryset.filter(newsletter_consent=(consent == '1'))

        # Return distinct results to avoid duplicates due to joins
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        """Dodatkowe dane kontekstowe"""
        context = super().get_context_data(**kwargs)
        # Pass the default page size to the template
        context['default_page_size'] = str(DEFAULT_PAGE_SIZE)
        context['selected_page_size'] = self.request.GET.get(
            'page_size', str(DEFAULT_PAGE_SIZE))
        # Rest of your code...

        # Add filter values to context
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_groups'] = self.request.GET.getlist('group', [])
        context['selected_partners'] = self.request.GET.getlist('partner', [])
        context['selected_consent'] = self.request.GET.get('consent', '')
        context['selected_page_size'] = self.request.GET.get(
            'page_size', str(DEFAULT_PAGE_SIZE))

        # Add flag to indicate if there are any active filters
        context['has_active_filters'] = bool(
            context['search_query'] or
            context['selected_groups'] or
            context['selected_partners'] or
            context['selected_consent'] != '' or
            (context['selected_page_size'] !=
             '20' and context['selected_page_size'])

        )

        # Add all groups and partners for filters
        context['subscriber_groups'] = SubscriberGroup.objects.all().order_by(
            'group_name')

        # Add partners for filters - assuming you have Partner model
        from apps.partner.models import Partner
        context['all_partners'] = Partner.objects.all().order_by('name')

        # Create URLs for removing each filter
        base_url = reverse('subscribers:subscriber_list')

        # URL for removing search filter
        search_remove_params = self.request.GET.copy()
        if 'search' in search_remove_params:
            search_remove_params.pop('search')
        if 'page' in search_remove_params:
            search_remove_params.pop('page')
        context['search_remove_url'] = f"{base_url}?{search_remove_params.urlencode()}" if search_remove_params else base_url

        # URL for removing consent filter
        consent_remove_params = self.request.GET.copy()
        if 'consent' in consent_remove_params:
            consent_remove_params.pop('consent')
        if 'page' in consent_remove_params:
            consent_remove_params.pop('page')
        context['consent_remove_url'] = f"{base_url}?{consent_remove_params.urlencode()}" if consent_remove_params else base_url

        # URL for removing page_size filter
        page_size_remove_params = self.request.GET.copy()
        if 'page_size' in page_size_remove_params:
            page_size_remove_params.pop('page_size')
        if 'page' in page_size_remove_params:
            page_size_remove_params.pop('page')
        context['page_size_remove_url'] = f"{base_url}?{page_size_remove_params.urlencode()}" if page_size_remove_params else base_url

        # URLs for removing each group filter
        context['group_remove_urls'] = {}
        for group_id in context['selected_groups']:
            group_remove_params = self.request.GET.copy()
            if 'page' in group_remove_params:
                group_remove_params.pop('page')
            # Remove the specific group ID while keeping others
            group_params = group_remove_params.getlist('group')
            group_remove_params.pop('group')
            for g_id in group_params:
                if g_id != group_id:
                    group_remove_params.appendlist('group', g_id)
            context['group_remove_urls'][group_id] = f"{base_url}?{group_remove_params.urlencode()}" if group_remove_params else base_url

        # URLs for removing each partner filter
        context['partner_remove_urls'] = {}
        for partner_id in context['selected_partners']:
            partner_remove_params = self.request.GET.copy()
            if 'page' in partner_remove_params:
                partner_remove_params.pop('page')
            # Remove the specific partner ID while keeping others
            partner_params = partner_remove_params.getlist('partner')
            partner_remove_params.pop('partner')
            for p_id in partner_params:
                if p_id != partner_id:
                    partner_remove_params.appendlist('partner', p_id)
            context['partner_remove_urls'][partner_id] = f"{base_url}?{partner_remove_params.urlencode()}" if partner_remove_params else base_url

        return context


class SubscriberCreateFormView(LoginRequiredMixin, TemplateView):
    """Widok formularza dodawania subskrybenta"""
    template_name = 'subscriber/subscriber_create_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Istniejący kod...

        # Dodaj wszystkich partnerów do kontekstu
        context['all_partners'] = Partner.objects.all().order_by(
            'name')[:50]  # Ograniczamy do 50 dla wydajności

        context['subscriber_groups'] = SubscriberGroup.objects.all().order_by('group_name')[
            :50]

        # Istniejący kod wyszukiwania partnerów...
        partner_search = self.request.GET.get('partner_search', '')
        if partner_search:
            from django.db.models import Q
            context['filtered_partners'] = Partner.objects.filter(
                Q(name__icontains=partner_search) |
                Q(vat_number__icontains=partner_search) |
                Q(country__name__icontains=partner_search)
            ).order_by('name')

        # Reszta istniejącego kodu...

        return context


class SubscriberCreateView(CreateView):
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscriber/subscriber_create_form.html'

    def get(self, request, *args, **kwargs):
        # Initialize form
        form = self.get_form()

        # Context data
        context = {
            'form': form,
            'subscriber_groups': SubscriberGroup.objects.all().order_by('group_name'),
            'selected_groups': [],
            'selected_partners': [],
            'selected_partner_objects': []
        }

        # Handle group search
        group_search = request.GET.get('group_search', '')
        if group_search:
            context['filtered_groups'] = SubscriberGroup.objects.filter(
                group_name__icontains=group_search
            ).order_by('group_name')

        # Handle partner search
        partner_search = request.GET.get('partner_search', '')
        if partner_search:
            context['filtered_partners'] = Partner.objects.filter(
                Q(name__icontains=partner_search) |
                Q(vat_number__icontains=partner_search) |
                Q(country__name__icontains=partner_search)
            ).order_by('name')

        # Handle form data from previous search
        # For example, if user has already selected some partners/groups before searching
        session_data = request.session.get('subscriber_form_data', {})

        if 'selected_groups' in session_data:
            context['selected_groups'] = session_data['selected_groups']

        if 'selected_partners' in session_data:
            partner_ids = session_data['selected_partners']
            context['selected_partners'] = partner_ids
            if partner_ids:
                context['selected_partner_objects'] = Partner.objects.filter(
                    id__in=partner_ids)

        # If this is a search action, update session for form persistence
        action = request.GET.get('action', '')
        if action in ['search_group', 'search_partner']:
            # Save current form values to session
            form_data = {}

            # Get group IDs from request
            group_ids = request.GET.getlist('group_affiliation')
            if group_ids:
                form_data['selected_groups'] = group_ids
            elif 'selected_groups' in session_data:
                form_data['selected_groups'] = session_data['selected_groups']

            # Get partner IDs from request
            partner_ids = request.GET.getlist('partner_ids')
            if partner_ids:
                form_data['selected_partners'] = partner_ids
            elif 'selected_partners' in session_data:
                form_data['selected_partners'] = session_data['selected_partners']

            # Save to session
            request.session['subscriber_form_data'] = form_data

        return render(request, self.template_name, context)

    # Modify this section in SubscriberCreateView.post() method
    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            # Save the form first to create the subscriber
            subscriber = form.save()

            # Process partner associations if any
            partner_ids = request.POST.getlist('partner_ids')
            if partner_ids:
                # Clear existing relationships first
                from apps.partner.models import PartnerEmail
                PartnerEmail.objects.filter(subscriber=subscriber).delete()

                # Create new relationships through the PartnerEmail model
                for partner_id in partner_ids:
                    try:
                        partner = Partner.objects.get(id=partner_id)
                        PartnerEmail.objects.create(
                            partner=partner,
                            subscriber=subscriber
                        )
                    except Exception as e:
                        # Log error but continue
                        print(f"Error adding partner {partner_id}: {str(e)}")

            # Clear session data
            if 'subscriber_form_data' in request.session:
                del request.session['subscriber_form_data']

            return redirect('subscribers:subscriber_list')

        # If form is invalid, add context for template
        context = {
            'form': form,
            'subscriber_groups': SubscriberGroup.objects.all().order_by('group_name'),
            'selected_groups': request.POST.getlist('group_affiliation'),
            'selected_partners': request.POST.getlist('partner_ids')
        }

        # Get partner objects if any
        partner_ids = request.POST.getlist('partner_ids')
        if partner_ids:
            context['selected_partner_objects'] = Partner.objects.filter(
                id__in=partner_ids)

        return render(request, self.template_name, context)


class SubscriberUpdateView(LoginRequiredMixin, UpdateView):
    """Edycja subskrybenta"""
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscriber/subscriber_update_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pobierz wszystkie grupy
        context['subscriber_groups'] = SubscriberGroup.objects.all().order_by(
            'group_name')

        # Pobierz wszystkich partnerów
        context['all_partners'] = Partner.objects.all().order_by(
            'name')[:50]  # Ograniczenie dla wydajności

        # Obsługa wyszukiwania grup
        group_search = self.request.GET.get('group_search', '')
        if group_search:
            context['filtered_groups'] = SubscriberGroup.objects.filter(
                group_name__icontains=group_search
            ).order_by('group_name')

        # Obsługa wyszukiwania partnerów
        partner_search = self.request.GET.get('partner_search', '')
        if partner_search:
            from django.db.models import Q
            context['filtered_partners'] = Partner.objects.filter(
                Q(name__icontains=partner_search) |
                Q(vat_number__icontains=partner_search) |
                Q(country__name__icontains=partner_search)
            ).order_by('name')

        # Pobierz obecnie wybrane grupy
        if self.object:
            context['selected_groups'] = self.object.group_affiliation.all(
            ).values_list('id', flat=True)
            # Pobierz partnerów powiązanych z tym subskrybentem
            context['selected_partners'] = self.object.partnered_with.all(
            ).values_list('id', flat=True)
        else:
            context['selected_groups'] = []
            context['selected_partners'] = []

        return context

    def form_valid(self, form):
        # Zapisz formularz i uzyskaj obiekt subskrybenta
        subscriber = form.save()

        # Obsługa grup
        group_ids = self.request.POST.getlist('group_ids', [])
        if group_ids:
            # Usuń wszystkie grupy przypisane do subskrybenta
            subscriber.group_affiliation.clear()
            # Dodaj wybrane grupy
            groups = SubscriberGroup.objects.filter(id__in=group_ids)
            subscriber.group_affiliation.add(*groups)

        # Obsługa partnerów
        partner_ids = self.request.POST.getlist('partner_ids', [])
        # Zawsze czyść istniejące powiązania, nawet jeśli partner_ids jest puste
        from apps.partner.models import PartnerEmail
        PartnerEmail.objects.filter(subscriber=subscriber).delete()

        if partner_ids:
            # Dodaj wybrane powiązania
            for partner_id in partner_ids:
                try:
                    partner = Partner.objects.get(id=partner_id)
                    PartnerEmail.objects.create(
                        partner=partner,
                        subscriber=subscriber
                    )
                except Exception as e:
                    # Zaloguj błąd, ale kontynuuj
                    print(f"Error adding partner {partner_id}: {str(e)}")

        messages.success(self.request, _(
            "Subskrybent został zaktualizowany pomyślnie."))
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('subscribers:subscriber_list')


class SubscriberDeleteConfirmView(LoginRequiredMixin, TemplateView):
    """Widok potwierdzenia usunięcia subskrybenta"""
    template_name = 'subscriber/subscriber_delete_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscriber'] = get_object_or_404(Subscriber, pk=kwargs['pk'])
        return context


class SubscriberDeleteView(LoginRequiredMixin, DeleteView):
    """Widok usuwania subskrybenta"""
    model = Subscriber
    success_url = reverse_lazy('subscribers:subscriber_list')

    def delete(self, request, *args, **kwargs):
        subscriber = self.get_object()
        messages.success(request, _(
            f"Subskrybent '{subscriber.email}' został usunięty pomyślnie."))
        return super().delete(request, *args, **kwargs)

# Group views


class SubscriberGroupListView(LoginRequiredMixin, ListView):
    """Lista grup subskrybentów"""
    model = SubscriberGroup
    template_name = 'subscriber/group_list.html'
    context_object_name = 'groups'
    paginate_by = 20

    def get_queryset(self):
        """Filtrowanie wyników"""
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(group_name__icontains=search_query)

        return queryset

    def get_context_data(self, **kwargs):
        """Dodatkowe dane kontekstowe"""
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class SubscriberGroupCreateFormView(LoginRequiredMixin, TemplateView):
    """View for the group creation form"""
    template_name = 'subscriber/group_create_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add form to context if it exists (e.g., after validation error)
        if hasattr(self, 'form'):
            context['form'] = self.form
        return context


class SubscriberGroupCreateView(LoginRequiredMixin, CreateView):
    """Group creation processing"""
    model = SubscriberGroup
    form_class = SubscriberGroupForm
    template_name = 'subscriber/group_create_form.html'

    def get_success_url(self):
        messages.success(self.request, _("Grupa została dodana pomyślnie."))
        return reverse('subscribers:group_list')


class SubscriberGroupUpdateView(LoginRequiredMixin, UpdateView):
    """Group update view with subscriber assignment capabilities"""
    model = SubscriberGroup
    form_class = SubscriberGroupForm
    template_name = 'subscriber/group_update.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get search parameters
        group_search_query = self.request.GET.get('group_search', '')
        search_query = self.request.GET.get('search', '')

        # Get all subscribers in this group
        all_group_subscribers = self.object.subscriber.all()

        # Get filtered group subscribers
        group_subscribers = all_group_subscribers
        if group_search_query:
            group_subscribers = group_subscribers.filter(
                models.Q(email__icontains=group_search_query) |
                models.Q(first_name__icontains=group_search_query) |
                models.Q(last_name__icontains=group_search_query)
            )

        # Add to context
        context['group_subscribers'] = group_subscribers
        context['group_search_query'] = group_search_query

        # Get available subscribers (those not in the group)
        available_subscribers = Subscriber.objects.exclude(
            id__in=all_group_subscribers.values_list('id', flat=True)
        )

        # Filter available subscribers if search provided
        if search_query:
            available_subscribers = available_subscribers.filter(
                models.Q(email__icontains=search_query) |
                models.Q(first_name__icontains=search_query) |
                models.Q(last_name__icontains=search_query)
            )

        # Add to context
        context['available_subscribers'] = available_subscribers
        context['search_query'] = search_query

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Check if this is a group update or subscriber assignment
        if 'update_group' in request.POST:
            # Handle group update
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        elif 'add_subscribers' in request.POST:
            # Handle adding subscribers to group
            subscriber_ids = request.POST.getlist('subscriber_ids', [])
            if subscriber_ids:
                subscribers = Subscriber.objects.filter(id__in=subscriber_ids)
                self.object.subscriber.add(*subscribers)
                messages.success(request, _(
                    f"{len(subscribers)} subskrybentów zostało dodanych do grupy."))
            return redirect('subscribers:group_update', pk=self.object.pk)
        elif 'remove_subscribers' in request.POST:
            # Handle removing subscribers from group
            subscriber_ids = request.POST.getlist('group_subscriber_ids', [])
            if subscriber_ids:
                subscribers = Subscriber.objects.filter(id__in=subscriber_ids)
                self.object.subscriber.remove(*subscribers)
                messages.success(request, _(
                    f"{len(subscribers)} subskrybentów zostało usuniętych z grupy."))
            return redirect('subscribers:group_update', pk=self.object.pk)

        # Default fallback
        return self.get(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, _(
            "Grupa została zaktualizowana pomyślnie."))
        return reverse('subscribers:group_update', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Check if this is a group update or subscriber assignment
        if 'update_group' in request.POST:
            # Handle group update
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        elif 'add_subscribers' in request.POST:
            # Handle adding subscribers to group
            subscriber_ids = request.POST.getlist('subscriber_ids', [])
            if subscriber_ids:
                subscribers = Subscriber.objects.filter(id__in=subscriber_ids)
                self.object.subscriber.add(*subscribers)
                messages.success(request, _(
                    f"{len(subscribers)} subskrybentów zostało dodanych do grupy."))
            return redirect('subscribers:group_update', pk=self.object.pk)
        elif 'remove_subscribers' in request.POST:
            # Handle removing subscribers from group
            subscriber_ids = request.POST.getlist('group_subscriber_ids', [])
            if subscriber_ids:
                subscribers = Subscriber.objects.filter(id__in=subscriber_ids)
                self.object.subscriber.remove(*subscribers)
                messages.success(request, _(
                    f"{len(subscribers)} subskrybentów zostało usuniętych z grupy."))
            return redirect('subscribers:group_update', pk=self.object.pk)

        # Default fallback
        return self.get(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, _(
            "Grupa została zaktualizowana pomyślnie."))
        return reverse('subscribers:group_update', kwargs={'pk': self.object.pk})


class SubscriberGroupDeleteView(LoginRequiredMixin, DeleteView):
    """Group delete view"""
    model = SubscriberGroup
    template_name = 'subscriber/group_delete_confirm.html'
    context_object_name = 'group'

    def get_success_url(self):
        messages.success(self.request, _(f"Grupa została usunięta pomyślnie."))
        return reverse('subscribers:group_list')


class SubscriberGroupViewSubscribersView(LoginRequiredMixin, DetailView):
    """View subscribers in a group"""
    model = SubscriberGroup
    template_name = 'subscriber/group_view_subscribers.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscribers'] = self.object.subscriber.all()
        return context


class SubscriberBulkGroupAssignView(LoginRequiredMixin, View):
    """View for bulk assignment of subscribers to groups"""
    template_name = 'subscriber/bulk_group_assign.html'

    def get(self, request, *args, **kwargs):
        # Get all subscribers and groups for selection
        subscribers = Subscriber.objects.all().order_by('email')
        subscriber_groups = SubscriberGroup.objects.all().order_by('group_name')

        # Pre-select subscribers from query params if provided
        selected_subscriber_ids = request.GET.getlist('subscriber_ids', [])
        selected_subscriber_ids = [
            int(id) for id in selected_subscriber_ids if id.isdigit()]

        context = {
            'subscribers': subscribers,
            'subscriber_groups': subscriber_groups,
            'selected_subscriber_ids': selected_subscriber_ids
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Get selected subscribers and groups
        subscriber_ids = request.POST.getlist('subscriber_ids', [])
        group_ids = request.POST.getlist('group_ids', [])
        action = request.POST.get('action', 'add')  # 'add' or 'remove'

        if not subscriber_ids or not group_ids:
            messages.error(request, _(
                "Musisz wybrać zarówno subskrybentów jak i grupy."))
            return self.get(request, *args, **kwargs)

        # Get objects
        subscribers = Subscriber.objects.filter(id__in=subscriber_ids)
        groups = SubscriberGroup.objects.filter(id__in=group_ids)

        if not subscribers.exists() or not groups.exists():
            messages.error(request, _(
                "Nie znaleziono wybranych subskrybentów lub grup."))
            return self.get(request, *args, **kwargs)

        # Perform the operation
        count = 0
        for subscriber in subscribers:
            if action == 'add':
                subscriber.group_affiliation.add(*groups)
            else:
                subscriber.group_affiliation.remove(*groups)
            count += 1

        # Show success message
        action_text = "przypisani do" if action == 'add' else "usunięci z"
        messages.success(
            request,
            _("{} subskrybentów zostało {} {} grup.").format(
                count, action_text, groups.count()
            )
        )

        return redirect('subscribers:subscriber_list')


class SubscriberBulkEditView(LoginRequiredMixin, View):
    """Widok formularza masowej edycji subskrybentów"""

    def post(self, request, *args, **kwargs):
        # Pobierz zaznaczone ID
        selected_ids = request.POST.get('selected_ids', '')
        if not selected_ids:
            messages.error(request, "Nie wybrano żadnych subskrybentów.")
            return redirect('subscribers:subscriber_list')

        # Przygotuj listę ID
        subscriber_ids = [int(id)
                          for id in selected_ids.split(',') if id.isdigit()]

        # Pobierz subskrybentów
        subscribers = Subscriber.objects.filter(id__in=subscriber_ids)

        if not subscribers.exists():
            messages.error(request, "Nie znaleziono wybranych subskrybentów.")
            return redirect('subscribers:subscriber_list')

        # Pobierz inne dane potrzebne do formularza
        subscriber_groups = SubscriberGroup.objects.all().order_by('group_name')
        all_partners = Partner.objects.all().order_by(
            'name')  # Dodaj pobieranie partnerów

        # Renderuj formularz
        return render(request, 'subscriber/subscriber_bulk_edit.html', {
            'selected_ids': selected_ids,
            'subscribers': subscribers,
            'subscriber_groups': subscriber_groups,
            'all_partners': all_partners,  # Dodaj partnerów do kontekstu
        })


# class SubscriberBulkUpdateView(LoginRequiredMixin, View):
#     """Widok do przetwarzania masowej aktualizacji subskrybentów"""

#     def post(self, request, *args, **kwargs):
#         # Pobierz zaznaczone ID
#         selected_ids = request.POST.get('selected_ids', '')
#         if not selected_ids:
#             messages.error(request, "Nie wybrano żadnych subskrybentów.")
#             return redirect('subscribers:subscriber_list')

#         # Przygotuj listę ID
#         subscriber_ids = [int(id)
#                           for id in selected_ids.split(',') if id.isdigit()]

#         # Sprawdź, które pola mają być zaktualizowane
#         fields_to_update = []
#         for field in ['email', 'common_name', 'first_name', 'last_name', 'partner_ids', 'group_ids', 'newsletter_consent']:
#             if request.POST.get(f'update_{field}') == 'true':
#                 fields_to_update.append(field)

#         if not fields_to_update:
#             messages.warning(
#                 request, "Nie wybrano żadnych pól do aktualizacji.")
#             return redirect('subscribers:subscriber_list')

#         # Licznik aktualizacji
#         update_count = 0

#         # Aktualizuj każdego subskrybenta osobno
#         for subscriber_id in subscriber_ids:
#             try:
#                 subscriber = Subscriber.objects.get(id=subscriber_id)

#                 # Aktualizuj poszczególne pola
#                 update_performed = False

#                 # Aktualizuj email
#                 if 'email' in fields_to_update:
#                     new_email = request.POST.get(f'email_{subscriber_id}')
#                     if new_email and new_email != subscriber.email:
#                         subscriber.email = new_email
#                         update_performed = True

#                 # Aktualizuj common_name
#                 if 'common_name' in fields_to_update:
#                     new_common_name = request.POST.get(
#                         f'common_name_{subscriber_id}')
#                     if new_common_name != subscriber.common_name:
#                         subscriber.common_name = new_common_name
#                         update_performed = True

#                 # Aktualizuj first_name
#                 if 'first_name' in fields_to_update:
#                     new_first_name = request.POST.get(
#                         f'first_name_{subscriber_id}')
#                     if new_first_name != subscriber.first_name:
#                         subscriber.first_name = new_first_name
#                         update_performed = True

#                 # Aktualizuj last_name
#                 if 'last_name' in fields_to_update:
#                     new_last_name = request.POST.get(
#                         f'last_name_{subscriber_id}')
#                     if new_last_name != subscriber.last_name:
#                         subscriber.last_name = new_last_name
#                         update_performed = True

#                 # Aktualizuj newsletter_consent
#                 if 'newsletter_consent' in fields_to_update:
#                     raw_value = request.POST.get(
#                         f'newsletter_consent_{subscriber_id}')
#                     new_consent = (raw_value == 'true')

#                     # Make absolutely sure we're doing a true boolean comparison
#                     if bool(new_consent) != bool(subscriber.newsletter_consent):
#                         print(
#                             f"Changing newsletter consent from {subscriber.newsletter_consent} to {new_consent}")
#                         subscriber.newsletter_consent = new_consent
#                         # Force save after this specific change
#                         subscriber.save()
#                         update_count += 1

#                 # Aktualizuj powiązania z partnerami
#                 if 'partner_ids' in fields_to_update:
#                     partner_ids = request.POST.getlist(
#                         f'partner_ids_{subscriber_id}')
#                     partners = Partner.objects.filter(id__in=partner_ids)

#                     # Pobierz aktualnych partnerów
#                     current_partners = set(
#                         subscriber.partnered_with.all().values_list('id', flat=True))
#                     new_partners = set(int(id)
#                                        for id in partner_ids if id.isdigit())

#                     # Jeśli partnerzy się zmienili, zaktualizuj
#                     if current_partners != new_partners:
#                         # Aktualizacja relacji M2M
#                         # Zakładając że relacja jest zdefiniowana przez model pośredni PartnerEmail
#                         from apps.partner.models import PartnerEmail

#                         # Usuń istniejące powiązania
#                         PartnerEmail.objects.filter(
#                             subscriber=subscriber).delete()

#                         # Dodaj nowe powiązania
#                         for partner in partners:
#                             PartnerEmail.objects.create(
#                                 partner=partner, subscriber=subscriber)

#                         update_count += 1

#                     # Aktualizuj grupy
#                     if 'group_ids' in fields_to_update:
#                         group_ids = request.POST.getlist(
#                             f'group_ids_{subscriber_id}')
#                         groups = SubscriberGroup.objects.filter(
#                             id__in=group_ids)

#                         # Pobierz aktualne grupy
#                         current_groups = set(
#                             subscriber.group_affiliation.all().values_list('id', flat=True))
#                         new_groups = set(int(id)
#                                          for id in group_ids if id.isdigit())

#                         # Jeśli grupy się zmieniły, zaktualizuj
#                         if current_groups != new_groups:
#                             subscriber.group_affiliation.set(groups)
#                             update_count += 1

#                     # Zapisz zmiany jeśli jakiekolwiek pola były aktualizowane
#                     if update_performed:
#                         subscriber.save()
#                         update_count += 1

#             except Subscriber.DoesNotExist:
#                 continue

#         # Wyświetl komunikat o aktualizacji
#         if update_count > 0:
#             messages.success(
#                 request, f"Pomyślnie zaktualizowano {update_count} subskrybentów.")
#         else:
#             messages.info(request, "Nie wprowadzono żadnych zmian.")

#         return redirect('subscribers:subscriber_list')

class SubscriberBulkUpdateView(LoginRequiredMixin, View):
    """Widok do przetwarzania masowej aktualizacji subskrybentów"""

    def post(self, request, *args, **kwargs):
        # Pobierz zaznaczone ID
        selected_ids = request.POST.get('selected_ids', '')
        if not selected_ids:
            messages.error(request, "Nie wybrano żadnych subskrybentów.")
            return redirect('subscribers:subscriber_list')

        # Przygotuj listę ID
        subscriber_ids = [int(id)
                          for id in selected_ids.split(',') if id.isdigit()]

        # Sprawdź, które pola mają być zaktualizowane
        fields_to_update = []
        for field in ['email', 'common_name', 'first_name', 'last_name', 'partner_ids', 'group_ids', 'newsletter_consent']:
            if request.POST.get(f'update_{field}') == 'true':
                fields_to_update.append(field)

        if not fields_to_update:
            messages.warning(
                request, "Nie wybrano żadnych pól do aktualizacji.")
            return redirect('subscribers:subscriber_list')

        # Licznik aktualizacji
        update_count = 0
        error_count = 0

        # Aktualizuj każdego subskrybenta osobno
        for subscriber_id in subscriber_ids:
            try:
                subscriber = Subscriber.objects.get(id=subscriber_id)
                field_updated = False  # Track if any field was updated for this subscriber

                # Aktualizuj email - Dodaj sprawdzenie unikalności
                if 'email' in fields_to_update:
                    new_email = request.POST.get(f'email_{subscriber_id}')
                    if new_email and new_email != subscriber.email:
                        # Sprawdź, czy email jest unikalny
                        if not Subscriber.objects.filter(email=new_email).exclude(id=subscriber_id).exists():
                            subscriber.email = new_email
                            field_updated = True
                            print(
                                f"Email updated from {subscriber.email} to {new_email}")
                        else:
                            # Email istnieje już w bazie
                            error_count += 1
                            print(
                                f"Error: Email {new_email} already exists in database")
                            messages.error(
                                request, f"Email {new_email} jest już używany przez innego subskrybenta.")
                            continue  # Skip this subscriber

                # Aktualizuj common_name
                if 'common_name' in fields_to_update:
                    new_common_name = request.POST.get(
                        f'common_name_{subscriber_id}')
                    if new_common_name != subscriber.common_name:
                        subscriber.common_name = new_common_name
                        field_updated = True
                        print(f"Common name updated to {new_common_name}")

                # Aktualizuj first_name
                if 'first_name' in fields_to_update:
                    new_first_name = request.POST.get(
                        f'first_name_{subscriber_id}')
                    if new_first_name != subscriber.first_name:
                        subscriber.first_name = new_first_name
                        field_updated = True
                        print(f"First name updated to {new_first_name}")

                # Aktualizuj last_name
                if 'last_name' in fields_to_update:
                    new_last_name = request.POST.get(
                        f'last_name_{subscriber_id}')
                    if new_last_name != subscriber.last_name:
                        subscriber.last_name = new_last_name
                        field_updated = True
                        print(f"Last name updated to {new_last_name}")

                # Aktualizuj newsletter_consent
                if 'newsletter_consent' in fields_to_update:
                    raw_value = request.POST.get(
                        f'newsletter_consent_{subscriber_id}')
                    new_consent = (raw_value == 'true')

                    if bool(new_consent) != bool(subscriber.newsletter_consent):
                        print(
                            f"Changing newsletter consent from {subscriber.newsletter_consent} to {new_consent}")
                        subscriber.newsletter_consent = new_consent
                        field_updated = True

                # Save if basic fields were updated
                if field_updated:
                    subscriber.save()
                    update_count += 1

                # Aktualizuj powiązania z partnerami
                if 'partner_ids' in fields_to_update:
                    partner_ids = request.POST.getlist(
                        f'partner_ids_{subscriber_id}')
                    # Convert empty strings to empty list
                    if not partner_ids or (len(partner_ids) == 1 and partner_ids[0] == ''):
                        partner_ids = []

                    partners = Partner.objects.filter(id__in=partner_ids)

                    # Pobierz aktualnych partnerów
                    current_partners = set(
                        subscriber.partnered_with.all().values_list('id', flat=True))
                    new_partners = set(int(id)
                                       for id in partner_ids if id.isdigit())

                    # Jeśli partnerzy się zmienili, zaktualizuj
                    if current_partners != new_partners:
                        # Aktualizacja relacji M2M
                        from apps.partner.models import PartnerEmail

                        # Usuń istniejące powiązania
                        PartnerEmail.objects.filter(
                            subscriber=subscriber).delete()

                        # Dodaj nowe powiązania
                        for partner in partners:
                            PartnerEmail.objects.create(
                                partner=partner, subscriber=subscriber)

                        update_count += 1
                        print(
                            f"Partners updated for subscriber {subscriber_id}")

                # Aktualizuj grupy - fixed indentation!
                if 'group_ids' in fields_to_update:
                    group_ids = request.POST.getlist(
                        f'group_ids_{subscriber_id}')
                    # Convert empty strings to empty list
                    if not group_ids or (len(group_ids) == 1 and group_ids[0] == ''):
                        group_ids = []

                    groups = SubscriberGroup.objects.filter(id__in=group_ids)

                    # Pobierz aktualne grupy
                    current_groups = set(
                        subscriber.group_affiliation.all().values_list('id', flat=True))
                    new_groups = set(int(id)
                                     for id in group_ids if id.isdigit())

                    # Jeśli grupy się zmieniły, zaktualizuj
                    if current_groups != new_groups:
                        subscriber.group_affiliation.set(groups)
                        update_count += 1
                        print(
                            f"Groups updated for subscriber {subscriber_id}, from {current_groups} to {new_groups}")

            except Subscriber.DoesNotExist:
                continue
            except Exception as e:
                error_count += 1
                print(f"Error updating subscriber {subscriber_id}: {str(e)}")
                messages.error(
                    request, f"Błąd podczas aktualizacji subskrybenta {subscriber_id}: {str(e)}")

        # Wyświetl komunikat o aktualizacji
        if update_count > 0:
            messages.success(
                request, f"Pomyślnie zaktualizowano {update_count} subskrybentów.")
        else:
            messages.info(request, "Nie wprowadzono żadnych zmian.")

        if error_count > 0:
            messages.warning(
                request, f"Wystąpiły błędy podczas aktualizacji {error_count} subskrybentów.")

        return redirect('subscribers:subscriber_list')


class SubscriberBulkActionView(LoginRequiredMixin, View):
    """View for processing bulk actions on subscribers"""

    def post(self, request, *args, **kwargs):
        # Get selected subscriber IDs
        subscriber_ids = request.POST.getlist('subscriber_ids', [])

        if not subscriber_ids:
            messages.error(request, "Nie wybrano żadnych subskrybentów.")
            return redirect('subscribers:subscriber_list')

        # Get the selected action
        bulk_action = request.POST.get('bulk_action', '')

        # Count of affected subscribers
        affected_count = 0

        # Process according to the selected action
        if bulk_action == 'consent_yes' or bulk_action == 'consent_no':
            # Set newsletter consent
            new_consent = (bulk_action == 'consent_yes')
            for subscriber_id in subscriber_ids:
                try:
                    subscriber = Subscriber.objects.get(id=subscriber_id)
                    subscriber.newsletter_consent = new_consent
                    subscriber.save()
                    affected_count += 1
                except Subscriber.DoesNotExist:
                    continue

            consent_text = "TAK" if new_consent else "NIE"
            messages.success(
                request, f"Zmieniono zgodę na {consent_text} dla {affected_count} subskrybentów.")

        elif bulk_action in ['add_to_groups', 'remove_from_groups']:
            # Process group assignment
            group_ids = request.POST.getlist('group_ids', [])

            if not group_ids:
                messages.error(request, "Nie wybrano żadnych grup.")
                return redirect('subscribers:subscriber_list')

            groups = SubscriberGroup.objects.filter(id__in=group_ids)

            for subscriber_id in subscriber_ids:
                try:
                    subscriber = Subscriber.objects.get(id=subscriber_id)

                    if bulk_action == 'add_to_groups':
                        subscriber.group_affiliation.add(*groups)
                    else:
                        subscriber.group_affiliation.remove(*groups)

                    affected_count += 1
                except Subscriber.DoesNotExist:
                    continue

            action_text = "dodano do" if bulk_action == 'add_to_groups' else "usunięto z"
            messages.success(
                request, f"{affected_count} subskrybentów {action_text} wybranych grup.")

        elif bulk_action in ['add_to_partners', 'remove_from_partners']:
            # Process partner assignment
            partner_ids = request.POST.getlist('partner_ids', [])

            if not partner_ids:
                messages.error(request, "Nie wybrano żadnych firm.")
                return redirect('subscribers:subscriber_list')

            partners = Partner.objects.filter(id__in=partner_ids)

            for subscriber_id in subscriber_ids:
                try:
                    subscriber = Subscriber.objects.get(id=subscriber_id)

                    if bulk_action == 'add_to_partners':
                        # Add partners
                        for partner in partners:
                            PartnerEmail.objects.get_or_create(
                                partner=partner,
                                subscriber=subscriber
                            )
                    else:
                        # Remove partners
                        PartnerEmail.objects.filter(
                            subscriber=subscriber,
                            partner__in=partners
                        ).delete()

                    affected_count += 1
                except Subscriber.DoesNotExist:
                    continue

            action_text = "dodano do" if bulk_action == 'add_to_partners' else "usunięto z"
            messages.success(
                request, f"{affected_count} subskrybentów {action_text} wybranych firm.")

        return redirect('subscribers:subscriber_list')
