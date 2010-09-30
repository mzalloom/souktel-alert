#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django import forms
from models import *

from decisiontree.utils import parse_tags, edit_string_for_tags


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer

    def clean_alias(self):
        data = self.cleaned_data["trigger"]
        return data.lower()


class TreesForm(forms.ModelForm):

    class Meta:
        model = Tree

    def __init__(self, *args, **kwargs):
        super(TreesForm, self).__init__(*args, **kwargs)
        states = TreeState.objects.select_related('question')
        states = states.order_by('question__text')
        self.fields['root_state'].label = 'First State'
        self.fields['root_state'].queryset = states
        self.fields['trigger'].label = 'Keyword'
        self.fields['completion_text'].label = 'Completion Text'


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['text'].label = 'Message Text'
        self.fields['error_response'].label = 'Error Text'
    
    
class StateForm(forms.ModelForm):

    class Meta:
        model = TreeState


class ReportForm(forms.Form):

    ANALYSIS_TYPES = (
        ('A', 'Mean'),
        ('R', 'Median'),
        ('C', 'Mode'),
    )
    #answer    = forms.CharField(label=("answer"),required=False)
    dataanalysis = forms.ChoiceField(choices=ANALYSIS_TYPES)


class AnswerSearchForm(forms.Form):
    # ANALYSIS_TYPES = (
    #     ('A', 'Mean'),
    #     ('R', 'Median'),
    #     ('C', 'Mode'),
    # )
    # answer = forms.ModelChoiceField(queryset=Answer.objects.none())
    # analysis = forms.ChoiceField(choices=ANALYSIS_TYPES)
    tag = forms.ModelChoiceField(queryset=Tag.objects.none())

    def __init__(self, *args, **kwargs):
        tree = kwargs.pop('tree')
        super(AnswerSearchForm, self).__init__(*args, **kwargs)
        # answers = \
        #     Answer.objects.filter(transitions__entries__session__tree=tree)
        tags = Tag.objects.filter(entries__session__tree=tree).distinct()
        
        # self.fields['answer'].queryset = answers.distinct()
        self.fields['tag'].queryset = tags
        # self.fields['analysis'].label = 'Calculator'
        # self.fields['tag'].label = 'Calculator'


class TagWidget(forms.TextInput):
    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, basestring):
            value = edit_string_for_tags(Tag.objects.filter(id__in=value))
        return super(TagWidget, self).render(name, value, attrs)


class TagField(forms.CharField):
    widget = TagWidget

    def clean(self, value):
        try:
            tag_names = parse_tags(value)
        except ValueError:
            raise forms.ValidationError(_("Please provide a comma-separated list of tags."))
        tags = []
        for tag_name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)
        return tags


class EntryTagForm(forms.ModelForm):
    tags = TagField()

    class Meta:
        model = Entry
        fields = ('tags',)


class PathForm(forms.ModelForm):
    tags = TagField(required=False)

    class Meta:
        model = Transition

    def __init__(self, *args, **kwargs):
        super(PathForm, self).__init__(*args, **kwargs)
        states = TreeState.objects.select_related('question')
        states = states.order_by('question__text')
        self.fields['current_state'].queryset = states
        self.fields['current_state'].label = 'Current State'
        self.fields['answer'].label = 'Answer'
        self.fields['answer'].queryset = Answer.objects.order_by('answer')
        self.fields['next_state'].label = 'Next State'
        self.fields['next_state'].queryset = states
        self.fields['tags'].label = 'Auto tags'


class TagForm(forms.ModelForm):
    
    class Meta:
        model = Tag

    def __init__(self, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)
        self.fields['recipients'] = forms.ModelMultipleChoiceField(
            queryset=Contact.objects.exclude(user__email=''),
            widget=forms.CheckboxSelectMultiple,
            required=False,
        )
