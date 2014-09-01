#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_django-census
------------

Tests for `django-census` models module.
"""

from django.contrib.auth.models import User
from census.models import Question, Reply, QuestionReplyException, question_reply, question_status_changed
from django.test import TestCase


class TestCensus(TestCase):

    def setUp(self):
        # Before performing any tests, create new users
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        self.member = User.objects.create_user('member', 'member@example.com', 'member')

    def tearDown(self):
        pass

    def test_question_status_steps(self):
        q = Question.objects.create(
            code='status-tests',
            title='Test statuses',
            author=self.admin
        )

        self.assertEqual(q.status, Question.STATUS_DRAFT)

        q.publish()
        self.assertEqual(q.status, Question.STATUS_PUBLISHED)

        q.complete()
        self.assertEqual(q.status, Question.STATUS_COMPLETED)

        q.archive()
        self.assertEqual(q.status, Question.STATUS_ARCHIVED)

    def _status_changed_receiver(self, sender, old_status, **kwargs):
        self.assertIn(old_status, Question.STATUS_DICT.keys())
        self.assertFalse(sender.status != old_status)

    def test_question_status_changed_signal(self):
        question_status_changed.connect(self._status_changed_receiver)

        self.test_question_status_steps()

        question_status_changed.disconnect(self._status_changed_receiver)

    def test_question_user_reply(self):
        q = Question.objects.create(
            code='reply-tests',
            title='Test reply',
            author=self.admin
        )
        self.assertEqual(q.reply_set.count(), 0)

        # should raise an exception for un-published question reply
        with self.assertRaises(QuestionReplyException):
            q.reply(self.admin, text='My reply')

        self.assertEqual(q.reply_set.count(), 0)

        q.publish()

        r = q.reply(self.admin, text='My reply')

        self.assertTrue(isinstance(r, Reply))
        self.assertEqual(q.reply_set.count(), 1)

        # should raise an exception for multiple reply to same question
        with self.assertRaises(QuestionReplyException):
            q.reply(self.admin, text='My Re-reply')

        for action in ('complete', 'archive'):
            getattr(q, action)()
            # should raise an exception if question is not in published status
            with self.assertRaises(QuestionReplyException):
                q.reply(self.member, text='User reply')

        q.publish()
        q.reply(self.member, text='User reply')

        self.assertEqual(q.reply_set.count(), 2)

    def _user_reply_receiver(self, sender, reply, **kwargs):
        self.assertEqual(sender.status, Question.STATUS_PUBLISHED)
        self.assertEqual(sender, reply.question)

    def test_question_user_reply_signal(self):

        question_reply.connect(self._user_reply_receiver)

        self.test_question_user_reply()

        question_reply.disconnect(self._user_reply_receiver)

