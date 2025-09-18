# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Essential tools
    wget \
    curl \
    unzip \
    # For pandoc installation
    ca-certificates \
    # Java for EPUBCheck
    openjdk-17-jre-headless \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Pandoc
ARG PANDOC_VERSION=3.1.9
RUN wget https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-linux-amd64.tar.gz \
    && tar xvzf pandoc-${PANDOC_VERSION}-linux-amd64.tar.gz --strip-components 1 -C /usr/local/ \
    && rm pandoc-${PANDOC_VERSION}-linux-amd64.tar.gz

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install -e .[docx,pandoc]

# Install EPUBCheck through docx2shelf tools manager
RUN docx2shelf tools install epubcheck

# Create workspace directory for user files
WORKDIR /workspace

# Expose volume for user files
VOLUME ["/workspace"]

# Set default entrypoint
ENTRYPOINT ["docx2shelf"]
CMD ["--help"]