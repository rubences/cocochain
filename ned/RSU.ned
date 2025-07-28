//
// RSU (Road Side Unit) Module for Highway Scenario
//

package cocochain;

import inet.node.inet.WirelessHost;

module RSU extends WirelessHost
{
    parameters:
        @display("i=device/accesspoint;is=l");
        
        // Network interface
        numWlanInterfaces = 1;
        wlan[0].typename = "Ieee80211Interface";
        wlan[0].mgmt.typename = "Ieee80211MgmtAdhoc";
        wlan[0].agent.typename = "";
        
        // Applications
        numApps = 1;
        app[0].typename = "RSUApp";
        
        // Mobility - RSUs are stationary
        mobility.typename = "StationaryMobility";
        
        // Physical parameters
        wlan[0].radio.transmitter.power = 20mW;
        wlan[0].radio.receiver.sensitivity = -85dBm;
        wlan[0].radio.receiver.energyDetection = -85dBm;
        wlan[0].radio.receiver.snirThreshold = 4dB;
}