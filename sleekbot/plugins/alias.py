# -*- coding: utf-8 -*-
"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

import logging

from sleekbot.commandbot import botcmd, botfreetxt
from sleekbot.commandbot import parse_args, ArgError
from sleekbot.plugbot import BotPlugin


class AliasCmd(object):
    """ Represent an aliased command
    """

    def __init__(self, jid, aliascmd, command=None):
        self.jid = jid
        self.alias = aliascmd
        self.command = command


class AliasStore(object):
    """ Class for storing aliased commands into he database
    """

    def __init__(self, store):
        self.store = store
        self.create_table()

    def create_table(self):
        """ Create the alias table.
        """
        with self.store.context_cursor() as cur:
            if not self.store.has_table(cur, 'alias'):
                cur.execute("""CREATE TABLE "alias" (
                            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                            "jid" VARCHAR(256), "alias" VARCHAR(256),
                            "command" VARCHAR(256))""")
                cur.execute('CREATE INDEX idx_jid ON alias (jid)')
                cur.execute('CREATE INDEX idx_jid_alias ON alias (jid, alias)')
                logging.debug("creada tabla alias")

    def update(self, aliascmd):
        """ Update or insert an aliased command.
        """
        with self.store.context_cursor() as cur:
            cur.execute('SELECT * FROM alias WHERE jid=? AND alias=?',
                        (aliascmd.jid, aliascmd.alias))
            if (len(cur.fetchall()) > 0):
                cur.execute('UPDATE alias SET jid=?, command=?, alias=?'
                    'WHERE jid=? AND alias=?', (aliascmd.jid, aliascmd.command,
                                                aliascmd.alias, aliascmd.jid,
                                                aliascmd.alias))
            else:
                cur.execute('INSERT INTO alias(jid, command, alias)' \
                    'VALUES(?,?,?)', (aliascmd.jid, aliascmd.command,
                    aliascmd.alias))

    def get(self, aliascmd):
        """ Get an alias.
        """
        with self.store.context_cursor() as cur:
            cur.execute('SELECT * FROM alias WHERE jid=? AND alias=?',
                        (aliascmd.jid, aliascmd.alias))
            results = cur.fetchall()

            if len(results) == 0:
                return None
            return AliasCmd(results[0][1], results[0][2], results[0][3])

    def get_all(self, jid):
        """ Get all aliases.
        """
        with self.store.context_cursor() as cur:
            cur.execute('SELECT * FROM alias WHERE jid=?', (jid,))
            results = cur.fetchall()

            if len(results) == 0:
                return None
            response = []
            for result in results:
                response.append(AliasCmd(result[1], result[2], result[3]))
            return response

    def delete(self, aliascmd):
        """ Delete an aliased command.
        """
        with self.store.context_cursor() as cur:
            cur.execute('DELETE FROM alias WHERE jid=? AND alias=?',
                    (aliascmd.jid, aliascmd.alias))


