from django.core.files import File
from wagtail.wagtailimages.models import get_image_model

__author__ = 'brett@codigious.com'

import glob
import codecs
import re
import filecmp
from io import StringIO, BytesIO
from optparse import make_option
import datetime
from faker import Faker
import yaml, yaml.parser
import markdown
import random

from django.contrib.auth.models import User

from wagtail.wagtailcore.models import Site

from django.core.management.base import BaseCommand, CommandError
from core.models import *

# <embed alt="urn" embedtype="image" format="right" id="1"/>


class ImageImporter(object):

    ImageModel = get_image_model()
    image_instance = ImageModel()

    def __init__(self, path, owner):
        self.library_path = path
        self.owner = owner
        #self.stdout = stdout
        #self.stderr = stderr
        self.results = {'total': 0,
                        'unchanged': 0,
                        'altered': 0,
                        'inserted': 0}

    def increment_stat(self, stat):
        self.results[stat] += 1

    def import_images(self):
        self.add_images_to_library(self.library_path)

    def add_file(self, path):
        basename = os.path.basename(path)

        image = self.ImageModel(uploaded_by_user=self.owner)

        with open(path, 'rb') as image_file:
            image.file.save(basename, File(image_file), save=True)

        image.title = basename
        image.save()
        return image

    def update_file(self, path):
        basename = os.path.basename(path)
        image = self.get_image_record(path)
        os.remove(image.file.path)
        with open(path, 'rb') as image_file:
            image.file.save(basename, File(image_file), save=True)
        image.save()
        return image

    def is_duplicate_name(self, path):
        file_name = self.image_instance.get_upload_to(os.path.basename(path))
        image_query = self.ImageModel.objects.filter(file=file_name)
        return image_query.exists()

    def get_image_record(self, path):
        file_name = self.image_instance.get_upload_to(os.path.basename(path))
        image = self.ImageModel.objects.get(file=file_name)
        return image

    def is_duplicate_image(self, path):
        image = self.get_image_record(path)
        return filecmp.cmp(image.file.path, path)

    def add_images_to_library(self, path):

        for path in [os.path.join(path, p) for p in os.listdir(path)]:
            if os.path.isdir(path):
                self.add_images_to_library(path)
            elif os.path.isfile(path):
                self.increment_stat('total')
                if self.is_duplicate_name(path):
                    if self.is_duplicate_image(path):
                        #self.stdout.write("Unchanged: {0} (skipped)".format(path))
                        self.increment_stat('unchanged')
                    else:
                        image = self.update_file(path)
                        #self.stdout.write("Updated: {0} (updating image, retaining id {1})".format(path, image.id))
                        self.increment_stat('altered')
                else:
                    self.stdout.write("Adding new image {0}".format(path))
                    #self.add_file(path)
                    self.increment_stat('inserted')

    def get_results(self):
        return self.results



class Command(BaseCommand):
    args = '<content directory>'
    help = 'Creates content from markdown and yaml files, found in <content directory>/pages'

    option_list = BaseCommand.option_list + (
        make_option('--content', dest='content_path', type='string', ),
        make_option('--owner', dest='owner', type='string'),
    )

    def handle(self, *args, **options):

        if not options['content_path']:
            raise CommandError("Pass --content <content dir>, where <content dir>/image-library contains images")

        if not options['owner']:
            raise CommandError("Pass --owner <username>, where <username> will be the content owner")

        path = options['content_path']
        if not os.path.isdir(path):
            raise CommandError("Content dir '{0}' does not exist or is not a directory".format(path))

        content_path = os.path.join(path, 'image-library')
        if not os.path.isdir(content_path):
            raise CommandError("Could not find image library '{0}'".format(content_path))

        try:
            owner = User.objects.get(username=options['owner'])
        except User.DoesNotExist:
            raise CommandError("Owner with username '{0}' does not exist".format(options['owner']))

        importer = ImageImporter(path=content_path, owner=owner, stdout=self.stdout, stderr=self.stderr)
        importer.import_images()
        results = importer.get_results()
        print "Total: {0}, unchanged: {1}, replaced: {2}, new: {3}".format(results['total'],
                                                                           results['unchanged'],
                                                                           results['altered'],
                                                                           results['inserted'])


