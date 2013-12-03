from django.db.models import ObjectDoesNotExist
from mezzanine import template
from bccf.models import Topic, HomeMarquee, HomeMarqueeSlide

import logging

log = logging.getLogger(__name__)

register = template.Library()

@register.inclusion_tag("generic/includes/big_marquee.html", takes_context=True)
def big_marquee_for(context, obj=None):
    """
    Provides generic content variable for the big marquee.
    """
    if obj is None: # For index
        context['show_tag'] = True
        context['topics'] = Topic.objects.all()
        try:
            homeMarquee = HomeMarquee.objects.get(active=True)
            context['slides'] = HomeMarqueeSlide.objects.filter(marquee=homeMarquee)
        except ObjectDoesNotExist:
            pass
    else: # For other pages
        context['show_tag'] = False
        #process object
    return context