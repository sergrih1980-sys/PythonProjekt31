from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from . import views

urlpatterns = [
    # Главная страница (пустой путь)
    path("", views.home, name="home"),

    # Авторизация
    path("register/", views.register, name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Получатели
    path("recipients/", views.RecipientListView.as_view(), name="recipient-list"),
    path("recipients/new/", views.RecipientCreateView.as_view(), name="recipient-create"),
    path("recipients/<int:pk>/edit/", views.RecipientUpdateView.as_view(), name="recipient-edit"),
    path("recipients/<int:pk>/delete/", views.RecipientDeleteView.as_view(), name="recipient-delete"),

    # Сообщения
    path("messages/", views.MessageListView.as_view(), name="message-list"),
    path("messages/new/", views.MessageCreateView.as_view(), name="message-create"),
    path("messages/<int:pk>/edit/", views.MessageUpdateView.as_view(), name="message-edit"),
    path("messages/<int:pk>/delete/", views.MessageDeleteView.as_view(), name="message-delete"),

    # Рассылки
    path("mailings/", views.MailingListView.as_view(), name="mailing-list"),
    path("mailings/new/", views.MailingCreateView.as_view(), name="mailing-create"),
    path("mailings/<int:pk>/", views.MailingDetailView.as_view(), name="mailing-detail"),
    path("mailings/<int:pk>/edit/", views.MailingUpdateView.as_view(), name="mailing-edit"),
    path("mailings/<int:pk>/delete/", views.MailingDeleteView.as_view(), name="mailing-delete"),

    # Статистика
    path("stats/", views.user_stats, name="user-stats"),

    # Действия менеджеров
    path("block-user/<int:user_id>/", views.block_user, name="block_user"),
    path("disable-mailing/<int:mailing_id>/", views.disable_mailing, name="disable_mailing"),
]
