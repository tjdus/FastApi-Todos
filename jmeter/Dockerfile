FROM eclipse-temurin:11-jre-jammy

# Set JMeter version and environment variables
ARG JMETER_VERSION=5.6.2
ENV JMETER_HOME=/opt/apache-jmeter-${JMETER_VERSION}
ENV PATH="${JMETER_HOME}/bin:${PATH}"

# Install required dependencies
RUN apt-get update && \
    apt-get install -y wget unzip libjson-simple-java libcommons-lang3-java libcommons-io-java && \
    rm -rf /var/lib/apt/lists/*

# Download and extract Apache JMeter
RUN wget https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.zip && \
    unzip apache-jmeter-${JMETER_VERSION}.zip -d /opt && \
    rm apache-jmeter-${JMETER_VERSION}.zip

WORKDIR ${JMETER_HOME}

# Default command
CMD ["jmeter", "-v"]
