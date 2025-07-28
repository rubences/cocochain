//
// CoCoChain Application Implementation
//

#include "CoCoChainApp.h"
#include <inet/common/ModuleAccess.h>
#include <inet/common/packet/Packet.h>
#include <inet/common/TimeTag.h>
#include <inet/networklayer/common/L3AddressResolver.h>
#include <cmath>
#include <algorithm>
#include <sstream>
#include <iomanip>

Define_Module(CoCoChainApp);

CoCoChainApp::CoCoChainApp() :
    localPort(9999),
    sendTimer(nullptr),
    transactionCounter(0),
    totalMessagesReceived(0),
    totalMalformedDetected(0),
    totalFalsePositives(0),
    totalValidTransactions(0),
    totalThroughput(0),
    lastThroughputUpdate(0),
    corruptionDist(0.0, 1.0),
    conceptDist(0.0, 1.0)
{
}

CoCoChainApp::~CoCoChainApp()
{
    cancelAndDelete(sendTimer);
}

void CoCoChainApp::initialize(int stage)
{
    ApplicationBase::initialize(stage);
    
    if (stage == INITSTAGE_LOCAL) {
        // Read parameters
        messageInterval = par("messageInterval");
        corruptionProbability = par("corruptionProbability");
        bftThreshold = par("bftThreshold").doubleValue();
        semanticVerification = par("semanticVerification");
        maxTransactionAge = par("maxTransactionAge");
        cosineSimilarityThreshold = par("cosineSimilarityThreshold").doubleValue();
        enablePbftComparison = par("enablePbftComparison").boolValue();
        
        // Initialize random number generator
        int seed = getRNG(0)->intRand();
        rng.seed(seed);
        
        // Register signals for statistics
        endToEndLatencySignal = registerSignal("endToEndLatency");
        consensusOverheadSignal = registerSignal("consensusOverhead");
        malformedDetectedSignal = registerSignal("malformedDetected");
        falsePositiveRateSignal = registerSignal("falsePositiveRate");
        throughputSignal = registerSignal("throughput");
        
        // Determine if this node is adversarial (10% of nodes)
        if (corruptionDist(rng) < corruptionProbability) {
            adversarialNodes.insert(getId());
            EV_INFO << "Node " << getId() << " configured as adversarial" << endl;
        }
        
        sendTimer = new cMessage("sendTimer");
    }
    else if (stage == INITSTAGE_APPLICATION_LAYER) {
        // Setup UDP socket
        socket.setOutputGate(gate("socketOut"));
        socket.setCallback(this);
        socket.bind(localPort);
        socket.setBroadcast(true);
        
        // Schedule first message
        scheduleAt(simTime() + uniform(0, messageInterval.dbl()), sendTimer);
    }
}

void CoCoChainApp::handleMessageWhenUp(cMessage *msg)
{
    if (msg == sendTimer) {
        sendTransaction();
        scheduleNextMessage();
    }
    else {
        ApplicationBase::handleMessageWhenUp(msg);
    }
}

void CoCoChainApp::socketDataArrived(UdpSocket *socket, Packet *packet)
{
    totalMessagesReceived++;
    emit(consensusOverheadSignal, 1); // Count each message as overhead
    
    // Extract message data (simplified - in real implementation would use proper serialization)
    auto chunk = packet->peekDataAt<BytesChunk>(B(0), packet->getDataLength());
    std::string data = chunk->getBytes().str();
    
    // Parse message type and content
    if (data.find("TRANSACTION:") == 0) {
        // Parse transaction
        Transaction tx;
        // Simplified parsing - in real implementation would use proper serialization
        std::istringstream iss(data.substr(12));
        iss >> tx.id >> tx.originator >> tx.timestamp;
        
        // Generate concept vector for this transaction
        tx.conceptVector = generateConceptVector();
        tx.semanticDigest = computeSemanticDigest(tx.conceptVector);
        
        processReceivedTransaction(tx);
    }
    else if (data.find("CONSENSUS:") == 0) {
        // Parse consensus message
        ConsensusMessage msg;
        std::istringstream iss(data.substr(10));
        int type;
        iss >> type >> msg.transactionId >> msg.senderId >> msg.vote >> msg.timestamp;
        msg.type = static_cast<ConsensusMessage::Type>(type);
        
        processConsensusMessage(msg);
    }
    
    delete packet;
}

void CoCoChainApp::socketErrorArrived(UdpSocket *socket, Indication *indication)
{
    EV_WARN << "Socket error: " << indication->str() << endl;
    delete indication;
}

