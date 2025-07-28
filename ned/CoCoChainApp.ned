//
// CoCoChain Application Module Definition
//

package cocochain.applications;

import inet.applications.contract.IApp;

simple CoCoChainApp like IApp
{
    parameters:
        double messageInterval @unit(s) = default(1.5s);
        double corruptionProbability = default(0.1);
        double bftThreshold = default(0.67);
        bool semanticVerification = default(true);
        double maxTransactionAge @unit(s) = default(10s);
        
        // Statistics
        @signal[endToEndLatency](type=double);
        @signal[consensusOverhead](type=long);
        @signal[malformedDetected](type=long);
        
        @statistic[endToEndLatency](title="End-to-end confirmation latency"; unit=s; record=histogram,vector,mean,max);
        @statistic[consensusOverhead](title="Consensus message overhead"; record=sum,count);
        @statistic[malformedDetected](title="Malformed transactions detected"; record=sum,count);
        
        @display("i=block/app");
        
    gates:
        input socketIn @labels(UdpControlInfo/up);
        output socketOut @labels(UdpControlInfo/down);
}