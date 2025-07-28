//
// Vehicle Application NED Definition
//

package cocochain;

import inet.applications.contract.IApp;

simple VehicleApp like IApp
{
    parameters:
        double transactionInterval @unit(s) = default(2s);  // Transaction sending interval
        int localPort = default(9999);                       // UDP port for vehicle communication
        
        @signal[authLatency](type=double);
        @signal[handover](type=double);
        
        @statistic[authLatency](title="Authentication Latency"; source=authLatency; record=vector,mean,max,histogram; unit=s);
        @statistic[handover](title="Handover Events"; source=handover; record=vector,count; unit=events);
        
        @display("i=block/app");
        
    gates:
        input socketIn @labels(UdpControlInfo/up);
        output socketOut @labels(UdpControlInfo/down);
}