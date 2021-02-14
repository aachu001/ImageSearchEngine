from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth.forms import PasswordResetForm
from django.db.models.query_utils import Q
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils.html import escape, strip_tags

from search.models import Figure_Details, Profile

#reCAPTCHA decorator
from .decorators import validate_recaptcha

#Elastic Search Utils
from .es_test import eSearch
from .es_client_service import eSearchNormalRetrieve, eSearchAdvancedRetrieve, eSearchIndexData, eSearchPaginator, eSearchRetrieveByID, autocomplete

#Py Utils
import mimetypes
import json
# Create your views here.

UserModel = get_user_model()
from .forms import SignUpForm, UserForm, ProfileForm

#signup
@validate_recaptcha
def signup(request):
    context = {}
    form = SignUpForm(request.POST or None)
    if request.method == "POST":
        if User.objects.filter(email=request.POST['email']).exists():
            messages.error(request, "Unsuccessful registration, Email Already Exists. Please use a different email." )
        elif not request.recaptcha_is_valid:
            print('Signup Page: Invalid Captcha...')
        elif form.is_valid() and request.recaptcha_is_valid:
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            sendActivationEmail(request, user, form)
            #login(request, user)
            #messages.success(request, "Please confirm your email address to complete the registration" )
            return render(request, 'accounts/register_account.html',context={'user':user, 'siteKey':settings.GOOGLE_RECAPTCHA_SITE_KEY})
        messages.error(request, "Unsuccessful registration, Invalid Information." )
    context['signup_form']=form
    context['siteKey'] = settings.GOOGLE_RECAPTCHA_SITE_KEY
    return render(request,'accounts/signup.html',context)

#--- https://www.ordinarycoders.com/blog/article/django-user-register-login-logout
#--- https://www.ordinarycoders.com/blog/article/django-password-reset
def sendActivationEmail(request, user, form):
    current_site = get_current_site(request)
    mail_subject = 'Activate your Eye of Sauron account.'
    message = render_to_string('accounts/account_activation.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
    })
    to_email = form.cleaned_data.get('email')
    email = EmailMessage(
                mail_subject, message, to=[to_email]
    )
    email.send()

# activate
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        print(user)
        print(default_token_generator.check_token(user, token))
        return HttpResponse('Activation link is invalid!')

#login
@validate_recaptcha
def login_c(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid() and request.recaptcha_is_valid:
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if not user.is_active:
                messages.error(request, "You are not a registered user. Please confirm the email before login")
            elif user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect('index')
            else:
                messages.error(request,"Invalid username or password.")
        elif not request.recaptcha_is_valid:
            #messages.error(request,"Invalid")
            print('Invalid Captcha....')
        else:
            messages.error(request,"Invalid Details.")
    form = AuthenticationForm()
    return render(request=request, template_name="accounts/login.html", context={"login_form":form,"siteKey":settings.GOOGLE_RECAPTCHA_SITE_KEY})

def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.") 
	return redirect("index")

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts/profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'passwords/password_change.html', {
        'form': form
    })

def password_reset_request(request):
	if request.method == "POST":
		password_reset_form = PasswordResetForm(request.POST)
		if password_reset_form.is_valid():
			data = password_reset_form.cleaned_data['email']
			associated_users = User.objects.filter(Q(email=data))
			if associated_users.exists():
				for user in associated_users:
					subject = "Eye of Sauron | Password Reset Requested"
					email_template_name = "passwords/password_reset_email.html"
					c = {
					"email":user.email,
					'domain':get_current_site(request).domain,
					'site_name': 'Website',
					"uid": urlsafe_base64_encode(force_bytes(user.pk)),
					"user": user,
					'token': default_token_generator.make_token(user),
					'protocol': 'http',
					}
					email = render_to_string(email_template_name, c)
					try:
						send_mail(subject, email, None , [user.email], fail_silently=False)
					except BadHeaderError:
						return HttpResponse('Invalid header found.')
					return redirect ("/password_reset/done/")
	password_reset_form = PasswordResetForm()
	return render(request=request, template_name="passwords/password_reset.html", context={"password_reset_form":password_reset_form})

#index
@login_required
def index(request):
    return render(request,'search/home.html')

