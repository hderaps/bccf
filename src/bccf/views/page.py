from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.db.models import ObjectDoesNotExist, Q
from django.http import HttpResponse
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from bccf.models import BCCFPage, BCCFChildPage, BCCFBabyPage, BCCFTopic, UserProfile
from pybb.models import Topic

import logging
import json

log = logging.getLogger(__name__)

@staff_member_required
def bccf_admin_page_ordering(request):
    """
    Updates the ordering of pages via AJAX from within the admin.
    """

    def get_id(s):
        s = s.split("_")[-1]
        return s if s and s != "null" else None
    page = get_object_or_404(BCCFChildPage, id=get_id(request.POST['id']))
    old_parent_id = page.parent_id
    new_parent_id = get_id(request.POST['parent_id'])
    if new_parent_id != page.parent_id:
        # Parent changed - set the new parent and re-order the
        # previous siblings.
        if new_parent_id is not None:
            new_parent = BCCFChildPage.objects.get(id=new_parent_id)
        else:
            new_parent = None
        page.set_parent(new_parent)
        pages = BCCFChildPage.objects.filter(parent_id=old_parent_id)
        for i, page in enumerate(pages.order_by('_order')):
            BCCFChildPage.objects.filter(id=page.id).update(_order=i)
    # Set the new order for the moved page and its current siblings.
    for i, page_id in enumerate(request.POST.getlist('siblings[]')):
        BCCFChildPage.objects.filter(id=get_id(page_id)).update(_order=i)
    return HttpResponse("ok")

def page(request, parent, child=None, baby=None):
    if(not request.is_ajax()):
        page = get_object_or_404(BCCFPage, slug=parent)
        template = 'bccf/%s_page.html' % (parent)
    else: 
        baby_obj = None
        if baby and baby != 'baby-resources' and baby != 'child-home':
            baby_temp = BCCFBabyPage.objects.get(slug=('%s/%s') % (child, baby))
            baby_obj = slugify(baby_temp.title)
        elif baby:
            baby_obj = baby
        child_obj = BCCFChildPage.objects.get(slug=child)
        if child_obj.content_model == 'eventforprofessionals':
            babies = BCCFChildPage.objects.filter(~Q(content_model='formpublished'), parent=child_obj).order_by('_order')        
        else:
            babies = BCCFChildPage.objects.filter(parent=child_obj, status=2).order_by('_order')
        template = 'generic/sub_page.html'

        #Related resources
        q = Q()
        for topic in child_obj.bccf_topic.all():        
            q = q | Q(bccf_topic = topic) 
        resources_pre = BCCFChildPage.objects.filter(Q(content_model='article') | Q(content_model='downloadableform') | Q(content_model='magazine') | Q(content_model='tipsheet') | Q(content_model='video')).distinct()    
        resources = resources_pre.filter(q, ~Q(slug=child)).order_by('?')[:10]
        
    context = RequestContext(request, locals())
    return render_to_response(template, {}, context_instance=context)
    
def topic_page(request, topic):
    page = get_object_or_404(BCCFTopic, slug=topic)
    context = RequestContext(request, locals())
    return render_to_response('bccf/topic_page.html', {}, context_instance=context)

def user_list(request):
    p = request.GET.get('page_var')
    f = request.GET.get('filter')

    if f:
        users_list = UserProfile.objects.filter(user__last_name__startswith=f).order_by('user__last_name', 'user__first_name')
    else:
        users_list = UserProfile.objects.all().order_by('user__last_name', 'user__first_name')       
        
    paginator = Paginator(users_list, 10)
    
    try:
        recordlist = paginator.page(p)
    except PageNotAnInteger:
        recordlist = paginator.page(1)
    except EmptyPage:
        recordlist = paginator.page(paginator.num_pages)
    context = RequestContext(request, locals())
    return render_to_response('bccf/user_directory.html', {}, context_instance=context)  
    
def next(request, parent, which, offset):
    if request.is_ajax():
        obj = BCCFPage.objects.get(slug=parent)
        if obj.slug == 'resources' or obj.slug == 'tag':
            slides = BCCFChildPage.objects.filter(gparent=obj.pk, content_model=which, status=2).order_by('-created')[offset:12]
        elif which == 'parent' or which == 'professional':
            slides = BCCFChildPage.objects.filter(gparent=obj.pk, page_for=which, status=2).order_by('-created')[offset:12]
        else:
            slides = BCCFChildPage.objects.filter(gparent=obj.pk, status=2).order_by('-created')[offset:12]
        parts = {
            'slide': render_to_string('generic/carousel_slide_part.html', {'slides':slides}),
            'grid': render_to_string('generic/carousel_slide_part.html', {'slides':slides})
        }    
        return HttpResponse(json.dumps(parts), content_type="application/json")
    else:
        return HttpResponse('No')

def topic_next(request, topic, which, offset):
    topic = BCCFTopic.objects.get(slug=topic)    
    slides = BCCFChildPage.objects.filter(topic=topic, page_for=which, status=2).order_by('-created')[offset:12]
    parts = {
        'slide': render_to_string('generic/carousel_slide_part.html', {'slides':slides}),
    }    
    return HttpResponse(json.dumps(parts), content_type="application/json")
    
def filter(request, query=None, type='slide'):
    if request.is_ajax():
        if query != '':    
            topics = BCCFTopic.objects.filter(Q(title__icontains=query))
            slides = BCCFChildPage.objects.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(bccf_topic=topics), content_model='topic', status=2).distinct()
        else:
            slides = BCCFChildPage.objects.filter(content_model='topic', status=2).order_by('-created')[:12]
        parts = {
            'slide': render_to_string('generic/carousel_slide_part.html', {'slides':slides}),
            'grid': render_to_string('generic/carousel_slide_part.html', {'slides':slides})
        }
        return HttpResponse(json.dumps(parts), content_type="application/json")
    else:
        return HttpResponse('No')