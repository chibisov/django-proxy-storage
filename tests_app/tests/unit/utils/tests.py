# -*- coding: utf-8 -*-
from django.test import TestCase

from proxy_storage import utils


class TestUtils(TestCase):
    def test_clean_path(self):
        experiments = [
            'file/hello.txt',
            '/file/hello.txt',
            'file/hello.txt/',
            '/file/hello.txt/',
            '///file/hello.txt///',
        ]

        for exp in experiments:
            self.assertEqual(utils.clean_path(exp), '/file/hello.txt')