void CoCoChainApp::socketClosed(UdpSocket *socket)
{
    // Socket closed
}

void CoCoChainApp::sendTransaction()
{
    Transaction tx;
    tx.id = ++transactionCounter + (getId() * 1000000ULL); // Ensure unique IDs
    tx.originator = getId();
    tx.timestamp = simTime().inUnit(SIMTIME_US);
    tx.conceptVector = generateConceptVector();
    
    // Apply corruption if this is an adversarial node
    if (isAdversarialNode()) {
        injectMalformedVector(tx.conceptVector);
    }
    
    tx.semanticDigest = computeSemanticDigest(tx.conceptVector);
    
    // Record start time for latency measurement
    transactionStartTimes[tx.id] = simTime();
    
    // Update throughput metrics
    totalThroughput++;
    updateThroughputMetrics();
    
    // Broadcast transaction
    std::ostringstream oss;
    oss << "TRANSACTION:" << tx.id << " " << tx.originator << " " << tx.timestamp;
    std::string data = oss.str();
    
    auto packet = new Packet("CoCoChainTransaction");
    packet->insertAtBack(makeShared<BytesChunk>(reinterpret_cast<const uint8_t*>(data.c_str()), data.length()));
    
    socket.sendTo(packet, Ipv4Address::ALLONES_ADDRESS, localPort);
    
    EV_INFO << "Sent transaction " << tx.id << " with " << 
               (tx.conceptVector.isCorrupted ? "corrupted" : "clean") << " concept vector" << endl;
}

void CoCoChainApp::processReceivedTransaction(const Transaction& tx)
{
    // Skip our own transactions
    if (tx.originator == getId()) return;
    
    // Check if transaction is too old
    simtime_t age = simTime() - SimTime(tx.timestamp, SIMTIME_US);
    if (age > maxTransactionAge) {
        EV_INFO << "Dropping old transaction " << tx.id << endl;
        return;
    }
    
    // Process with both PBFT and CoCoChain if comparison is enabled
    bool cocoChainResult = processCocoChainConsensus(tx);
    
    if (enablePbftComparison) {
        bool pbftResult = processPbftConsensus(tx);
        EV_INFO << "Transaction " << tx.id << " - PBFT: " << pbftResult 
                << ", CoCoChain: " << cocoChainResult << endl;
    }
    
    if (!cocoChainResult) {
        EV_INFO << "Detected and rejected malformed transaction " << tx.id << endl;
        return;
    }
    
    // Store transaction and start consensus
    pendingTransactions[tx.id] = tx;
    startConsensus(tx);
}

void CoCoChainApp::startConsensus(const Transaction& tx)
{
    // Create and send vote message
    ConsensusMessage vote;
    vote.type = ConsensusMessage::VOTE;
    vote.transactionId = tx.id;
    vote.senderId = getId();
    vote.vote = verifySemanticIntegrity(tx); // Vote based on verification
    vote.timestamp = simTime().inUnit(SIMTIME_US);
    
    // Broadcast vote
    std::ostringstream oss;
    oss << "CONSENSUS:" << static_cast<int>(vote.type) << " " << vote.transactionId << " " 
        << vote.senderId << " " << vote.vote << " " << vote.timestamp;
    std::string data = oss.str();
    
    auto packet = new Packet("CoCoChainConsensus");
    packet->insertAtBack(makeShared<BytesChunk>(reinterpret_cast<const uint8_t*>(data.c_str()), data.length()));
    
    socket.sendTo(packet, Ipv4Address::ALLONES_ADDRESS, localPort);
    
    EV_INFO << "Sent " << (vote.vote ? "positive" : "negative") << " vote for transaction " << tx.id << endl;
}

void CoCoChainApp::processConsensusMessage(const ConsensusMessage& msg)
{
    if (msg.type != ConsensusMessage::VOTE) return;
    
    // Store vote
    consensusVotes[msg.transactionId].push_back(msg);
    
    // Check if we have enough votes to reach consensus
    auto& votes = consensusVotes[msg.transactionId];
    int totalVotes = votes.size();
    int positiveVotes = 0;
    
    for (const auto& vote : votes) {
        if (vote.vote) positiveVotes++;
    }
    
    // Need to estimate total network size for BFT threshold
    // For simplicity, use a conservative estimate
    int estimatedNetworkSize = 100; // Conservative estimate of local neighborhood
    int requiredVotes = static_cast<int>(estimatedNetworkSize * bftThreshold);
    
    if (totalVotes >= requiredVotes) {
        bool consensus = (positiveVotes >= requiredVotes);
        
        if (consensus) {
            finalizeTransaction(msg.transactionId);
        } else {
            // Transaction rejected by consensus
            pendingTransactions.erase(msg.transactionId);
            consensusVotes.erase(msg.transactionId);
            EV_INFO << "Transaction " << msg.transactionId << " rejected by consensus" << endl;
        }
    }
}