#Test Elastic Search
@login_required
def etest(request):
    results=[]
    name_term=""
    gender_term=""
    if request.method == 'POST':
        if request.POST.get('name') and request.POST.get('gender'):
            #print("--> Both name and gender found")
            name_term=request.POST['name']
            gender_term=request.POST['gender']
        elif request.POST.get('name'):
            #print("--> Name found")
            name_term=request.POST['name']
        elif request.POST.get('gender'):
            #print("--> Gender found")
            gender_term=request.POST['gender']
        # -- pagination
        page = 1
    if request.method == 'GET':
        if request.GET.get('name') and request.GET.get('gender'):
            #print("--> Both name and gender found")
            name_term=request.GET['name']
            gender_term=request.GET['gender']
        elif request.GET.get('name'):
            #print("--> Name found")
            name_term=request.GET['name']
        elif request.GET.get('gender'):
            #print("--> Gender found")
            gender_term=request.GET['gender']
        # -- pagination
        page = int(request.GET.get('page', '1'))
    start = (page-1) * 10
    end = start + 10
    search_term = name_term or gender_term
    search_query = {
        'name' : name_term,
        'gender' : gender_term
    }
    print(request.POST)
    total, results, posts = eSearch(firstName=name_term, gender=gender_term, pageLowerLimit=start, pageUpperLimit=end, page=page)
    # settings.POSTS_PER_PAGE
    print('--> ',posts)   
    context={
        'results': results,
        'paginator': posts,
        'count': total,
        'search_term': search_term,
        'query' : search_query
    }
    return render(request,'search/etest.html', context=context)

#advanced search
@login_required
def advanced_search(request):
    results=[]
    imgPatentID=""
    imgDescription=""
    imgObject=""
    imgAspect=""
    if request.method == "POST":
        if request.POST.get('img-patentID'):
            imgPatentID=request.POST['img-patentID']
            imgPatentID = escape(strip_tags(escape(imgPatentID))) # XSS
        if request.POST.get('img-desc'):
            imgDescription=request.POST['img-desc']
            imgDescription = escape(strip_tags(escape(imgDescription))) # XSS
        if request.POST.get('img-obj'):
            imgObject=request.POST['img-obj']
            imgObject = escape(strip_tags(escape(imgObject))) # XSS
        if request.POST.get('img-aspect'):
            imgAspect=request.POST['img-aspect']
            imgAspect = escape(strip_tags(escape(imgAspect))) # XSS
        print(request.POST.keys())
        #--- pagination
        page = 1
    elif request.method == 'GET':
        if request.GET.get('patentID'):
            imgPatentID=request.GET['patentID']
            imgPatentID = escape(strip_tags(escape(imgPatentID))) # XSS
        if request.GET.get('desc'):
            imgDescription=request.GET['desc']
            imgDescription = escape(strip_tags(escape(imgDescription))) # XSS
        if request.GET.get('obj'):
            imgObject=request.GET['obj']
            imgObject = escape(strip_tags(escape(imgObject))) # XSS
        if request.GET.get('aspect'):
            imgAspect=request.GET['aspect']
            imgAspect = escape(strip_tags(escape(imgAspect))) # XSS
        #--- pagination
        page = int(request.GET.get('page', '1'))
    search_term = imgPatentID or imgDescription or imgObject or imgAspect
    print('--> Search Term: ',search_term)
    start = (page-1) * 10
    end = start + 10
    search_query = {
        'patentID': imgPatentID,
        'desc':imgDescription,
        'obj':imgObject,
        'aspect':imgAspect,
    }
    #retrieve results from elastic search
    total, results, paginate = eSearchAdvancedRetrieve(imgPatentID, imgDescription, imgObject, imgAspect, pageLowerLimit = start, pageUpperLimit = end, page=page)
    context = {
        'results': results,
        'paginator': paginate,
        'count': total,
        'search_term': search_term,
        'query' : search_query
    }
    return render(request,'search/advanced.html', context=context)

#advanced search
@login_required
def search(request):
    results=[]
    search_term=""
    page=1
    print(request.POST)
    if request.method == "POST":
        if request.POST.get('e_doc_id'):
            print('Building in progress....')
            elastic_id = request.POST.get('e_doc_id')
            messages.success(request, 'item: '+elastic_id+' saved to your profile')
            return redirect()
        else:
            search_term = request.POST['img-search-string']
            search_term = escape(strip_tags(escape(search_term))) # XSS script
            # -- pagination
            page = 1
    if request.method == 'GET':
        if request.GET.get('q'):
            #print("--> Both name and gender found")
            search_term=request.GET['q']
            search_term = escape(strip_tags(escape(search_term))) # XSS script
            # -- pagination
            page = int(request.GET.get('page', '1'))
    print('--> Search Term: ',search_term)
    start = (page-1) * 10
    end = start + 10
    search_query = {
        'q': search_term
    }
    total, results, paginate = eSearchNormalRetrieve(search_term, pageLowerLimit = start, pageUpperLimit = end, page=page)
    context = {
        'results': results,
        'paginator': paginate,
        'count': total,
        'search_term': search_term,
        'query' : search_query
    }
    return render(request,'search/search.html', context=context)


