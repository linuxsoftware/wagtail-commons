__author__ = 'brett@codigious.com'

import glob
import codecs
import re
from io import StringIO, BytesIO
from optparse import make_option
import datetime
from faker import Faker
import yaml, yaml.parser
import markdown
import random

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.contrib.contenttypes.models import ContentType

from wagtail.wagtailcore.models import Site

from django.core.management.base import BaseCommand, CommandError
from core.models import *


class Command(BaseCommand):
    args = '<content directory>'
    help = 'Create users, found in <content directory>/users.yml'

    option_list = BaseCommand.option_list + (
        make_option('--content', dest='content_path', type='string', ),
    )

    def handle(self, *args, **options):

        if not options['content_path']:
            raise CommandError("Pass --content <content dir>, where <content dir>/users.yml contains users")

        path = options['content_path']
        if not os.path.isdir(path):
            raise CommandError("Content dir '{0}' does not exist or is not a directory".format(path))

        content_path = os.path.join(path, 'users.yml')
        if not os.path.isfile(content_path):
            raise CommandError("Could not find file '{0}'".format(content_path))

        f = codecs.open(content_path, encoding='utf-8')
        stream = yaml.load_all(f)
        users = stream.next()
        f.close()

        for user in users:
            try:
                u = User.objects.create(username=user['username'],
                                        email=user['email'],
                                        first_name=user['first_name'],
                                        last_name=user['last_name'],
                                        is_superuser=user['is_superuser'])
                u.set_password(user['password'])
                u.save()
                self.stdout.write("Created {0}".format(user['username']))
            except IntegrityError:
                self.stderr.write("Could not create {0}, already exists?".format(user['username']))