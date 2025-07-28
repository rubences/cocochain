//
// RSU Application NED Definition
//

package cocochain;

import inet.applications.contract.IApp;

simple RSUApp like IApp
{
    parameters:
        bool usePBFT = default(false);          // Use PBFT instead of CoCoChain
        double coverageRadius @unit(m) = default(1000m);  // RSU coverage radius
        int localPort = default(8888);          // UDP port for RSU communication
        
        @signal[authLatency](type=double);
        @signal[handoverSuccess](type=double);
        @signal[throughput](type=double);
        
        @statistic[authLatency](title="Authentication Latency"; source=authLatency; record=vector,mean,max,histogram; unit=s);
        @statistic[handoverSuccess](title="Handover Success Rate"; source=handoverSuccess; record=vector,mean; unit=ratio);
        @statistic[throughput](title="Transaction Throughput"; source=throughput; record=vector,mean; unit="tx/s");
        
        @display("i=block/app");
        
    gates:
        input socketIn @labels(UdpControlInfo/up);
        output socketOut @labels(UdpControlInfo/down);
}