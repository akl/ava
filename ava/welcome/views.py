import logging

import django.views.generic.edit
import django.views.generic.base
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator

from . import forms

from ava.import_ldap import forms as import_ldap_forms
from ava.import_google import forms as import_google_forms
from ava.utils import require_ava_superuser

log = logging.getLogger(__name__)


class CreateFirstUser(django.views.generic.edit.FormView):
    template_name = 'welcome/create_first_user.html'
    form_class = forms.CreateFirstSuperUser
    success_url = reverse_lazy('welcome-import-selection')

    def form_valid(self, form):
        # create the new superuser as described in the form
        user = form.save()

        # Now use the data from the same form to authenticate() and
        # login(). This looks weird, but it's required to set the
        # correct auth_backend. See the link for details:
        # https://docs.djangoproject.com/en/1.8/topics/auth/default/#django.contrib.auth.login
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1']
        )
        login(self.request, user)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add a conventient template context variable to know if the
        # form should be visible.
        context['no_users_exist'] = not User.objects.exists()
        return context


class ImportSelection(django.views.generic.base.TemplateView):
    template_name = 'welcome/import_selection.html'

    ## Use 'method_decorator' and 'require_ava_superuser' to force
    ## This view to be usable only by the AVA superuser.
    @method_decorator(require_ava_superuser)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ImportLDAP(django.views.generic.edit.FormView):
    template_name = 'welcome/import_ldap.html'
    success_url = reverse_lazy('welcome-import-progress')

    form_class = import_ldap_forms.LDAPConfigurationCredentialsForm

    ## Use 'method_decorator' and 'require_ava_superuser' to force
    ## This view to be usable only by the AVA superuser.
    @method_decorator(require_ava_superuser)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        import_successful = form.run_ldap_import()

        if import_successful:
            return super().form_valid(form)
        else:
            return super().form_invalid(form)


class ImportGoogle(django.views.generic.edit.FormView):
    template_name = 'welcome/import_google.html'
    success_url = reverse_lazy('google-auth-login-redirect')

    form_class = import_google_forms.GoogleConfigurationWelcomeForm

    ## Use 'method_decorator' and 'require_ava_superuser' to force
    ## This view to be usable only by the AVA superuser.
    @method_decorator(require_ava_superuser)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        import_successful, google_config = form.run_google_import()

        if google_config is not None:
            self.request.session['google_configuration_id'] = google_config.id

        if import_successful:
            return super().form_valid(form)
        else:
            return super().form_invalid(form)


class ImportProgress(django.views.generic.base.TemplateView):
    template_name = 'welcome/import_progress.html'

    ## Use 'method_decorator' and 'require_ava_superuser' to force
    ## This view to be usable only by the AVA superuser.
    @method_decorator(require_ava_superuser)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
