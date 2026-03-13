from apify_client import ApifyClientAsync

from api.settings import settings

apify_client = ApifyClientAsync(token=settings.APIFY_API_TOKEN)
