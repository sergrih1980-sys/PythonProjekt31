from time import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.views.decorators.cache import cache_page
from .models import Recipient, Message, Mailing, MailingAttempt, UserProfile
from .forms import MailingForm, MessageForm, RecipientForm, CustomUserCreationForm
from django.contrib.auth.models import User


# --- Базовые классы для ограничения доступа (владелец либо is_staff) ---
class OwnerListView(ListView):
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(creator=self.request.user)


class OwnerDetailView(DetailView):
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(creator=self.request.user)



def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # ждём подтверждения (в прод — письмо с токеном)
            user.save()
            UserProfile.objects.create(user=user, is_email_confirmed=False)
            messages.success(request, "Аккаунт создан. Администратор активирует его.")
            return redirect("login")
    else:
        form = CustomUserCreationForm()
    return render(request, "mailer/register.html", {"form": form})


# --- CRUD: Получатели (Recipient) ---
class RecipientListView(OwnerListView):
    model = Recipient
    template_name = "mailer/recipient_list.html"
    context_object_name = "recipients"


class RecipientCreateView(CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailer/recipient_form.html"
    success_url = reverse_lazy("recipient-list")


class RecipientUpdateView(UpdateView):
    model = Recipient
    form_class = RecipientForm
    template_name = "mailer/recipient_form.html"
    success_url = reverse_lazy("recipient-list")


class RecipientDeleteView(DeleteView):
    model = Recipient
    template_name = "mailer/recipient_confirm_delete.html"
    success_url = reverse_lazy("recipient-list")


# --- CRUD: Сообщения (Message) ---
class MessageListView(OwnerListView):
    model = Message
    template_name = "mailer/message_list.html"
    context_object_name = "messages"


class MessageCreateView(CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailer/message_form.html"
    success_url = reverse_lazy("message-list")


class MessageUpdateView(UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailer/message_form.html"
    success_url = reverse_lazy("message-list")


class MessageDeleteView(DeleteView):
    model = Message
    template_name = "mailer/message_confirm_delete.html"
    success_url = reverse_lazy("message-list")


# --- CRUD: Рассылки (Mailing) ---
class MailingListView(OwnerListView):
    model = Mailing
    template_name = "mailer/mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 10


class MailingDetailView(OwnerDetailView):
    model = Mailing
    template_name = "mailer/mailing_detail.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(CreateView):
    form_class = MailingForm
    template_name = "mailer/mailing_form.html"
    success_url = reverse_lazy("mailing-list")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.creator = self.request.user
        obj.save()
        form.save_m2m()  # сохраняем ManyToMany (получатели)
        messages.success(self.request, "Рассылка создана.")
        return redirect(self.success_url)


class MailingUpdateView(UpdateView):
    form_class = MailingForm
    template_name = "mailer/mailing_form.html"
    success_url = reverse_lazy("mailing-list")

    def form_valid(self, form):
        # Если пользователь не менеджер — нельзя менять creator (защита от подмены)
        if not self.request.user.is_staff:
            form.instance.creator = self.request.user
        return super().form_valid(form)


class MailingDeleteView(DeleteView):
    model = Mailing
    template_name = "mailer/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing-list")


# --- Действия менеджеров ---
@login_required
def block_user(request, user_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Доступ запрещён: только для менеджеров.")
    target = get_object_or_404(User, pk=user_id)
    target.is_active = not target.is_active
    target.save()
    messages.info(request, f"Пользователь {target.username} {'заблокирован' if not target.is_active else 'разблокирован'}.")
    return redirect("admin:auth_user_changelist")


@login_required
def disable_mailing(request, mailing_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Доступ запрещён: только для менеджеров.")
    mailing = get_object_or_404(Mailing, pk=mailing_id)
    mailing.status = Mailing.STATUS_COMPLETED
    mailing.save()
    messages.warning(request, "Рассылка принудительно отключена.")
    return redirect("mailing-detail", pk=mailing.pk)


# --- Статистика (для пользователя) ---
@login_required
def user_stats(request):
    mailings = Mailing.objects.filter(creator=request.user)
    attempts = MailingAttempt.objects.filter(mailing__in=mailings)

    total_attempts = attempts.count()
    success_count = attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count()
    failed_count = total_attempts - success_count
    total_messages = attempts.values("recipient").distinct().count()

    context = {
        "total_attempts": total_attempts,
        "success_count": success_count,
        "failed_count": failed_count,
        "total_messages": total_messages,
    }
    return render(request, "mailer/user_stats.html", context)

def home(request):
    if request.user.is_authenticated:
        return redirect("mailing-list")
    return render(request, "mailer/home.html")


@cache_page(60 * 5)  # 5 минут
@login_required
def dashboard(request):
    total_mailings = Mailing.objects.count()
    now = timezone.now()
    active_mailings = Mailing.objects.filter(
        start_time__lte=now,
        end_time__gte=now,
    ).count()
    total_recipients = Recipient.objects.count()

    context = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "total_recipients": total_recipients,
    }
    return render(request, "mailer/dashboard.html", context)
