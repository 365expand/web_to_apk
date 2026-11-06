FROM eclipse-temurin:17-jdk-jammy

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH="${PATH}:${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools:${ANDROID_HOME}/build-tools/34.0.0"
ENV GRADLE_USER_HOME=/home/appuser/.gradle

# Install Python 3.12, software-properties-common, curl, unzip, git
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    unzip \
    git \
    libgl1 \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && rm -rf /var/lib/apt/lists/*

# Install Android Command Line Tools & SDK packages
RUN mkdir -p ${ANDROID_HOME}/cmdline-tools \
    && curl -o /tmp/cmdline-tools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip \
    && unzip /tmp/cmdline-tools.zip -d ${ANDROID_HOME}/cmdline-tools \
    && mv ${ANDROID_HOME}/cmdline-tools/cmdline-tools ${ANDROID_HOME}/cmdline-tools/latest \
    && rm /tmp/cmdline-tools.zip

# Accept licenses and install platform and build tools
RUN yes | sdkmanager --licenses \
    && sdkmanager "platforms;android-34" "build-tools;34.0.0" "platform-tools"

# Create non-root application user
RUN useradd -m -s /bin/bash appuser

# Setup application directory
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy Android template first to pre-warm the Gradle daemon and dependency cache
COPY android_templates /app/android_templates
RUN chown -R appuser:appuser /app ${ANDROID_HOME}

# Switch to non-root user and pre-warm Gradle cache
USER appuser
RUN cd /app/android_templates/webview \
    && echo "sdk.dir=${ANDROID_HOME}" > local.properties \
    && chmod +x gradlew \
    && ./gradlew assembleRelease --stacktrace || true \
    && ./gradlew clean

# Copy application source code
USER root
COPY . /app/backend
RUN chown -R appuser:appuser /app

USER appuser
WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

