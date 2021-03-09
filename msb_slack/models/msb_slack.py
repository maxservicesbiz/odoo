# -*- coding: utf-8 -*-
#   Copyright (C) 2020  Max Services Biz


from odoo import models, fields, api, _, http
import logging
from odoo.exceptions import  ValidationError
import requests
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)


class LibSlack: 

    def __init__(self, webhook_url, icon_url):
        self.webhook_url = webhook_url
        self.icon_url = icon_url
    
    def notify(self, message):
        message.update({
            "username": 'Odoo',
            "icon_url": self.icon_url or  "https://maxs.biz/logo.png",
            #"icon_emoji": ":ghost:"
        })

        if self.webhook_url:
            res = requests.post(url=self.webhook_url, json=message)
            if res.status_code != 200: 
                print(res.text)

    def notify_by_channel(self, channel, message):
        payload = {
            "text": message,
            "channel": "#"+ channel or 'general'
        }
        self.notify(payload)

    def notify_direct(self, username, message):       
        payload = {
            "text": self.html_text(message),
            "channel": "@"+username
        }
        self.notify(payload)
    
    def html_text(self, text):
        soup = BeautifulSoup(text,features="html")
        return soup.getText()

class MSBSlacMailThread(models.AbstractModel):
    _inherit = 'mail.thread'


    def _message_post_after_hook(self, message):        
        message = message.sudo()
        params =  self.env['ir.config_parameter'].sudo()
        url = params.get_param("msb_slack_slack_webhook_url", default=False)
        icon_url ="{}/logo.png".format( params.get_param("web.base.url", ""))
        libslack = LibSlack(url, icon_url)
        
        if len(message.channel_ids) and message.channel_ids.channel_type=='chat' and message.channel_ids.public=='private':
            issuer = message.author_id 
            receiver = False
            if len(message.channel_ids.channel_last_seen_partner_ids) == 2:
                # Direct message 
                # if private channel only existe 2 parners is consider how is direct message
                for r in message.channel_ids.channel_last_seen_partner_ids:
                    if r.partner_id.id != issuer.id:
                        receiver = r.partner_id
                        break
                if issuer and receiver and receiver.slack_id:
                    msg = "%s \n %s" % (self.slack_author(issuer) , message.body)
                    libslack.notify_direct(receiver.slack_id, message= msg)
            elif len(message.channel_ids.channel_last_seen_partner_ids) > 2:
                # Private channel
                pass
        elif len(message.channel_ids) and message.channel_ids.channel_type=='channel' and message.channel_ids.public=='groups':
            if len(message.channel_ids):
                libslack.notify_by_channel(
                    channel=message.channel_ids[0].name,
                    message=message.body
                )
        if message.message_type == 'notification' and len(message.tracking_value_ids):
            # message.subtype_id.name 'Task Opened'
            # message.model project.task
            # message.res_id 
            # message.record_name
            channels = self.env['mail.channel'].sudo().search([])
            channel_notify = []
            for channel in channels:
                 for model in channel.slack_model_ids:
                    if model.model == message.model:
                        channel_notify.append(channel)
            
            msg_tracking_values = [ "{} : {} -> {} ".format(
                m.get('changed_field'), m.get('old_value') , m.get('new_value') 
            ) for m in  message.message_format()[0].get('tracking_value_ids',[])]

            for c in channel_notify:
                msg = "<{}|{}>\n {} \n {}".format(
                    self.slack_model_url(message.model, message.res_id),
                    message.record_name or message.subtype_id.name ,
                    self.slack_author(message.author_id),                    
                    " \n ".join(msg_tracking_values)
                )
                libslack.notify_by_channel(c.name, msg )
        return super(MSBSlacMailThread, self)._message_post_after_hook(message)
    
    def slack_author(self, author_id):
        #author_id.slack_id or
        return "Author: @{}".format( author_id.name)
        
        
    def slack_model_url(self, _model, _id ):
        url = "{}/web?db={}#id={}&view_type=form&model={}".format(
            self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            http.request.session.db,
            _id, 
            _model
        )
        #'&action=' +  str(self.env['ir.model.data'].get_object_reference('mail', 'email_compose_message_wizard_form')[1])
        return url
            