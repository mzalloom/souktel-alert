from django.contrib import admin

from goals import models as goals


class GoalAdmin(admin.ModelAdmin):
    list_display = ('id', 'connection', 'body', 'date_created',
                    'date_last_notified', 'active')
    list_filter = ('active', 'date_created', 'date_last_notified')
    search_fields = ('body',)
    ordering = ('-date_created',)
admin.site.register(goals.Goal, GoalAdmin)


class AnswerAdmin(admin.ModelAdmin):
    pass
admin.site.register(goals.Answer, AnswerAdmin)