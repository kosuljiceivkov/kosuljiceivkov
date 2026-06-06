from django.http import JsonResponse


def health_check(request):
    """Render / load balancer health probe."""
    return JsonResponse({"status": "ok"})
