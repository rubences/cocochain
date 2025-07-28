//
// CoCoChain Network Definition
// High-density urban network with 4x4 grid topology
//

package cocochain.networks;

import cocochain.nodes.Vehicle;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.physicallayer.ieee80211.packetlevel.Ieee80211ScalarRadioMedium;

network CoCoChainNetwork
{
    parameters:
        int numVehicles = default(2500);
        double playgroundSizeX @unit(m) = default(2236m);
        double playgroundSizeY @unit(m) = default(2236m);
        int gridRows = default(4);
        int gridCols = default(4);
        
        @display("bgb=$playgroundSizeX,$playgroundSizeY");
        
    submodules:
        radioMedium: Ieee80211ScalarRadioMedium {
            @display("p=50,50");
        }
        
        configurator: Ipv4NetworkConfigurator {
            @display("p=50,100");
        }
        
        vehicle[numVehicles]: Vehicle {
            @display("p=uniform(0,$playgroundSizeX),uniform(0,$playgroundSizeY)");
        }
}