from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver 
from django.db.models.signals import post_save 
import json
#Custom utils
from .fileUtils import readDataFromindexJson, fileExists

BULK_JSON_DATA_FILE = './dataset/jsondata.json'

# Create your models here.
# User Profile
class Profile(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    # image details
    # -- elastic search document id
    e_doc_id = models.CharField(max_length=100, default=None)
    search_query = models.TextField(default=None)
    # products = models.ManyToManyField(Product)
    # @receiver(post_save, sender=User)
    # def create_user_profile(sender, instance, created, **kwargs):
    #     if created:
    #         Profile.objects.create(user=instance)
    
    # @receiver(post_save, sender=User)
    # def save_user_profile(sender, instance, **kwargs):
    #     instance.profile.save()
        
# figure_details
class Figure_Details(models.Model):
    patentID = models.CharField(max_length=50, default=None)
    pid = models.CharField(max_length=50, default=None)
    is_multiple = models.CharField(max_length=50, default=None)
    origreftext = models.CharField(max_length=50, default=None)
    figid = models.CharField(max_length=50, default=None)
    subfig = models.CharField(max_length=50, default=None)
    is_caption = models.CharField(max_length=50, default=None)
    description = models.CharField(max_length=50,default=None)
    aspect = models.CharField(max_length=50, default=None)
    object = models.CharField(max_length=50, default=None)
    imgPath = models.CharField(max_length=300, default='')
    createdBy = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    
    def __str__(self):
        return self.name
    
    @classmethod
    def populate(cls):
        cls.objects.all().delete()
        patentObjs = {}
        patentData = readDataFromindexJson(BULK_JSON_DATA_FILE)
        for i in range(1,len(patentData),2):
            tmp = json.loads(patentData[i])
            imgPathDB = fileExists('dataset/images/'+tmp['patentID']+'-D0'+tmp['pid'][2:]+'.png', tmp['pid'])
            patentObjs[i] = {
                'patentID':  tmp['patentID'],
                'pid': tmp['pid'],
                'is_multiple' : tmp['is_multiple'],
                'origreftext' : tmp['origreftext'],
                'figid' : tmp['figid'],
                'subfig' : tmp['subfig'],
                'is_caption' : tmp['is_caption'],
                'description' : tmp['description'],
                'aspect' : tmp['aspect'],
                'object' : tmp['object'],
                'imgPath': imgPathDB
            }
            #print('PatentId: ',test['patentID'], ', pid: ', test['pid'], ', fig-Path: ', imgPathDB)
        cls.objects.bulk_create([
            cls(
                patentID=doc['patentID'],
                pid=doc['pid'],
                is_multiple = doc['is_multiple'],
                origreftext = doc['origreftext'],
                figid = doc['figid'],
                subfig = doc['subfig'],
                is_caption = doc['is_caption'],
                description = doc['description'],
                aspect = doc['aspect'],
                object = doc['object'],
                imgPath=doc['imgPath'],
                createdBy=User.objects.get(id=1),
            )
            for doc in patentObjs.values()
        ])        