class Alias(BotPlugin):
    """ A plugin for global and user defined aliases.
    """

    freetextRegex = ''

    def __init__(self, aliases=None):
        BotPlugin.__init__(self)
        # global aliases
        self.global_aliases = {}
        if not aliases:
            return
        for alias, cmd in aliases.items():
            logging.debug("Cargar alias global: %s", alias)
            self.global_aliases[alias] = AliasCmd(None, alias, cmd)

    def _on_register(self):
        """ On plugin load parse the freetextRegex together and set it global
        so botfreetext can use it later.
        """
        self.chat_prefix = self.bot.chat_prefix
        self.muc_prefix = self.bot.muc_prefix
        self.alias_store = AliasStore(self.bot.store)

        # botfreetext regex string with im and mux prefix
        global freetextRegex
        freetextRegex = "^[\%s\%s][a-zA-Z].*$" \
                        % (self.chat_prefix, self.muc_prefix)

    @botfreetxt(priority=1, regex=freetextRegex)
    def handle_alias(self, text, msg, command_found, freetext_found, match):
        """ Botfreetext handler that match global or user defined
            aliases. The aliased command replaces the msg['body'] which
            is then routed again to self.bot.handle_msg_botcmd(msg).
        """
        if command_found is True:
            return
        if msg['type'] == 'groupchat':
            prefix = self.muc_prefix
        else:
            prefix = self.chat_prefix
        command = msg.get('body', '').strip().split(' ', 1)[0]
        if ' ' in msg.get('body', ''):
            args = msg['body'].split(' ', 1)[-1].strip()
        else:
            args = ''
        if command.startswith(prefix):
            if len(prefix):
                command = command.split(prefix, 1)[-1]
            aliascmd = self.alias_store.get(AliasCmd(self.bot.get_real_jid(msg),
                    command))
            if not aliascmd is None:
                msg['body'] = str("%s%s %s" % (prefix, aliascmd.command, args))
                self.bot.handle_msg_botcmd(msg)
            elif command in self.global_aliases:
                aliascmd = self.global_aliases[command]
                msg['body'] = "%s%s %s" % (prefix, aliascmd.command, args)
                self.bot.handle_msg_botcmd(msg)

    @botcmd(usage="[add | del | list] [alias] [comando [opciones]]")
    def alias(self, command, args, msg):
        """ Reemplaza comandos largos (incluyendo opciones) con palabras cortas.
        """
        try:
            args = parse_args(args, (('action',
                                    (str, 'add', 'del', 'list')), ))
        except ArgError as error:
            return error.msg

        args.parsed_ = False
        return getattr(self, 'alias_' + args.action,)(command, args, msg)

    @botcmd(usage="alias comando [opciones])", hidden=True)
    def alias_add(self, command, args, msg):
        """ Añade un alias con el comando y opciones especificados.
        """
        try:
            args = parse_args(args, (('action', (str, 'add')), ('alias', str),
                    ('command', str)))
        except ArgError as error:
            return error.msg

        bot_commands = dict(self.bot.chat_commands.items()
                            + self.bot.muc_commands.items())

        if not args.alias in bot_commands:
            if not args.tail_ is None:
                command = args.command + ' ' + args.tail_
            else:
                command = args.command
            self.alias_store.update(AliasCmd(self.bot.get_real_jid(msg),
                                            args.alias, command))
            return "Alias guardado."
        else:
            return "%s es un comando del bot." % args.alias

    @botcmd(usage="alias", hidden=True)
    def alias_del(self, command, args, msg):
        """ Elimina un alias.
        """
        try:
            args = parse_args(args, (('action', (str, 'del')), ('alias', str)))
        except ArgError as error:
            return error.msg

        aliascmd = self.alias_store.get(AliasCmd(self.bot.get_real_jid(msg),
                                    args.alias))
        if not aliascmd is None:
            self.alias_store.delete(AliasCmd(self.bot.get_real_jid(msg),
                                    args.alias))
            return "Alias eliminado."
        if args.alias in self.global_aliases:
            return "No se puede borrar un alias global."
        return "Alias desconocido."

    @botcmd(hidden=True)
    def alias_list(self, command, args, msg):
        """ Muestra los alias existentes.
        """
        aliases = self.alias_store.get_all(self.bot.get_real_jid(msg))
        response = 'Alias: '
        if not aliases is None:
            for aliascmd in aliases:
                response += "\n%s = %s" % (aliascmd.alias, aliascmd.command)
        if not self.global_aliases == {}:
            for (key, aliascmd) in self.global_aliases.iteritems():
                response += "\n(*) %s = %s" % (aliascmd.alias, aliascmd.command)
        if response == 'Alias: ':
            response += "Ninguno."
        return response

    def example_config(self):
        """ Configuration example """
        return {'aliases': {'r': 'rehash',
                            'r100': 'random 100',
                            'say2muc': 'say c1@conference.localhost'}}


