import logging
log = logging.getLogger(__name__)

from django.template.context import Context
from django.template.loader import get_template

from mezzanine import template

from bccf import forms

register = template.Library()

@register.render_tag
def tab_content(context, token):
    tab = context['tab']
    user = context['user']
    t = get_template('accounts/account_profile_update_%s.html' % tab)

    if 'form' in context:
        return t.render(Context(context))
    if tab == 'account':
        context['form'] = forms.AccountInformationForm(instance=user, initial={'postal_code':user.profile.postal_code})
    elif tab == 'contact':
        context['form'] = forms.ContactInformationForm(instance=user.profile)
    return t.render(Context(context))