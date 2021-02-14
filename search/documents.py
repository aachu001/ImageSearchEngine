from django_elasticsearch_dsl import DocType, Index
from .models import Figure_Details

patentImgs = Index('patentImages')
patentImgs.settings(number_of_shards=1, number_of_replicas=0)
@patentImgs.doc_type
class ImageDocument(DocType):
    class Meta:
        # The model associated with Elasticsearch document
        model = Figure_Details
        # The fields of the model you want to be indexed
        # in Elasticsearch
        fields = (
            'patentID',
            'pid',
            'is_multiple',
            'origreftext',
            'figid',
            'subfig',
            'is_caption',
            'description',
            'aspect',
            'object',
        )
