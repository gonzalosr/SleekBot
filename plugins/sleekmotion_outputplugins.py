"""
    sleekmotion.py - An approximate port of bMotion to Sleek.
    Copyright (C) 2007 Kevin Smith

    SleekBot is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    SleekBot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this software; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import random

def typostransform( oldstring):
    corrections = []
    wordpairs = {'the':'teh','is':'si','I':'i'}
    charpairs = {
        'z':{'new':'z\\','correct':"-\\"},
        ')':{'new':')_','correct':"-_"},
        'd':{'new':'df','correct':"-f"},
        'e':{'new':'re','correct':"-r"},
        's':{'new':'sd','correct':"-d"},
        'l':{'new':';l','correct':"-;"}
        
                }
    outputwords = oldstring.split()
    
    for i in range(len(outputwords)):
        if outputwords[i] in wordpairs.keys() and random.randint(0,100) < 10:
            corrections.append("s/%s/%s/" % (wordpairs[outputwords[i]],outputwords[i]))
            outputwords[i] = wordpairs[outputwords[i]]
            continue
        for j in range(len(outputwords[i])):
            if outputwords[i][j] in charpairs.keys() and random.randint(0,100) < 10:
                corrections.append(charpairs[outputwords[i][j]]['correct'])
                outputwords[i] = outputwords[i][:j] + charpairs[outputwords[i][j]]['new'] + outputwords[i][j+1:]
                break
    
    for i in range(len(outputwords) - 1):
        if random.randint(0,100) < 10:
            outputwords[i] = "".join(outputwords[i:i+2])
            del outputwords[i+1]
            corrections.append('+space')
            break
    output = " ".join(outputwords)
    if len(corrections) > 0:
        output = output + "|" + " ".join(corrections)
    return output

class sleekmotion_outputplugins(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        plugins = []
        plugins.append({'name':'typos','function':typostransform,'probability':10})
        for plugin in plugins:
            self.bot.botplugin['sleekmotion'].registerOutputPlugin(plugin)