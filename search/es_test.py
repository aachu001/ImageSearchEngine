from django.core.paginator import Paginator, Page
from django.core.paginator import PageNotAnInteger, EmptyPage
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from .es_client_service import eSearchPaginator, esPaginator

def eSearch(firstName="", gender="", pageLowerLimit = 0, pageUpperLimit = 10, page=1):
    client = Elasticsearch()
    q = Q("bool", should=[Q("match", firstname=firstName),
                          Q("match", gender=gender)],
          minimum_should_match=1)
    s = Search(using=client, index="bank").query(q)[pageLowerLimit:pageUpperLimit]
    response = s.execute()
    print('Total hits found : ', response.hits.total)
    totalResults = response.hits.total.value
    #paginator = eSearchPaginator(response, per_page=10 )
    paginator = esPaginator(totalResults = totalResults, perPage = 10)
    posts = paginator.paginate(page)
    #     try:
    #         posts = paginator.page(page)
    #     except PageNotAnInteger:
    #         posts = paginator.page(1)
    #     except EmptyPage:
    #         posts = paginator.page(paginator.get_number_pages)
    # else:
    #    posts = paginator.page(1) 
    search=get_results(response)
    return totalResults, search, posts

def get_results(response):
    results=[]
    for hit in response:
        result_tuple = (hit.firstname + ' ' + hit.lastname, hit.email, hit.gender, hit.address)
        results.append(result_tuple)
    return results

if __name__ == '__main__':
    print("Opal guy details: \n",eSearch(firstName="opal"))
    print("the first 20 Female gender details: \n", eSearch(gender="f"))