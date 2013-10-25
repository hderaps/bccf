from functools import wraps
import logging
from urlparse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http.response import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.decorators import available_attrs
from django.utils.encoding import force_str
from django.utils.http import urlencode

from bccf.models import Settings


log = logging.getLogger(__name__)


def require_member(category_name, func, request, *args, **kwargs):
    log.debug('Requiring %s' % category_name)
    user = request.user
    absolute_uri = request.build_absolute_uri()
    path = request.get_full_path()
    # Must be logged in.
    if not user or user.is_anonymous():
        resolved_login_url = force_str(resolve_url(settings.LOGIN_URL))
        login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
        current_scheme, current_netloc = urlparse(absolute_uri)[:2]
        if ((not login_scheme or login_scheme == current_scheme) and (not login_netloc or login_netloc == current_netloc)):
            path = request.get_full_path()
        else:
            path = absolute_uri
        log.debug('User not logged in. Redirecting to login page')
        return redirect_to_login(path, resolved_login_url)
    # Must have a profile
    if not user.profile:
        messages.info(request, 'Please update your profile information.')
        log.debug('User has no profile. Redirecting to profile page')
        return HttpResponseRedirect('/member/profile/?%s' % urlencode((('next', path),)))
    # Must have a parent membership product
    membership_product = user.profile.membership_product
    if membership_product:
        is_parent_product = False
        categ_slugs = [category_name, 'membership/%s' % category_name]
        for category in membership_product.categories.all():
            log.debug('Checking if %s is in %s' % (category.slug, categ_slugs))
            if category.slug in categ_slugs:
                is_parent_product = True
        if not is_parent_product:
            # If it's not a parent, we'll just redirect to the front page with a message.
            messages.info(request, 'Sorry, you do not have the required membership for that event. If this is a mistake, please contact the administration.')
            return HttpResponseRedirect('/')
    else:
        # No product - ask them to select membership!
        messages.info(request, 'Please select the type of membership you prefer.')
        return HttpResponseRedirect('/member/membership/%s/?%s' % (category_name, urlencode((('next', path),))))
    retval = func(request, *args, **kwargs)
    return retval


def require_parent(func):
    @wraps(func, assigned=available_attrs(func))
    def _wrapper(request, *args, **kwargs):
        return require_member(Settings.get_setting('PARENT_MEMBERSHIP_CATEGORY'), func, request, *args, **kwargs)
    return _wrapper


def require_professional(func):
    @wraps(func, assigned=available_attrs(func))
    def _wrapper(request, *args, **kwargs):
        return require_member(Settings.get_setting('PROFESSIONAL_MEMBERSHIP_CATEGORY'), func, request, *args, **kwargs)
    return _wrapper