# save History AJAX query
#@login_required
def saveHistory(request):
    if request.method == "POST":
        #print('Building in progress....')
        query = {}
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        elastic_id = data.get('e_doc_id')
        search_query = data.get('query')
        #search_query = json.loads(str(search_query))
        if len(search_query) > 2:
            query['type'] = search_query.get('type')
            query['patentID'] = search_query.get('patentID')
            query['obj'] = search_query.get('obj')
            query['aspect'] = search_query.get('aspect')
            query['desc'] = search_query.get('desc')
        else:
            query['type'] = search_query.get('type')
            query['q'] = search_query.get('q')
        print(query)
        if Profile.objects.filter(user_id=request.user.id, e_doc_id = elastic_id).exists():
            return JsonResponse({'job':'fail', 'message' : 'item id: `'+elastic_id+'` already exists in your favourite list'})
        p = Profile(user_id=request.user, e_doc_id = elastic_id, search_query = search_query)
        p.save()
        #messages.success(request, 'item: '+elastic_id+' saved to your profile')
    return JsonResponse({ 'job':'success', 'message' : 'item id: `'+elastic_id+'` saved to your favourite list' })


def getAutocompleteList(request):
    if request.method == "POST":
        query = {}
        data = json.loads(request.body.decode("utf-8"))
        search_query = data.get('query')
        autocomplete(search_query)
    return JsonResponse({ 'job':'success'})

def removeItemFromProfile(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        print(data)
        elastic_id = data.get('e_doc_id')
        if not len(elastic_id) > 0:
            return JsonResponse({'job':'fail', 'message' : 'No item id: `'+elastic_id+'` mentioned in your favourite list'})
        if not Profile.objects.filter(user_id=request.user.id, e_doc_id = elastic_id).exists():
            return JsonResponse({'job':'fail', 'message' : 'item id: `'+elastic_id+'` does not exist in your favourite list'})
        p = Profile.objects.filter(user_id=request.user, e_doc_id = elastic_id).delete()
        print(p)
        if not p[0] >= 1 :
            return JsonResponse({'job':'fail', 'message' : 'error removing item id: `'+elastic_id+'` from your favourite list'})
    return JsonResponse({ 'job':'success', 'message' : 'item id: `'+elastic_id+'` removed from your favourite list' })

def checkFiletype(fileName):
    mimetypes.init()
    mimestart = mimetypes.guess_type(fileName)[0]
    if mimestart != None:
        mimestart = mimestart.split('/')[0]
        if mimestart == 'image':
            return True
        return False

#index new data
@login_required
def indexData(request):
    index = False
    if request.method == 'POST':
        imgfile = request.FILES['img-file']
        if checkFiletype(imgfile.name):
            fs = FileSystemStorage(location=settings.IMAGE_DATA_ROOT)
            imgName = request.POST['img-patentID']+'-D000'+request.POST['img-figId']+'.png'
            filename = fs.save(imgName, imgfile)
            if eSearchIndexData(request.POST):
                index = True
                messages.info(request, "Data successfully indexed.") 
            else:
                messages.error(request, "Error in indexing data.")
        else:
            messages.error(request, "Please upload only an image file. ('png','jpeg','jpg')")
    context = {
        'index' : index
    }
    return render(request,'search/newImagePatent.html', context=context)

#profile
@login_required
def getProfileDetails(request):
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        #profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid():
            user_form.save()
            messages.success(request,('Your profile was successfully updated!'))
        elif profile_form.is_valid():
            #profile_form.save()
            messages.success(request,('Your wishlist was successfully updated!'))
        else:
            messages.error(request,('Unable to complete request'))
        return redirect ("/accounts/profile")
    user_form = UserForm(instance=request.user)
    idsList = list(Profile.objects.filter(user_id = request.user.id).values_list('e_doc_id', flat=True))
    recent_searches = list(Profile.objects.filter(user_id=request.user.id).values_list('search_query',flat=True))
    recent_searches = [json.loads(query.replace('\'','"')) for query in recent_searches]
    recent_searches.reverse()
    print(recent_searches[0])
    profile_items = eSearchRetrieveByID(idsList)
    #profile_form = ProfileForm(instance=request.user.profile)
    return render(request=request, template_name="accounts/profile.html", context={"user":request.user, "user_form":user_form, "profile_items":profile_items, "recent":recent_searches[0:5] })
    #return render(request,'accounts/profile.html',context={})
