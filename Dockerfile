FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install ROCm
RUN wget -qO - https://repo.radeon.com/rocm/rocm.gpg.key | apt-key add - && \
    echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/debian/ ubuntu main' | tee /etc/apt/sources.list.d/rocm.list && \
    apt-get update && apt-get install -y rocm-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Run the application
CMD ["python3", "run_kde_ai_interface.py"]
