#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import logging
import sleekxmpp


from .commandbot import CommandBot
from .plugbot import PlugBot
from .store import Store
from .confighandler import ConfigDict

from .acl import Enum

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


END_STATUS = Enum(['none', 'restart', 'reload', 'die'])


class SleekBot(sleekxmpp.ClientXMPP, CommandBot, PlugBot):
    """ SleekBot is a pluggable Jabber/XMPP bot based on SleekXMPP

        SleekBot was originally written by Nathan Fritz and Kevin Smith.
        Este fork es mantenido por Gonzalo Sánchez Romero
    """

    def __init__(self, config, plugin_config=None):
        """ Initializes the bot
                config -- specifies the configuration. Options:
                          - a dictionary
                          - a yaml filename
                          - a json filename
        """
        self._botconfig = ConfigDict(config)
        logging.info("Logging in as %s", self.botconfig['auth.jid'])
        sleekxmpp.ClientXMPP.__init__(self, **self.botconfig['auth'])
        self.store = self.botconfig.get('storage', None)
        if self.store is not None:
            self.store = Store(self.store)
        else:
            logging.warning("No storage element found in config file - "
                            "proceeding with no persistent storage, "
                            "plugin behaviour may be undefined.")
        self.rooms = {}
        self.add_event_handler("session_start", self.handle_session_start,
                               threaded=True)
        self.register_xmpp_plugins()
        CommandBot.__init__(self)
        PlugBot.__init__(self, default_package='sleekbot.plugins')
        self.register_adhocs()
        self.end_status = END_STATUS.none

    def start(self):
        """ Connects to the server
        """

        logging.info("Conectando ...")
        server = 'nemo.notin.es:5222'
        # self.botconfig.get('connection.server', '')
        if server and isinstance(server, (str, unicode)):
            server = server.split(':')
        else:
            server = None
        super(SleekBot, self).connect(server)

    def get_botconfig(self):
        """ Gets config elementtree
        """
        return self._botconfig

    def set_botconfig(self, value):
        """ Sets the config elementtree
                value is None: loads the previous config file
                type of value is str: use is as the name of the config file
        """

        self._botconfig.set(value)

    botconfig = property(get_botconfig, set_botconfig, None,
                         'Configuration as a dictionary')

    def register_adhocs(self):
        """ Register all ad-hoc commands with SleekXMPP.
        """
        aboutform = self.plugin['xep_0004'].makeForm('form', "Sobre SleekBot")
        aboutform.addField('about', 'fixed', value=self.__doc__)
        # self.plugin['xep_0050'].addCommand('about', 'About Sleekbot', aboutform)
        pluginform = self.plugin['xep_0004'].makeForm('form', 'Plugins')
        plugins = pluginform.addField('plugin', 'list-single', 'Plugins')
        for key in self.cmd_plugins:
            plugins.addOption(key, key)
        plugins = pluginform.addField('option', 'list-single', 'Commands')
        plugins.addOption('about', 'About')
        # plugins.addOption('config', 'Configure')
        # self.plugin['xep_0050'].addCommand('plugins', 'Plugins', pluginform, self.form_plugin_command, True)

    def form_plugin_command(self, form, sessid):
        """ Take appropriate action when a plugin ad-hoc request is received.
        """
        value = form.getValues()
        option = value['option']
        plugin = value['plugin']
        if option == 'about':
            aboutform = self.plugin['xep_0004'].makeForm('form',
                                                         'Sobre SleekBot')
            aboutform.addField('about', 'fixed',
                               value=self.cmd_plugins[plugin].about())
            return aboutform, None, False
        elif option == 'config':
            pass

    def register_xmpp_plugins(self):
        """ Registers all XMPP plugins required by botconfig.
        """

        plugins = self.botconfig.get('plugins.xmpp', ())

        for plugin in plugins:
            try:
                self.registerPlugin(**plugin)
                logging.info("Registro plugin XMPP %s OK",
                             plugin['plugin'])
            except Exception as ex:
                logging.info("Registro plugin XMPP %s ERROR: %s",
                             plugin['plugin'], ex)

    def handle_session_start(self, event):
        """ Event runnning when the session is established.
        """
        self.getRoster()
        priority = self.botconfig.get('connection.priority', '1')
        self.sendPresence(ppriority=priority)
        self.join_rooms()

    def join_rooms(self):
        """ Join to MUC rooms
        """
        logging.info("Joining MUC rooms")
        xrooms = self.botconfig.get('rooms', ())

        try:
            rooms = {}
            for xroom in xrooms:
                rooms[xroom['room']] = xroom['nick']
        except:
                logging.info('No se han encontrado habitaciones')

        for room in set(self.rooms.keys()).difference(rooms.keys()):
            logging.info("Saliendo de la habitación %s.", room)
            self.plugin['xep_0045'].leaveMUC(room, self.rooms[room])
            del self.rooms[room]
        for room in set(rooms.keys()).difference(self.rooms.keys()):
            self.rooms[room] = rooms[room]
            logging.info("Uniéndose a la habitación %s como %s.",
                         room, rooms[room])
            self.plugin['xep_0045'].joinMUC(room, rooms[room])

    def restart(self):
        """ Cause the bot to be completely restarted (will reconnect etc.)
        """
        self.end_status = END_STATUS.restart
        logging.info("Reiniciando bot")
        self.die()

    def rehash(self):
        """ Re-reads the config file, making appropriate runtime changes.
            Causes all plugins to be reloaded (or unloaded).
            The XMPP stream and MUC rooms will not be disconnected.
        """
        logging.info("Recarga iniciada")
        modules = self.cmd_plugins.get_modules()
        CommandBot.pause(self)
        PlugBot.stop(self)

        logging.info("Recargando archivo de configuración")
        self.botconfig = None
        for module in modules:
            reload(module)
        CommandBot.reset(self)

        PlugBot.start(self)
        CommandBot.resume(self)
        self.join_rooms()

    def die(self):
        """ Kills the bot.
        """
        PlugBot.stop(self)
        CommandBot.stop(self)
        self.rooms = {}
        logging.info("Desconectando bot")
        self.disconnect()

    def mucnick_to_jid(self, mucroom, mucnick):
        """ Returns the jid associated with a mucnick and mucroom
        """
        if mucroom in self.plugin['xep_0045'].getJoinedRooms():
            logging.debug("Buscando JID real de %s %s", mucroom, mucnick)
            real_jid = self.plugin['xep_0045'].getJidProperty(mucroom,
                                                              mucnick, 'jid')
            logging.debug(real_jid)
            if real_jid:
                return real_jid
            else:
                return None
        return None

    def get_real_jid(self, msg):
        """ Returns the real jid of a msg
        """
        if msg['type'] == 'groupchat' and msg['mucnick']:
            return self.mucnick_to_jid(msg['mucroom'], msg['mucnick']).bare
        else:
            if msg['jid'] in self['xep_0045'].getJoinedRooms():
                return self.mucnick_to_jid(msg['mucroom'], msg['mucnick']).bare
            else:
                return msg['from'].bare
        return None
