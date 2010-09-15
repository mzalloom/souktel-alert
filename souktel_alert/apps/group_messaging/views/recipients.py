#!/usr/bin/env python
# encoding=utf-8
import logging

from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _
from django.template import RequestContext
from django.forms.formsets import formset_factory
from django.contrib import messages

from django.http import HttpResponseRedirect

from rapidsms.models import Contact

from group_messaging.models import Recipient
from group_messaging.models import Site
from group_messaging.models import Group
from group_messaging.decorators import contact_required

from group_messaging.forms import RecipientForm, ConnectionFormset


@contact_required
def list_recipients(request):
    recipients = Contact.objects.filter(site=request.contact.site)
    paginator = Paginator(recipients,10)
    
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    
    try:
        recipient_list = paginator.page(page)
    except (EmptyPage, InvalidPage):
        recipient_list = paginator.page(paginator.num_pages)

    context = {'recipients': recipient_list,'count':recipients.count()}
    return render_to_response('recipients_list.html', context,
                              context_instance=RequestContext(request))


@contact_required
def recipient(request, recipientid=None):
    instance = Contact()
    if recipientid:
        instance = get_object_or_404(Contact, pk=recipientid)

    if request.method == 'POST':
        form = RecipientForm(request.POST, instance=instance)
        formset = ConnectionFormset(request.POST, instance=instance)
        if form.is_valid() and formset.is_valid():
            saved_contact = form.save()
            connections = formset.save(commit=False)
            for connection in connections:
                connection.contact = saved_contact
                connection.save()
            if recipientid:
                msg = _(u"You have successfully updated the recipient")
            else:
                msg = "You have successfully inserted a recipient %s."
                msg = _(msg % saved_contact.name)
            messages.add_message(request, messages.INFO, msg)
            return redirect(list_recipients)
    else:
        form = RecipientForm(instance=instance)
        formset = ConnectionFormset(instance=instance)

    context = {
        'recipient': recipient,
        'form': form,
        'formset': formset,
    }
    return render_to_response('recipient.html', context,
                              context_instance=RequestContext(request))


@contact_required
def delete(request, recipientid):
    recipient = get_object_or_404(Contact, pk=recipientid)
    recipient.delete()
    msg = "You have successfully deleted this record"
    messages.add_message(request, messages.INFO, msg)
    return redirect(list_recipients)


class BulkRecipientForm(forms.Form):
       
    firstName = forms.CharField(label=_(u"First Name"), max_length=50)
    lastName  = forms.CharField(label=_(u"Last Name"),max_length=50)
    identity  = forms.CharField(label=_(u"Identity"),max_length=30)
    active    = forms.BooleanField(label=_(u"Active"),required=False)

@contact_required
def manage_recipients(request,context):

    RecipientFormSet = formset_factory(BulkRecipientForm, extra=3)
    if request.method == 'POST':
        groupid = request.POST['group']
        if groupid and groupid.__len__() > 0:
            group = Group.objects.get(id=groupid)
        #groupSite = Group.objects.get(site=request.contact.site)
        #print groupSite
        #if groupSite.id <> request.contact.site.id :
            #raise forms.ValidationError('Invalid user site : user site is different than entered site??')
        formset = RecipientFormSet(request.POST, request.FILES)
        if formset.is_valid():
            try:
                for form in formset.forms:                
                    if form.is_valid() and form.cleaned_data:
                        recipient = Recipient(first_name=form.cleaned_data['firstName'] ,\
                                           last_name=form.cleaned_data['lastName'],\
                                           identity=form.cleaned_data['identity'],\
                                           active=form.cleaned_data['active'],\
                                           site = request.contact.site)
                        recipient.save()
                        if groupid and groupid.__len__() > 0:
                            group.recipients.add(recipient)
            
            except Exception, e :
                    validationMsg = "Failed to add new recipient %s." % e
                    raise
       
            mycontext = {}  #{'validationMsg':validationMsg}
            context = (mycontext)
            return redirect(list)
        else:
            print "ddsadsd"
    else:
        formset = RecipientFormSet()

    groups = Group.objects.filter(site=request.contact.site, active=True)
    mycontext = {'formset': formset, 'groups': groups}
    context = (mycontext)
    return render_to_response('manage_recipients.html', context, context_instance=RequestContext(request))
   