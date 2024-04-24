from django.http import HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt

from app.helpers.phsaysImageCreator import phsays as phsaysLib

@csrf_exempt
def phsays(request : HttpRequest):
    
    if request.method == "POST":
        data = request.POST
        message = data.get("message")
        return HttpResponse(phsaysLib.getImage(message, "BONDSTORY_MINAMOTO_EDIT.ttf", "app/helpers/phsaysImageCreator"))
    else:
        return HttpResponse("Invalid Request Method.")