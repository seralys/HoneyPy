# -*- coding: utf-8 -*-

# HoneyPy Copyright (C) 2013-2017 foospidy
# https://github.com/foospidy/HoneyPy
# See LICENSE for details
# Written by Seralys S.à.r.l

import sys
from datetime import datetime
from twisted.python import log
import pysyslogclient
import socket

# prevent creation of compiled bytecode files
sys.dont_write_bytecode = True


def process(config, section, parts, time_parts):
    # TCP
    #	parts[0]: date
    #	parts[1]: time_parts
    #	parts[2]: plugin
    #	parts[3]: session
    #	parts[4]: protocol
    #	parts[5]: event
    #	parts[6]: local_host
    #	parts[7]: local_port
    #	parts[8]: service
    #	parts[9]: remote_host
    #	parts[10]: remote_port
    #	parts[11]: data
    # UDP
    #	parts[0]: date
    #	parts[1]: time_parts
    #	parts[2]: plugin string part
    #	parts[3]: plugin string part
    #	parts[4]: session
    #	parts[5]: protocol
    #	parts[6]: event
    #	parts[7]: local_host
    #	parts[8]: local_port
    #	parts[9]: service
    #	parts[10]: remote_host
    #	parts[11]: remote_port
    #	parts[12]: data

    if parts[4] == 'TCP':
        if len(parts) == 11:
            parts.append('')  # no data for CONNECT events

        post(config, section, parts[0], time_parts[0], parts[0] + ' ' + time_parts[0], time_parts[1], parts[3],
             parts[4], parts[5], parts[6], parts[7], parts[8], parts[9], parts[10], parts[11])
    else:
        # UDP splits differently (see comment section above)
        if len(parts) == 12:
            parts.append('')  # no data sent

        post(config, section, parts[0], time_parts[0], parts[0] + ' ' + time_parts[0], time_parts[1], parts[4],
             parts[5], parts[6], parts[7], parts[8], parts[9], parts[10], parts[11], parts[12])


def post(config, section, date, time, date_time, millisecond, session, protocol, event, local_host, local_port, service,
         remote_host, remote_port, data):


    syslog_server = config.get('syslog', 'syslog_server')
    syslog_protocol = config.get('syslog', 'syslog_protocol')
    syslog_program = config.get('syslog', 'syslog_program')

    if syslog_program == "hostname":
        syslog_program = socket.gethostname()

    syslog_port = int(config.get('syslog', 'syslog_port'))
    syslog_facility = int(config.get('syslog', 'syslog_facility'))
    syslog_severity = int(config.get('syslog', 'syslog_severity'))

    syslog_client = pysyslogclient.SyslogClientRFC3164(syslog_server, syslog_port, proto=syslog_protocol)

    date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S").isoformat()

    # applying [:-3] to time to truncate millisecond
    data = {
        'date': date,
        'time': time,
        'date_time': date_time,
        'millisecond': str(millisecond)[:-3],
        'session': session,
        'protocol': protocol,
        'event': event,
        'local_host': local_host,
        'local_port': local_port,
        'service': service,
        'remote_host': remote_host,
        'remote_port': remote_port,
        'data': data,
        'bytes': str(len(data))
    }

    try:
        payload = '\n'.join(['%s=%s' % (key, value) for (key, value) in data.items()])
        payload = payload.encode('ascii', 'ignore')

        syslog_client.log(payload,
                          facility=syslog_facility,
                          severity=syslog_severity,
                          program=syslog_program)

        log.msg('Sending event to syslog server %s with payload %s' % (syslog_server, payload))
    except Exception as e:
        log.msg('Error posting to %s : %s' % (section, str(e.message).strip()))
    finally:
        # quietly close the socket after use
        try:
            syslog_client.close()
        except:
            pass
