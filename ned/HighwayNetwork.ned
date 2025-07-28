//
// Highway Network Topology for CoCoChain Simulation
// 20 km linear highway with 5 RSUs (1 km coverage each, 500m overlap)
//

package cocochain;

import inet.node.inet.WirelessHost;
import inet.physicallayer.wireless.ieee80211.packetlevel.Ieee80211ScalarRadioMedium;
import inet.visualizer.canvas.integrated.IntegratedCanvasVisualizer;
import inet.mobility.single.LinearMobility;

network HighwayNetwork
{
    parameters:
        int numVehicles = default(200);
        double highwayLength @unit(m) = default(20000m);  // 20 km highway
        
        @display("bgb=21000,1000;bgi=background/highway");

    submodules:
        visualizer: IntegratedCanvasVisualizer {
            @display("p=100,50");
        }
        
        radioMedium: Ieee80211ScalarRadioMedium {
            @display("p=100,150");
        }

        // 5 RSUs along the highway at 2km, 6km, 10km, 14km, 18km
        rsu[5]: WirelessHost {
            parameters:
                numApps = 1;
                app[0].typename = "RSUApp";
                mobility.typename = "StationaryMobility";
                mobility.initialX = 2000m + index * 4000m;
                mobility.initialY = 500m;
                
                // High power for 1km coverage
                wlan[0].radio.transmitter.power = 100mW;
                
            @display("p=$x,500;i=device/accesspoint");
            x = 2000 + index * 4000;
        }

        // Vehicles moving on the highway
        vehicle[numVehicles]: WirelessHost {
            parameters:
                numApps = 1;
                app[0].typename = "VehicleApp";
                mobility.typename = "LinearMobility";
                mobility.speed = uniform(27.8mps, 36.1mps); // 100-130 km/h
                mobility.angle = uniform(-5deg, 5deg);
                mobility.initialX = uniform(0m, 20000m);
                mobility.initialY = uniform(400m, 600m);
                
            @display("p=$x,$y;i=device/car");
            x = uniform(0, 20000);
            y = uniform(400, 600);
        }

    connections allowunconnected:
}