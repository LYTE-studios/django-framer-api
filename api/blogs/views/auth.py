from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from ..forms import EmailUserCreationForm

class RegisterView(CreateView):
    form_class = EmailUserCreationForm
    template_name = 'client/register.html'
    success_url = reverse_lazy('client:login')