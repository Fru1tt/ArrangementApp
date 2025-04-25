from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.event_list, name='home'),
    path('create/', views.create_event, name='create_event'),
    path('my-events/', views.my_events, name='my_events'),
    path('login/', auth_views.LoginView.as_view(template_name='ETA/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/edit/', views.event_edit, name='event_edit'),

    path('friends/', views.friend_page, name='friend_page'),
    path('send-friend-request/<int:to_user_id>/', views.send_friend_request, name='send_friend_request'),
    path('accept-friend-request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('decline-friend-request/<int:request_id>/', views.decline_friend_request, name='decline_friend_request'),

    path('attendance/update/', views.update_attendance, name='update_attendance'),
    path('manage-account/', views.manage_account, name='manage_account'),

    path('event/<int:event_id>/invite/<int:profile_id>/', views.send_event_invite, name='send_event_invite'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notification/<int:notif_id>/', views.view_notification, name='view_notification'),
    
    path('update-attendance/', views.update_attendance, name='update_attendance'),

    path("profilepage/<str:username>/", views.profilepage, name="profilepage"),

]
