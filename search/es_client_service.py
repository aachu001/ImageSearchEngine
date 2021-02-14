from django.core.paginator import Paginator, Page

from elasticsearch import Elasticsearch, helpers
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.query import MultiMatch
from .fileUtils import readDataFromindexJson, fileExists

elasticIndex = "patentimgs"

# elastic-search paginator class
class eSearchPaginator(Paginator):
    """
    Override Django's built-in Paginator class to take in a count/total number of items;
    Elasticsearch provides the total as a part of the query results, so we can minimize hits.
    """
    def __init__(self, *args, **kwargs):
        super(eSearchPaginator, self).__init__(*args, **kwargs)
        self._count = self.object_list.hits.total.value
        self._number_pages = self._count//self.per_page
        self._page_range = list(range(1,self._number_pages+1))
        print(self._count)
        print(self._number_pages)
        print(self._page_range)

    def page(self, number):
        # this is overridden to prevent any slicing of the object_list - Elasticsearch has
        # returned the sliced data already.
        number = self.validate_number(number)
        self._number = number
        return Page(self.object_list, number, self) 

class esPaginator:
    def __init__(self, totalResults = 0, perPage=10):
        self.count = totalResults
        self.perPage = perPage
        self.num_pages = totalResults//perPage
        
        self.paginator = {
            'number' : 0,
            'count' : totalResults,
            'has_other_pages':False,
            'has_previous':False,
            'get_prev_page':0,
            'has_next':False,
            'get_next_page':0,
            'get_page_range':0,
            'num_pages' : 1,
        }
    def paginate(self, number):
        if self.count > self.perPage:
            self.paginator['has_other_pages'] = True
            self.paginator['has_previous'] = True if number > 1 else False
            self.paginator['has_next'] = True if number < (self.num_pages + 1) else False
            self.paginator['num_pages'] = self.count//self.perPage + 1
            self.paginator['get_page_range'] = list(range(1,self.paginator['num_pages']+1))
            if number in self.paginator['get_page_range']:
                self.paginator['number'] = number
                self.paginator['get_prev_page'] = number - 1
                self.paginator['get_next_page'] = number + 1
            else:
                self.paginator['number'] = 1
                self.paginator['get_prev_page'] = 1
                self.paginator['get_next_page'] = 1
            return self.paginator
        return self.paginator


#AutoComplete Feature
def autocomplete(q):
    spellCheckRequired = False
    client = Elasticsearch()
    s = Search(using=client, index=elasticIndex)
    query = s.suggest(
        'suggestions',
        q,
        term = {
            'field' : 'description'
        }
    )
    response = query.execute()
    print('--> ', response)
    search_query = response.suggest.suggestions[0].text
    suggestions = [txt.text for txt in response.suggest.suggestions[0].options]
    spell_check = suggestions[0]
    if len(suggestions) > 1:
        suggestions = suggestions[1:]
    print('--> ', search_query)
    if spell_check == search_query:
        print('--> No correction required.')
        spellCheckRequired = False
    else:
        print('--> Please Search related to : ',spell_check)
        spellCheckRequired = True
    print('--> ', suggestions)
    return {
        'query' : search_query,
        'suggestions': suggestions,
        'spell_check': spellCheckRequired,
        'spelling': spell_check
            }

# Index new Data
def eSearchIndexData(data):
    client = Elasticsearch()
    newPatent = {
        "patentID": data['img-patentID'],
        "pid": 'p-00'+data['img-figId'],
        "is_multiple": "0",
        "origreftext": "FIG. "+data['img-figId'],
        "figid": data['img-figId'], 
        "subfig": "", 
        "is_caption": "0", 
        "description": data['img-desc'], 
        "aspect": data['img-aspect'], 
        "object": data['img-obj']
    }
    response = client.index(
        index = elasticIndex,
        doc_type = '_doc',
        body = newPatent
    )
    print('--> ', response)
    if response['result'] == "created":
        print('--> created')
        return True
    else:
        return False

def eSearchUpdateIndex():
    return ''

def eSearchNormalRetrieve(searchTerm="", pageLowerLimit = 0, pageUpperLimit = 10, page=1):
    client = Elasticsearch()
    q = MultiMatch(query=searchTerm, 
                   fields=['patentID', 
                           'pid',
                           'origreftext',
                           'description',
                           'aspect', 
                           'object'],
                   fuzziness='AUTO')
    s = Search(using=client, index=elasticIndex).query(q)[pageLowerLimit:pageUpperLimit]
    response = s.execute()
    print('Total hits found : ', response.hits.total)
    totalResults = response.hits.total.value
    paginator = esPaginator(totalResults = totalResults, perPage = 10)
    posts = paginator.paginate(page)
    search=get_results(response)
    return totalResults, search, posts

def eSearchAdvancedRetrieve(imgPatentId="", imgDescription="", imgObject="", imgAspect="", pageLowerLimit = 0, pageUpperLimit = 10, page=1):
    client = Elasticsearch()
    q = Q("bool", 
          should=[
              Q("match", patentID={"query":imgPatentId, "fuzziness": "1"}),
              Q("match", description={"query":imgDescription, "fuzziness":"1"}),
              Q("match", object={"query":imgObject, "fuzziness":"1"}),
              Q("match", aspect={"query":imgAspect, "fuzziness":"1"}),
            ],
          minimum_should_match=1)
    s = Search(using=client, index=elasticIndex).query(q)[pageLowerLimit:pageUpperLimit]
    response = s.execute()
    print('Total hits found : ', response.hits.total)
    totalResults = response.hits.total.value
    paginator = esPaginator(totalResults = totalResults, perPage = 10)
    posts = paginator.paginate(page)
    search=get_results(response)
    return totalResults, search, posts

def eSearchRetrieveByID(idList = []):
    client = Elasticsearch()
    q = Q('ids',values=idList)
    s = Search(using=client, index=elasticIndex).query(q)
    response = s.execute()
    print('Total hits found : ', response.hits.total)
    search = get_results(response)
    #print(search)
    return search
    

def get_results(response):
    results=[]
    for hit in response:
        #print(hit.meta.id)
        imgPathDB = fileExists('dataset/images/'+hit['patentID']+'-D0'+hit['pid'][2:]+'.png', hit['pid'])
        result_tuple = (hit.meta.id, hit.patentID, hit.pid, hit.origreftext, hit.aspect, hit.object, imgPathDB, hit.description)
        #print(result_tuple)
        results.append(result_tuple)
    return results


def bulkUploadData():
    client = Elasticsearch()
    patentData = readDataFromindexJson(BULK_JSON_DATA_FILE)
    helpers.bulk(client, patentData, index=elasticIndex)
    

if __name__ == '__main__':
    print("Opal guy details: \n",eSearch(firstName="opal"))
    print("the first 20 Female gender details: \n", eSearch(gender="f"))