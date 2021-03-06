#!/usr/bin/env python
# encoding=utf-8
import logging

from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.translation import ugettext_lazy as _
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.contrib.auth.decorators import login_required

from rapidsms.models import Contact

from group_messaging.models import Group, Site
from group_messaging.forms import GroupForm


@login_required
def list(request):
    groups = Group.objects.annotate(count=Count('recipients'))
    context = {
        'groups': groups.order_by('code'),
    }
    return render_to_response('groups_users/groups/list.html', context,
                              context_instance=RequestContext(request))


@login_required
def add(request):
    ''' add function '''
    if request.method == 'POST':  # If the form has been submitted...
        form = GroupForm(request.contact.site, request.POST)
        if form.is_valid():  # All validation rules pass
            form.save()
            return HttpResponseRedirect(reverse('new_group'))
    else:
        form = GroupForm(site=request.contact.site)  # An unbound form
    context = {'form': form}
    return render_to_response('groups_users/groups/create_edit.html', context,
                              context_instance=RequestContext(request))


@login_required
def delete(request, group_id):

    ''' add function '''

    try:
        Groups_obj = Group.objects.get(id=group_id)
        Groups_obj.delete()
    except Exception, e:
        return HttpResponse("Error 2 : %s" % e)

    return redirect(list)


@login_required
def update(request, group_id):
    group = get_object_or_404(Group, pk=group_id)

    ''' add function '''
    if request.method == 'POST':  # If the form has been submitted...
        form = GroupForm(request.contact.site, request.POST)
        if form.is_valid():  # All validation rules pass
            code = form.cleaned_data['code']
            name = form.cleaned_data['name']
            active = form.cleaned_data['active']
            recipients = form.cleaned_data['recipients']
            managers = form.cleaned_data['managers']

            try:
                group = Group.objects.get(id=group_id)
                group.name = name
                group.code = code
                group.active = active
                group.save()

                group.recipients.clear()
                for recipient in recipients:
                    group.recipients.add(recipient)
                group.managers.clear()
                for manager in managers:
                    group.managers.add(manager)
                    
            except Exception, e:
                return HttpResponse("Error 2 : %s" % e)

            return HttpResponseRedirect('/group_messaging/groups/')

    else:
        Groups_obj = Group.objects.get(id=group_id)
        managers = [(manager.id) for manager \
                    in Groups_obj.managers.select_related()]

        recipients = [(recipient.id) for recipient \
                    in Groups_obj.recipients.select_related()]

        form = GroupForm(request.contact.site, \
                initial={'code': Groups_obj.code, \
                'name': Groups_obj.name, 'active': Groups_obj.active, \
                'managers': managers,'recipients': recipients})

    context = {'form': form, 'group': group}

    return render_to_response('groups_users/groups/create_edit.html', context, context_instance=RequestContext(request))