void CoCoChainApp::finalizeTransaction(uint64_t txId)
{
    if (confirmedTransactions.count(txId)) return; // Already confirmed
    
    confirmedTransactions.insert(txId);
    
    // Record end-to-end latency if we initiated this transaction
    if (transactionStartTimes.count(txId)) {
        simtime_t latency = simTime() - transactionStartTimes[txId];
        emit(endToEndLatencySignal, latency.dbl());
        transactionStartTimes.erase(txId);
        EV_INFO << "Transaction " << txId << " confirmed with latency " << latency << "s" << endl;
    }
    
    // Clean up
    pendingTransactions.erase(txId);
    consensusVotes.erase(txId);
}

ConceptVector CoCoChainApp::generateConceptVector()
{
    ConceptVector cv;
    cv.nodeId = getId();
    cv.timestamp = simTime().inUnit(SIMTIME_US);
    cv.isCorrupted = false;
    
    // Generate random concept vector (simplified)
    cv.data.resize(10); // 10-dimensional concept space
    for (int i = 0; i < 10; i++) {
        cv.data[i] = conceptDist(rng);
    }
    
    return cv;
}

void CoCoChainApp::corruptConceptVector(ConceptVector& cv)
{
    cv.isCorrupted = true;
    // Introduce systematic corruption
    for (auto& val : cv.data) {
        val *= (1.0 + uniform(-0.5, 0.5)); // Add noise
    }
}

std::string CoCoChainApp::computeSemanticDigest(const ConceptVector& cv)
{
    // Simplified semantic digest using hash of concept vector
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(6);
    for (const auto& val : cv.data) {
        oss << val << ";";
    }
    
    std::string data = oss.str();
    std::hash<std::string> hasher;
    size_t hash = hasher(data);
    
    std::ostringstream result;
    result << std::hex << hash;
    return result.str();
}

bool CoCoChainApp::verifySemanticIntegrity(const Transaction& tx)
{
    if (!semanticVerification) return true;
    
    // Recompute semantic digest and compare
    std::string computedDigest = computeSemanticDigest(tx.conceptVector);
    bool isValid = (computedDigest == tx.semanticDigest);
    
    // Additional checks for malformed vectors
    if (isValid) {
        // Check for obvious corruption patterns
        double variance = 0.0;
        double mean = 0.0;
        for (const auto& val : tx.conceptVector.data) {
            mean += val;
        }
        mean /= tx.conceptVector.data.size();
        
        for (const auto& val : tx.conceptVector.data) {
            variance += (val - mean) * (val - mean);
        }
        variance /= tx.conceptVector.data.size();
        
        // Flag as malformed if variance is too high (indicating corruption)
        if (variance > 2.0) {
            isValid = false;
        }
        
        // Additional cosine similarity check for top-k concepts
        if (isValid && isTopKConcept(tx.conceptVector)) {
            ConceptVector refVector = generateConceptVector();
            double similarity = calculateCosineSimilarity(tx.conceptVector.data, refVector.data);
            
            if (similarity < cosineSimilarityThreshold) {
                isValid = false;
            }
        }
    }
    
    return isValid;
}

bool CoCoChainApp::isAdversarialNode()
{
    return adversarialNodes.count(getId()) > 0;
}

void CoCoChainApp::injectMalformedVector(ConceptVector& cv)
{
    corruptConceptVector(cv);
    // Additional malicious modifications for top-k concept manipulation
    if (uniform(0, 1) < 0.5) {
        // Inject extreme values
        int idx = intuniform(0, cv.data.size() - 1);
        cv.data[idx] = uniform(-10, 10);
    }
    
    // Mark as top-k manipulation if appropriate
    if (uniform(0, 1) < 0.3) {
        cv.isTopK = true;
        manipulateTopKVector(cv);
    }
}

double CoCoChainApp::calculateCosineSimilarity(const std::vector<double>& a, const std::vector<double>& b)
{
    if (a.size() != b.size()) return 0.0;
    
    double dotProduct = 0.0;
    double normA = 0.0;
    double normB = 0.0;
    
    for (size_t i = 0; i < a.size(); i++) {
        dotProduct += a[i] * b[i];
        normA += a[i] * a[i];
        normB += b[i] * b[i];
    }
    
    if (normA == 0.0 || normB == 0.0) return 0.0;
    
    return dotProduct / (sqrt(normA) * sqrt(normB));
}

