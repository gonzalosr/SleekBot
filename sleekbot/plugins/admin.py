# -*- coding: utf-8 -*-
"""
    This file is part of SleekBot. http://github.com/hgrecco/SleekBot
    See the README file for more information.
"""

from sleekbot.commandbot import botcmd, CommandBot, denymsg
from sleekbot.commandbot import parse_args, ArgError
from sleekbot.plugbot import BotPlugin


class Admin(BotPlugin):
    """A plugin to manage the bot."""

    @botcmd(name='rehash', allow=CommandBot.msg_from_owner)
    @denymsg('No molas lo suficiente como para ejecutar este comando')
    def handle_rehash(self, command, args, msg):
        """ Reload the bot config and plugins without dropping the XMPP stream.
        """

        self.bot.rehash()
        return "Recargado, amo"

    @botcmd(name='restart', allow=CommandBot.msg_from_owner)
    @denymsg('No molas lo suficiente como para ejecutar este comando')
    def handle_restart(self, command, args, msg):
        """ Restart the bot, reconnecting, etc ..."""

        self.bot.restart()
        return "Reiniciado, amo"

    @botcmd(name='die', allow=CommandBot.msg_from_owner)
    @denymsg('No molas lo suficiente como para ejecutar este comando')
    def handle_die(self, command, args, msg):
        """ Kill the bot."""

        self.bot.die()
        return "Muriendo... Nunca verás este mensaje"

    @botcmd(name='reload', allow=CommandBot.msg_from_owner)
    def handle_reload(self, command, args, msg):
        """ Reload the plugins """

        self.bot.cmd_plugins.reload_all()
        return "Plugins recargados, amo"

    @botcmd(hidden=True)
    def register(self, command, args, msg):
        """ Register yourself the first time as a bot owner
        """
        if self.bot.acl.count() > 0:
            return
        rolen = getattr(self.bot.acl.ROLE, 'owner')
        self.bot.acl[msg['from'].bare] = rolen
        return "Ahora eres mi amo."


class ACL(BotPlugin):
    """ A plugin to manage users."""

    @botcmd(usage='[add|del|see|test] jid rol',
            allow=CommandBot.msg_from_admin)
    def acl(self, command, args, msg):
        """ Administración de ACLs
        """
        try:
            args = parse_args(args, (('action', ('add', 'del', 'see', 'test')),
                                     ('jid', str), ('role', 'user')))
        except ArgError as ex:
            return ex.msg

        return getattr(self, 'acl_' + args.action,)(command, args, msg)

    @botcmd(usage='jid rol', allow=CommandBot.msg_from_admin, hidden=True)
    def acl_add(self, command, args, msg):
        """Add a jid with a given role
            If the user exists, modify the role.
        """
        try:
            args = parse_args(args, (('jid', str), ('role', 'user')))
        except ArgError as ex:
            return ex.msg

        try:
            rolen = getattr(self.bot.acl.ROLE, args.role)
        except AttributeError as ex:
            return '%s no es un rol válido' % args.role

        present = args.jid in self.bot.acl
        self.bot.acl[args.jid] = rolen
        if present:
            return '%s actualizado como %s' % (args.jid, args.role)
        else:
            return '%s añadido como %s' % (args.jid, args.role)

    @botcmd(usage='jid', allow=CommandBot.msg_from_admin, hidden=True)
    def acl_del(self, command, args, msg):
        """Deletes a jid
        """
        try:
            args = parse_args(args, (('jid', str), ))
        except ArgError as ex:
            return ex.msg

        present = args.jid in self.bot.acl
        if present:
            del self.bot.acl[args.jid]
            return '%s eliminado' % args.jid
        else:
            return '%s no se ha encontrado en la acl' % args.jid

    @botcmd(usage='jid', allow=CommandBot.msg_from_admin, hidden=True)
    def acl_see(self, command, args, msg):
        """See the role a jid
        """
        try:
            args = parse_args(args, (('jid', str), ))
        except ArgError as ex:
            return ex.msg

        part = self.bot.acl.find_part(args.jid)
        if part:
            if part == args.jid:
                return '%s es %s' % \
                    (args.jid, self.bot.acl.ROLE[self.bot.acl[args.jid]])
            else:
                return '%s a traves de %s es %s' % \
                       (args.jid, part, self.bot.acl.ROLE[self.bot.acl[part]])
        else:
            return '%s no se ha encontrado en la acl' % args.jid

    @botcmd(usage='jid rol', allow=CommandBot.msg_from_admin, hidden=True)
    def acl_test(self, command, args, msg):
        """Test if jid belongs to role
        """
        try:
            args = parse_args(args, (('jid', str), ('role', 'user')))
        except ArgError as ex:
            return ex.msg
        try:
            rolen = getattr(self.bot.acl.ROLE, args.role)
        except:
            return '%s no es un rol válido' % args.role

        present = args.jid in self.bot.acl
        if present:
            if self.bot.acl.check(args.jid, rolen):
                return '%s es %s' % (args.jid, args.role)
            else:
                return '%s no es %s' % (args.jid, args.role)
        else:
            return '%s no se ha encontrado en la acl' % args.jid
