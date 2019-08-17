from asgiref.sync import async_to_sync

import channels.layers

from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView

from . import models


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['rooms'] = models.Room.objects.all().order_by('name')
        return context


class InviteView(TemplateView):
    template_name = "invite.html"

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        REQUEST_DATA = request.POST
        email = REQUEST_DATA.get('email')
        if not email:
            context['error'] = "Email field not provided"
            return super(TemplateView, self).render_to_response(context)

        data = {
            'type': 'send_invite',
            'email': email,
            'message': "Hi, %s, you're invited!! Check us out at http://www.solutionx.com.my for more info!" % email
        }
        channel_layer = channels.layers.get_channel_layer(settings.BATCH_CHANNEL_LAYER)
        async_to_sync(channel_layer.send)('send-email', data)
        context['message'] = "We're sending the invite for you!"
        return super(TemplateView, self).render_to_response(context)


class ChatView(TemplateView):
    template_name = "chat.html"

    def get_context_data(self, **kwargs):
        context = super(ChatView, self).get_context_data(**kwargs)
        label = kwargs['room_name']
        try:
            chats = reversed(list(models.Room.objects.get(label=label).messages.only('handle', 'message', 'timestamp').order_by("-id")[:5]))
            context['chats'] = chats
        except Exception as e:
	        raise e;
        context['CHAT_PORT'] = settings.CHAT_PORT
        return context