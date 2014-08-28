# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db.models.aggregates import Count
from ordered_model.admin import OrderedModelAdmin
from .models import Question, Answer, Reply

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


class QuestionAdmin(OrderedModelAdmin):
    list_display = ('code', 'title', 'status', 'question_replies', 'updated_at', 'author', 'order', 'move_up_down_links')

    def get_queryset(self, request):
        return super(QuestionAdmin, self).get_queryset(request).annotate(replies_count=Count('reply'))

    def question_replies(self, obj):
        return obj.replies_count
    question_replies.short_description = 'Replies'
    question_replies.admin_order_field = 'replies_count'

    inlines = [
        AnswerInline,
    ]


class AnswerAdmin(OrderedModelAdmin):
    list_display = ('value', 'question', 'updated_at', 'order', 'move_up_down_links')


class ReplyAdmin(OrderedModelAdmin):
    list_display = ('counter', 'question', 'answer', 'replier', 'replied_at')


admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Reply, ReplyAdmin)
# admin.site.register(models.Threshold)