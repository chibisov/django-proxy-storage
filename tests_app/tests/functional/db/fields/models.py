# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

from proxy_storage.db.fields import ProxyStorageFileField


class SurveyAnswer(models.Model):
    user = models.ForeignKey(User)
    resume = ProxyStorageFileField(upload_to='proxy/', null=True)

    class Meta:
        app_label = 'tests_app'