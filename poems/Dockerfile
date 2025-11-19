FROM juancho926/customubuntu:2.1

WORKDIR /app

# Update package list and install Python3 and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

# Copy application code
COPY node.py .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python3", "node.py"]
