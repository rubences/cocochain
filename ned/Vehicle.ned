//
// Vehicle Node Definition for CoCoChain
//

package cocochain.nodes;

import inet.applications.contract.IApp;
import inet.linklayer.ieee80211.Ieee80211Interface;
import inet.mobility.contract.IMobility;
import inet.networklayer.common.InterfaceTable;
import inet.networklayer.ipv4.Ipv4NetworkLayer;
import inet.transportlayer.udp.Udp;

module Vehicle
{
    parameters:
        int numApps = default(1);
        bool hasUdp = default(true);
        mobility.typename = default("RandomWaypointMobility");
        
        @display("i=device/car");
        @networkNode();
        
    gates:
        input radioIn @directIn;
        
    submodules:
        interfaceTable: InterfaceTable {
            @display("p=50,250");
        }
        
        mobility: <mobility.typename> like IMobility {
            @display("p=50,200");
        }
        
        app[numApps]: <> like IApp {
            @display("p=200,50,row,60");
        }
        
        udp: Udp if hasUdp {
            @display("p=200,150");
        }
        
        networkLayer: Ipv4NetworkLayer {
            @display("p=200,200");
        }
        
        wlan: Ieee80211Interface {
            @display("p=200,300");
        }
        
    connections allowunconnected:
        for i=0..numApps-1 {
            app[i].socketOut --> udp.appIn++ if hasUdp;
            app[i].socketIn <-- udp.appOut++ if hasUdp;
        }
        
        udp.ipOut --> networkLayer.transportIn++ if hasUdp;
        udp.ipIn <-- networkLayer.transportOut++ if hasUdp;
        
        networkLayer.ifOut++ --> wlan.upperLayerIn;
        networkLayer.ifIn++ <-- wlan.upperLayerOut;
        
        wlan.radioIn <-- radioIn;
}