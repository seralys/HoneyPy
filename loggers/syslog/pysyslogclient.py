
# -*- coding: utf-8 -*-

# Copyright (c) 2016, Alexander Böhm
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import division
from __future__ import absolute_import

version = u"0.1.1"

import socket, sys
from datetime import datetime


def datetime2rfc3339(dt, is_utc=False):
    if is_utc == False:
        # calculating timezone
        d1 = datetime.now()
        d2 = datetime.utcnow()
        diff_hr = (d1 - d2).seconds / 60 / 60
        tz = u""

        if diff_hr == 0:
            tz = u"Z"
        else:
            if diff_hr > 0:
                tz = u"+%s" % (tz)

            tz = u"%s%.2d%.2d" % (tz, diff_hr, 0)

        return u"%s%s" % (dt.strftime(u"%Y-%m-%dT%H:%M:%S.%f"), tz)

    else:
        return dt.isoformat() + u'Z'


FAC_KERNEL = 0
FAC_USER = 1
FAC_MAIL = 2
FAC_SYSTEM = 3
FAC_SECURITY = 4
FAC_SYSLOG = 5
FAC_PRINTER = 6
FAC_NETWORK = 7
FAC_UUCP = 8
FAC_CLOCK = 9
FAC_AUTH = 10
FAC_FTP = 11
FAC_NTP = 12
FAC_LOG_AUDIT = 13
FAC_LOG_ALERT = 14
FAC_CLOCK2 = 15
FAC_LOCAL0 = 16
FAC_LOCAL1 = 17
FAC_LOCAL2 = 18
FAC_LOCAL3 = 19
FAC_LOCAL4 = 20
FAC_LOCAL5 = 21
FAC_LOCAL6 = 22
FAC_LOCAL7 = 23

SEV_EMERGENCY = 0
SEV_ALERT = 1
SEV_CRITICAL = 2
SEV_ERROR = 3
SEV_WARNING = 4
SEV_NOTICE = 5
SEV_INFO = 6
SEV_DEBUG = 7


class SyslogClient(object):
    u"""
    >>> client = SyslogClient("localhost", 10514)
    >>> client.log("test")
    """

    def __init__(self, server, port, proto=u'udp', forceipv4=False, clientname=None, rfc=None, maxMessageLength=1024):
        self.socket = None
        self.server = server
        self.port = port
        self.proto = socket.SOCK_DGRAM
        self.rfc = rfc
        self.maxMessageLength = maxMessageLength
        self.forceipv4 = forceipv4

        if proto != None:
            if proto.upper() == u'UDP':
                self.proto = socket.SOCK_DGRAM
            elif proto.upper() == u'TCP':
                self.proto = socket.SOCK_STREAM

        if clientname == None:
            self.clientname = socket.getfqdn()
            if self.clientname == None:
                self.clientname = socket.gethostname()

    def connect(self):
        if self.socket == None:
            r = socket.getaddrinfo(self.server, self.port, socket.AF_UNSPEC, self.proto)
            if r == None:
                return False

            for (addr_fam, sock_kind, proto, ca_name, sock_addr) in r:
                self.socket = socket.socket(addr_fam, self.proto)
                if self.socket == None:
                    return False

                try:
                    self.socket.connect(sock_addr)
                    return True

                except socket.timeout, e:
                    if self.socket != None:
                        self.socket.close()
                        self.socket = None
                    continue

                # ensure python 2.x compatibility
                except socket.error, e:
                    if self.socket != None:
                        self.socket.close()
                        self.socket = None
                    continue

            return False

        else:
            return True

    def close(self):
        if self.socket != None:
            self.socket.close()
            self.socket = None

    def log(self, message, timestamp=None, hostname=None, facility=None, severity=None):
        pass

    def send(self, messagedata):
        if self.socket != None or self.connect():
            try:
                if self.maxMessageLength != None:
                    self.socket.sendall(messagedata[:self.maxMessageLength])
                else:
                    self.socket.sendall(messagedata)
            except IOError, e:
                self.close()


class SyslogClientRFC5424(SyslogClient):
    u"""
    >>> client = SyslogClientRFC5424("localhost", 10514, proto='udp')
    >>> client.log("test")
    >>> client = SyslogClientRFC5424("localhost", 10514, proto='tcp')
    >>> client.log("test")
    """

    def __init__(self, server, port, proto=u'udp', forceipv4=False, clientname=None):
        SyslogClient.__init__(self,
                              server=server,
                              port=port,
                              proto=proto,
                              forceipv4=forceipv4,
                              clientname=clientname,
                              rfc=u'5424',
                              maxMessageLength=None,
                              )

    def log(self, message, facility=None, severity=None, timestamp=None, hostname=None, version=1, program=None,
            pid=None, msgid=None):
        if facility == None:
            facility = FAC_USER

        if severity == None:
            severity = SEV_INFO

        pri = facility * 8 + severity

        if timestamp == None:
            timestamp_s = datetime2rfc3339(datetime.utcnow(), is_utc=True)
        else:
            timestamp_s = datetime2rfc3339(timestamp, is_utc=False)

        if hostname == None:
            hostname_s = self.clientname
        else:
            hostname_s = hostname

        if program == None:
            appname_s = u"-"
        else:
            appname_s = program

        if pid == None:
            procid_s = u"-"
        else:
            procid_s = pid

        if msgid == None:
            msgid_s = u"-"
        else:
            msgid_s = msgid

        d = u"<%i>%i %s %s %s %s %s %s\n" % (
            pri,
            version,
            timestamp_s,
            hostname_s,
            appname_s,
            procid_s,
            msgid_s,
            message
        )

        self.send(d.encode(u'utf-8'))


class SyslogClientRFC3164(SyslogClient):
    u"""
    >>> client = SyslogClientRFC3164("localhost", 10514, proto='udp')
    >>> client.log("test")
    >>> client = SyslogClientRFC3164("localhost", 10514, proto='tcp')
    >>> client.log("test")
    """

    def __init__(self, server, port, proto=u'udp', forceipv4=False, clientname=None):
        SyslogClient.__init__(self,
                              server=server,
                              port=port,
                              proto=proto,
                              forceipv4=forceipv4,
                              clientname=clientname,
                              rfc=u'3164',
                              maxMessageLength=1024,
                              )

    def log(self, message, facility=None, severity=None, timestamp=None, hostname=None, program=u"SyslogClient",
            pid=None):
        if facility == None:
            facility = FAC_USER

        if severity == None:
            severity = SEV_INFO

        pri = facility * 8 + severity

        if timestamp == None:
            t = datetime.now()
        else:
            t = timestamp

        timestamp_s = t.strftime(u"%b %d %H:%M:%S")

        if hostname == None:
            hostname_s = self.clientname
        else:
            hostname_s = hostname

        tag_s = u""
        if program == None:
            tag_s += u"SyslogClient"
        else:
            tag_s += program

        if pid != None:
            tag_s += u"[%i]" % (pid)

        d = u"<%i>%s %s %s: %s\n" % (
            pri,
            timestamp_s,
            hostname_s,
            tag_s,
            message
        )

        self.send(d.encode(u'ASCII', u'ignore'))


if __name__ == u'__main__':
    import doctest

    doctest.testmod()
