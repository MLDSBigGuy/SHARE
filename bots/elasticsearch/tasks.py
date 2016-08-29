import logging
import re

from django.apps import apps
from elasticsearch import helpers
from elasticsearch import Elasticsearch

from project import settings

from share.tasks import ProviderTask
from share.models import AbstractCreativeWork
from share.models import Entity
from share.models import Person
from share.models import Tag
from share.models import Subject

from bots.elasticsearch import util

logger = logging.getLogger(__name__)


def safe_substr(value, length=32000):
    if value:
        return str(value)[:length]
    return None


def score_text(text):
    return int(
        (len(re.findall('(?!\d)\w', text)) / (1 + len(re.findall('[\W\d]', text))))
        / (len(text) / 100)
    )


def add_suggest(obj):
    if obj['name']:
        obj['suggest'] = {
            'input': re.split('[\\s,]', obj['name']) + [obj['name']],
            'output': obj['name'],
            'payload': {
                'id': obj['id'],
                'name': obj['name'],
                'type': obj['type'],
            },
            'weight': score_text(obj['name'])
        }
    return obj


__shareuser_cache = {}
def sources(qs):
    sus = []
    for through in qs:
        if through.shareuser_id not in __shareuser_cache:
            __shareuser_cache[through.shareuser_id] = through.shareuser
        sus.append(__shareuser_cache[through.shareuser_id])
    return sus


class IndexModelTask(ProviderTask):

    def do_run(self, model_name, ids):
        es_client = Elasticsearch(settings.ELASTICSEARCH_URL, retry_on_timeout=True, timeout=30)
        model = apps.get_model('share', model_name)
        for resp in helpers.streaming_bulk(es_client, self.bulk_stream(model, ids)):
            logger.debug(resp)

    def bulk_stream(self, model, ids):
        opts = {'_index': settings.ELASTICSEARCH_INDEX, '_type': model.__name__.lower()}
        qs = model.objects.filter(id__in=ids)
        for inst in qs.all():
            # if inst.is_delete:  # TODO
            #     yield {'_id': inst.pk, '_op_type': 'delete', **opts}
            yield {'_id': inst.pk, '_op_type': 'index', **self.serialize(inst), **opts}

    def serialize(self, inst):
        return {
            AbstractCreativeWork: self.serialize_creative_work,
            Entity: self.serialize_entity,
            Person: self.serialize_person,
            Tag: self.serialize_tag,
            Subject: self.serialize_subject,
        }[type(inst)._meta.concrete_model](inst)

    def serialize_person(self, person, suggest=True):
        serialized_person = util.fetch_person(person.pk)
        return add_suggest(serialized_person) if suggest else serialized_person

    def serialize_entity(self, entity, suggest=True):
        serialized_entity = {
            'id': entity.pk,
            'type': type(entity).__name__.lower(),
            'name': safe_substr(entity.name),
            'url': entity.url,
            'location': safe_substr(entity.location),
        }
        return add_suggest(serialized_entity) if suggest else serialized_entity

    def serialize_tag(self, tag, suggest=True):
        serialized_tag = {
            'id': str(tag.pk),
            'type': 'tag',
            'name': safe_substr(tag.name),
        }
        return add_suggest(serialized_tag) if suggest else serialized_tag

    def serialize_subject(self, subject, suggest=True):
        serialized_subject = {
            'id': str(subject.pk),
            'type': 'subject',
            'name': safe_substr(subject.name),
        }
        return add_suggest(serialized_subject) if suggest else serialized_subject

    def serialize_link(self, link):
        return {
            'type': safe_substr(link.type),
            'url': safe_substr(link.url),
        }

    def serialize_creative_work(self, creative_work):
        return util.fetch_abstractcreativework(creative_work.pk)


class IndexSourceTask(ProviderTask):

    def do_run(self):
        es_client = Elasticsearch(settings.ELASTICSEARCH_URL, retry_on_timeout=True, timeout=30)
        for resp in helpers.streaming_bulk(es_client, self.bulk_stream()):
            logger.debug(resp)

    def bulk_stream(self):
        ShareUser = apps.get_model('share.ShareUser')
        opts = {'_index': settings.ELASTICSEARCH_INDEX, '_type': 'source'}
        for source in ShareUser.objects.exclude(robot='').exclude(long_title='').all():
            yield {'_op_type': 'index', '_id': source.robot, **self.serialize(source), **opts}

    def serialize(self, source):
        serialized_source = {
            'id': str(source.pk),
            'type': 'source',
            'name': safe_substr(source.long_title),
            'short_name': safe_substr(source.robot)
        }
        return add_suggest(serialized_source)
