# -*- coding: utf-8 -*-

from framework.duerLink.duerLinkIntf import *
import time

clientId    = "BhqAyIkxbhbWPvPMXeE1uHUX"

duerLink = duerLinkIntf()

def networkConfigNotify_callback(notify_type):
    if notify_type == notify_network_status_type.ENetworkConfigStarted:
        print "networkConfig :: ENetworkConfigStarted"

    elif notify_type == notify_network_status_type.ENetworkConfigIng:
        print "networkConfig :: ENetworkConfigIng"

    elif notify_type == notify_network_status_type.ENetworkLinkFailed:
        print "networkConfig :: ENetworkLinkFailed"

    elif notify_type == notify_network_status_type.ENetworkConfigRouteFailed:
        print "networkConfig :: ENetworkConfigRouteFailed"

    elif notify_type == notify_network_status_type.ENetworkConfigExited:
        print "networkConfig :: ENetworkConfigExited"

    elif notify_type == notify_network_status_type.ENetworkLinkSucceed:
        print "networkConfig :: ENetworkLinkSucceed"
    pass

def networkStatus_callback(status):
    if status == InternetConnectivity.UNAVAILABLE:
        print "networkStatus :: UNAVAILABLE"

    elif status == InternetConnectivity.AVAILABLE:
        print "networkStatus :: AVAILABLE"

    elif status == InternetConnectivity.UNKNOW:
        print "networkStatus :: UNKNOW"

    pass

def dlpDataNotify_callback(jsonData, sessionId):
    print "Dlp data recv : %s" % jsonData
    response = "{\"to_client\":{\"header\":{\"namespace\":\"dlp.authentication\",\
    \"name\":\"PassportPairReturn\",\"messageId\":\"1cafb8d9-8958-4dec-926c-ac8ee060c840\"},\
    \"payload\":{\"status\":0,\"message\":\"\"}}}"
    duerLink.send_dlp_msg_to_all_clients(response)
    return " "



duerLink.init_duer_link()

networkconfigObserver = networkConfigObserver()
networkconfigObserver.add_callback(networkConfigNotify_callback)
duerLink.set_networkConfig_observer(networkconfigObserver)

networkStatusObserver = networkStatusObserver()
networkStatusObserver.add_callback(networkStatus_callback)
duerLink.set_monitor_observer(networkStatusObserver)

dlpObserver = dlpDataObserver()
dlpObserver.add_callback(dlpDataNotify_callback)
duerLink.set_dlp_data_observer(dlpObserver)

duerLink.start_network_recovery()

duerLink.start_discover_and_bound(clientId)

while True:
    time.sleep(2)
    continue
