from django.urls import path

from .views import (
    CallNextView,
    CallNumberView,
    CompleteView,
    PublicDisplayView,
    QueueView,
    UnexaminedView,
)

urlpatterns = [
    path("queue/", QueueView.as_view(), name="queue"),
    path("queue/call/<int:number>/", CallNumberView.as_view(), name="queue-call"),
    path("queue/unexamined/<int:number>/", UnexaminedView.as_view(), name="queue-unexamined"),
    path("queue/call-next/", CallNextView.as_view(), name="queue-call-next"),
    path("queue/complete/", CompleteView.as_view(), name="queue-complete"),
    path("queue/display/", PublicDisplayView.as_view(), name="queue-display"),
]
