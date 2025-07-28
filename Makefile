#
# CoCoChain Makefile
#

# OMNeT++ configuration
OMNETPP_ROOT ?= $(shell readlink -f $$(which omnetpp-config | head -1 | sed 's|/bin/omnetpp-config||'))
CONFIGFILE = $(OMNETPP_ROOT)/Makefile.inc
ifneq ("$(wildcard $(CONFIGFILE))","")
include $(CONFIGFILE)
endif

# Project configuration
TARGET = CoCoChain
SRCDIR = src
NEDDIR = ned

# Source files
SOURCES = $(wildcard $(SRCDIR)/*.cc) $(wildcard $(SRCDIR)/*.cpp)
HEADERS = $(wildcard $(SRCDIR)/*.h) $(wildcard $(SRCDIR)/*.hpp)

# Compiler flags
CXXFLAGS += -std=c++17 -Wall -Wextra

# Include paths
INCLUDE_PATH += -I$(SRCDIR)

# Dependencies
LIBS += -linet$(D)

# Veins support (optional)
ifdef VEINS_ROOT
INCLUDE_PATH += -I$(VEINS_ROOT)/src
LIBS += -lveins$(D)
endif

# Build targets
all: $(TARGET)

$(TARGET): $(SOURCES) $(HEADERS)
	@echo "Building $(TARGET)..."
	$(CXX) $(CXXFLAGS) $(INCLUDE_PATH) -o $@ $(SOURCES) $(LDFLAGS) $(LIBS)

clean:
	rm -f $(TARGET) *.o *_m.cc *_m.h results/*

run: $(TARGET)
	cd simulations && ../$(TARGET) -u Cmdenv -c General --repeat=10

analyze:
	cd scripts && python3 analyze_results.py

.PHONY: all clean run analyze