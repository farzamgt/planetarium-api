from django.urls import reverse


REGISTER_URL = reverse("user:create")
LOGIN_URL = reverse("user:login")
ME_URL = reverse("user:manage")
