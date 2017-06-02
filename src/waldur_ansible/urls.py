from . import views, models


def register_in(router):
    router.register(r'ansible-playbooks', views.PlaybookViewSet, base_name=models.Playbook.get_url_name())