bool CoCoChainApp::isTopKConcept(const ConceptVector& cv)
{
    // Check if concept vector represents a top-k concept
    // For simplicity, we consider it top-k if any dimension exceeds threshold
    for (const auto& val : cv.data) {
        if (abs(val) > 0.8) return true;
    }
    return cv.isTopK;
}

void CoCoChainApp::manipulateTopKVector(ConceptVector& cv)
{
    // Adversaries inject manipulated top-k concept vectors
    cv.isTopK = true;
    cv.isCorrupted = true;
    
    // Find the highest value and manipulate it
    auto maxIt = std::max_element(cv.data.begin(), cv.data.end());
    if (maxIt != cv.data.end()) {
        *maxIt = *maxIt * uniform(1.5, 3.0); // Amplify the top concept
    }
    
    // Add subtle noise to other dimensions
    for (auto& val : cv.data) {
        if (&val != &(*maxIt)) {
            val += uniform(-0.1, 0.1);
        }
    }
}

bool CoCoChainApp::processPbftConsensus(const Transaction& tx)
{
    // Simplified PBFT consensus simulation
    // In real PBFT: Pre-prepare, Prepare, Commit phases
    
    // Basic verification without semantic checking
    bool isValid = !tx.conceptVector.isCorrupted;
    
    // PBFT requires 2f+1 nodes for f faulty nodes
    // Assume 1/3 can be faulty, so need 2/3 agreement
    double pbftThreshold = 0.67;
    
    // Simulate consensus with basic checks
    if (uniform(0, 1) < pbftThreshold) {
        return isValid;
    }
    
    return false;
}

bool CoCoChainApp::processCocoChainConsensus(const Transaction& tx)
{
    // CoCoChain consensus with semantic verification
    if (!verifySemanticIntegrity(tx)) {
        return false;
    }
    
    // Additional cosine similarity check for top-k concepts
    if (isTopKConcept(tx.conceptVector)) {
        // Generate reference vector for comparison
        ConceptVector refVector = generateConceptVector();
        double similarity = calculateCosineSimilarity(tx.conceptVector.data, refVector.data);
        
        if (similarity < cosineSimilarityThreshold) {
            // Mark as potential false positive if it's actually valid
            if (!tx.conceptVector.isCorrupted) {
                totalFalsePositives++;
                updateFalsePositiveRate(true, true);
            }
            return false;
        }
    }
    
    // Update metrics
    if (tx.conceptVector.isCorrupted) {
        totalMalformedDetected++;
        emit(malformedDetectedSignal, 1);
    } else {
        totalValidTransactions++;
        updateFalsePositiveRate(true, false);
    }
    
    return true;
}

void CoCoChainApp::updateThroughputMetrics()
{
    simtime_t currentTime = simTime();
    if (currentTime - lastThroughputUpdate >= 1.0) { // Update every second
        emit(throughputSignal, totalThroughput);
        totalThroughput = 0;
        lastThroughputUpdate = currentTime;
    }
}

void CoCoChainApp::updateFalsePositiveRate(bool wasValid, bool wasRejected)
{
    // FPR = False Positives / (False Positives + True Negatives)
    // False Positive: Valid transaction incorrectly rejected
    if (wasValid && wasRejected) {
        totalFalsePositives++;
    }
    
    // Calculate and emit FPR periodically
    if ((totalValidTransactions + totalMalformedDetected) > 0) {
        double fpr = static_cast<double>(totalFalsePositives) / 
                    static_cast<double>(totalValidTransactions + totalFalsePositives);
        emit(falsePositiveRateSignal, fpr);
    }
}

void CoCoChainApp::scheduleNextMessage()
{
    scheduleAt(simTime() + messageInterval + uniform(-0.1, 0.1), sendTimer);
}

void CoCoChainApp::finish()
{
    // Record final statistics
    recordScalar("Total messages received", totalMessagesReceived);
    recordScalar("Total malformed detected", totalMalformedDetected);
    recordScalar("Total false positives", totalFalsePositives);
    recordScalar("Total valid transactions", totalValidTransactions);
    recordScalar("Confirmed transactions", confirmedTransactions.size());
    
    // Calculate final FPR
    if ((totalValidTransactions + totalFalsePositives) > 0) {
        double finalFpr = static_cast<double>(totalFalsePositives) / 
                         static_cast<double>(totalValidTransactions + totalFalsePositives);
        recordScalar("Final FPR", finalFpr);
    }
    
    ApplicationBase::finish();
}