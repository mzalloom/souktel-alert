#!/usr/bin/env python
# encoding=utf-8
import logging
from datetime import datetime

from rapidsms.models import Connection, Backend
from rapidsms.messages.outgoing import OutgoingMessage

from group_messaging.models import SendingLog, OutgoingLog


logger = logging.getLogger(__name__)


def process_queue_callback(router, *args, **kwargs):
    return process_queue(router)


def process_queue(router):

    # queued messages
    messages = OutgoingLog.objects.filter(status=OutgoingLog.QUEUED)[:10]

    for message in messages:
        logger.debug('Processing message: %s', message)
        
        conn, _ = Connection.objects.get_or_create(identity=message.identity,
                                                   backend=message.backend)
        msg = OutgoingMessage(conn, message.text)
        msg.send()
        message.status = str(OutgoingLog.DELIVERED)
        message.save()


def send_message(sender, groups, text, date):
    
    # create message object
    message = SendingLog(sender=sender, text=text, date=date)
    message.save()

    # attach groups
    for group in groups:

        # skip non-active groups
        if not group.active:
                continue
        message.groups.add(group)

        # attach recipients from group
        for recipient in group.recipients.select_related():

            # skip non-active recipients
            if not recipient.active:
                continue

            message.recipients.add(recipient)

            # create to-send messages
            msg = OutgoingLog(sender=sender, identity=recipient.default_connection.identity, \
                              backend=recipient.default_connection.backend, text=message.text, \
                              status=OutgoingLog.QUEUED)
            msg.save()

