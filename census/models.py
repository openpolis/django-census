# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models.aggregates import Count
from django.dispatch import Signal
from django.utils.translation import ugettext_lazy as _
from ordered_model.models import OrderedModel

USER_MODEL = settings.AUTH_USER_MODEL

question_status_changed = Signal(providing_args=["old_status"])
question_reply = Signal(providing_args=["reply"])


class QuestionException(Exception):
    pass

class QuestionReplyException(QuestionException):
    pass


class QuestionManager(models.Manager):

    @staticmethod
    def set_status(question, new_status, save=True):
        """
        Changes the status of a question.
        :param question: Question
        :param new_status: draft|published|completed|archived
        :return: Question
        """
        old_status, question.status = question.status, new_status
        if save:
            question.save()
        question_status_changed.send_robust(sender=question, old_status=old_status)
        return question

    @classmethod
    def publish(cls, question):
        return cls.set_status(question, Question.STATUS_PUBLISHED)

    @classmethod
    def complete(cls, question):
        return cls.set_status(question, Question.STATUS_COMPLETED)

    @classmethod
    def archive(cls, question):
        return cls.set_status(question, Question.STATUS_ARCHIVED)

    @staticmethod
    def reply(question, user, answer=None, text='', safe_error=False):
        """
        :raises QuestionReplyException
        """
        try:
            with transaction.atomic():

                # check if user has already replied to this question
                if question.reply_set.filter(replier=user).exists():
                    raise QuestionReplyException(_('User "{replier}" already replied to "{question}"'.format(
                        replier=user, question=question)))
                # check if question is ready to be replied
                if question.status != Question.STATUS_PUBLISHED:
                    raise QuestionReplyException(_('Question "{question}" is not {status_label}'.format(
                        question=question, status_label=Question.STATUS_PUBLISHED_LABEL)))
                # check if is valid answer
                if answer:
                    if not isinstance(answer, Answer):
                        answer = question.answer_set.get(value=answer)
                    elif answer not in question.answer_set.all():
                        raise QuestionReplyException(_('Invalid answer "{answer}" for question "{question}"'.format(
                            answer=answer, question=question)))

                # create new reply
                new_reply = Reply.objects.create(
                    question=question,
                    replier=user,
                    answer=answer,
                    text=text
                )

                question_reply.send_robust(question, reply=new_reply)

                return new_reply

        except (QuestionReplyException, Answer.DoesNotExist):
            if not safe_error:
                raise


class Question(OrderedModel):

    code = models.SlugField(_('Code'), max_length=512, unique=True, db_index=True)

    STATUS_SET = (STATUS_DRAFT, STATUS_DRAFT_LABEL), \
                 (STATUS_PUBLISHED, STATUS_PUBLISHED_LABEL), \
                 (STATUS_COMPLETED, STATUS_COMPLETED_LABEL), \
                 (STATUS_ARCHIVED, STATUS_ARCHIVED_LABEL) = (
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('completed', _('Completed')),
        ('archived', _('Archived'))
    )
    STATUS_DICT = dict(STATUS_SET)
    PUBLIC_STATUS_SET = (STATUS_PUBLISHED, STATUS_COMPLETED)
    NOT_PUBLIC_STATUS_SET = (STATUS_DRAFT, STATUS_ARCHIVED)
    status = models.CharField(_('Current status'), choices=STATUS_SET, default=STATUS_DRAFT, max_length=10)

    TYPE_SET = (TYPE_TEXT, TYPE_TEXT_LABEL), \
               (TYPE_SINGLE_CHOICE, TYPE_SINGLE_CHOICE_LABEL), \
               (TYPE_MULTIPLE_CHOICE, TYPE_MULTIPLE_CHOICE_LABEL) = (
        ('text', _('Sign question')),
        ('single', _('Single-choice question')),
        ('multi', _('Multi-choice question'))
    )
    TYPE_DICT = dict(TYPE_SET)
    question_type = models.CharField(_('Question type'), choices=TYPE_SET, default=TYPE_SINGLE_CHOICE, max_length=10)

    title = models.CharField(_('Title'), max_length=512)
    description = models.TextField(_('Description'), blank=True)
    short_description = models.TextField(_('Short description'), max_length=1024, blank=True)

    # Timestamping fields
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True, editable=False)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True, editable=False)
    published_at = models.DateTimeField(_('Published at'), blank=True, null=True)
    completed_at = models.DateTimeField(_('Completed at'), blank=True, null=True)
    archived_at = models.DateTimeField(_('Archived at'), blank=True, null=True)

    # External relations
    author = models.ForeignKey(USER_MODEL, related_name='owned_question_set')

    objects = QuestionManager()

    def set_status(self, new_status):
        return Question.objects.set_status(self, new_status)

    def publish(self):
        return Question.objects.publish(self)

    def complete(self):
        return Question.objects.complete(self)

    def archive(self):
        return Question.objects.archive(self)

    def reply(self, user, answer=None, text=''):
        return Question.objects.reply(self, user, answer, text)

    class Meta(OrderedModel.Meta):
        verbose_name = _('question')
        verbose_name_plural = _('questions')
        get_latest_by = 'updated_at'

    def __unicode__(self):
        return self.code


class Answer(OrderedModel):
    """
    Choice for a Question.
    """
    value = models.SlugField(max_length=512)
    text = models.TextField(_('Text'))

    updated_at = models.DateTimeField(_('Updated at'), auto_now=True, editable=False)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True, editable=False)

    # External relations
    question = models.ForeignKey(Question, verbose_name=_('question'))

    class Meta(OrderedModel.Meta):
        verbose_name = _('answer')
        verbose_name_plural = _('answers')
        unique_together = (('question', 'value'), )
        order_with_respect_to = 'question'

    def __unicode__(self):
        return "%s:%s" % (self.question.code, self.value)


class Reply(OrderedModel):
    """
    User selected Answer about a Question.
    """
    text = models.TextField(_('Reply text'), blank=True)

    # Timestamping fields
    replied_at = models.DateTimeField(_('Replied at'), auto_now_add=True, editable=False)

    # External relations
    answer = models.ForeignKey(Answer, null=True, blank=True)
    question = models.ForeignKey(Question)
    replier = models.ForeignKey(USER_MODEL)

    @property
    def counter(self):
        return self.order + 1

    class Meta(OrderedModel.Meta):
        verbose_name = _('reply')
        verbose_name_plural = _('replies')
        get_latest_by = 'replied_at'
        unique_together = (('question', 'replier'), )

    def __unicode__(self):
        return "%s:%s" % (self.answer, self.replier)
