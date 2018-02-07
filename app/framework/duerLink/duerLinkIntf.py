# -*- coding: utf-8 -*-

import duerLink

class platform_type:
    ERaspberryPi = duerLink.ERaspberryPi
    EMtk         = duerLink.EMtk
    EHodor       = duerLink.EHodor
    EOther       = duerLink.EOther

class auto_config_network_type:
    ESoftAP = duerLink.ESoftAP
    EBle    = duerLink.EBle
    EAll    = duerLink.EAll

class notify_network_status_type:
    ENetworkNone                = duerLink.ENetworkNone
    ENetworkConfigExited        = duerLink.ENetworkConfigExited
    ENetworkConfigStarted       = duerLink.ENetworkConfigStarted
    ENetworkConfigIng           = duerLink.ENetworkConfigIng
    ENetworkConfigRouteFailed   = duerLink.ENetworkConfigRouteFailed
    ENetworkLinkSucceed         = duerLink.ENetworkLinkSucceed
    ENetworkLinkFailed          = duerLink.ENetworkLinkFailed
    ENetworkRecoveryStart       = duerLink.ENetworkRecoveryStart
    ENetworkRecoverySucceed     = duerLink.ENetworkRecoverySucceed
    ENetworkRecoveryFailed      = duerLink.ENetworkRecoveryFailed

class InternetConnectivity:
    UNAVAILABLE = duerLink.UNAVAILABLE
    AVAILABLE   = duerLink.AVAILABLE
    UNKNOW      = duerLink.UNKNOW


def notify_network_config_status_default_callback(notify_type):
    print "Network config notify type %d" % notify_type

def network_status_changed_callback(current_status):
    print "Network status %d" % current_status

def dlp_data_notify_callback(jsonData, sessionId):
    print "Dlp data recv : %s" % jsonData
    return " "

class networkConfigObserver(duerLink.NetworkConfigStatusObserver):
    def notify_network_config_status(self, notify_type):
        self.callback(notify_type)

    def add_callback(self, callback=notify_network_config_status_default_callback):
        self.callback = callback


class networkStatusObserver(duerLink.NetWorkPingStatusObserver):
    def network_status_changed(self, current_status):
        self.callback(current_status)

    def add_callback(self, callback=network_status_changed_callback):
        self.callback = callback


class dlpDataObserver(duerLink.DuerLinkReceivedDataObserver):
    def NotifyReceivedData(self, jsonData, sessionId=0):
        reponse = self.callback(jsonData, sessionId)
        return reponse

    def add_callback(self, callback=dlp_data_notify_callback):
        self.callback = callback


class duerLinkIntf(object):

    def __init__(self):
        self.duerLinkInstance = duerLink.DuerLinkWrapper.get_instance()

    def init_duer_link(self):
        self.duerLinkInstance.init_duer_link()

    def start_network_recovery(self):
        self.duerLinkInstance.start_network_recovery()

    def start_discover_and_bound(self, client_id):
        self.duerLinkInstance.start_discover_and_bound(client_id)

    def set_networkConfig_observer(self, networkConfig_ob):
        self.duerLinkInstance.set_networkConfig_observer(networkConfig_ob)

    def set_monitor_observer(self, monitor_ob):
        self.duerLinkInstance.set_monitor_observer(monitor_ob)

    def set_dlp_data_observer(self, dlp_ob):
        self.duerLinkInstance.set_dlp_data_observer(dlp_ob)

    def send_dlp_msg_to_all_clients(self, sendBuffer):
        self.duerLinkInstance.send_dlp_msg_to_all_clients(sendBuffer)
