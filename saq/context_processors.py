from .constants import SAQUrls, PRETEST

def saq_urls(request):
    return {
        'SAQ': SAQUrls,
        'PRETEST': PRETEST
    }