# -*- coding: utf-8 -*-
"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

from sleekbot.commandbot import botcmd, CommandBot, denymsg
from sleekbot.plugbot import BotPlugin
from time import gmtime, strftime
# from sleekxmpp.exceptions import IqError, IqTimeout
# import logging


class Others(BotPlugin):
    """A plugin to interact with and obtain information about other users."""

    @botcmd(usage='[muc] [text]', allow=CommandBot.msg_from_owner)
    @denymsg("No soy tu zorra.")
    def say(self, command, args, msg):
        """Hace que el bot envíe un texto a un canal."""

        if args.count(" ") >= 1:
            [muc, text] = args.split(" ", 1)
        else:
            return "Parámetros insuficientes"
        self.bot.sendMessage(muc, text, mtype='groupchat')
        return "Mensaje enviado."

    @botcmd(usage='[jid] [text]', allow=CommandBot.msg_from_owner)
    @denymsg("No soy tu zorra.")
    def tell(self, command, args, msg):
        """Hace que el bot envíe un texto a un JID."""

        if args.count(" ") >= 1:
            [jid, text] = args.split(" ", 1)
            idmensaje = str(msg['id'])
            fechahora = strftime("%d-%m-%Y %H:%M:%S")
            origen = str(msg['from']).split('@')[0].capitalize()
            texto = idmensaje + " desde " + origen + "\n" + fechahora + "\n" + text
        else:
            return "Parámetros insuficientes"
        self.bot.sendMessage(jid, texto, mtype='message')
        return "Mensaje enviado."

    @botcmd(usage='[telefono] [texto]', allow=CommandBot.msg_from_owner)
    @denymsg("No soy tu zorra.")
    def wa(self, command, args, msg):
        """Hace que el bot envíe un texto al whatsapp de un teléfono."""

        if args.count(" ") >= 1:
            [jid, text] = args.split(" ", 1)
        else:
            return "Parámetros insuficientes"
        self.bot.sendMessage(jid, text, mtype='message')
        return "Mensaje enviado."

#    @botcmd(usage='[jid]')
#    def ping(self, command, args, msg):
#        """Discover latency to a jid."""
#        try:
#            latency = self.bot['xep_0199'].sendPing(args, 10)
#            if latency is None:
#                response = "No response when pinging " + args
#            else:
#                response = "Ping response received from %s in %d seconds." % \
#                    (args, latency)
#
#        except IqError as err:
#            logging.error(err.iq['error']['condition'])
#            response = err.iq['error']['condition']
#        except IqTimeout:
#            logging.error('Server is taking too long to respond')
#            response = 'Server is taking too long to respond'
#
#        return response
