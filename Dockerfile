FROM docker-hub.common.cdn.repositories.cloud.sap/python:3.13

ARG ARTIFACTORY_USER
ARG ARTIFACTORY_TOKEN

ENV ARTIFACTORY_URL="https://common.repositories.cloud.sap/artifactory/api/pypi/application-foundation-sdk-python"
ENV ARTIFACTORY_USER=${ARTIFACTORY_USER}
ENV ARTIFACTORY_TOKEN=${ARTIFACTORY_TOKEN}

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    mkdir -p /root/.pip && \
    printf "[global]\n\
index-url = https://%s:%s@common.repositories.cloud.sap/artifactory/api/pypi/application-foundation-sdk-python/simple\n\
extra-index-url = https://pypi.org/simple\n" \
    "$ARTIFACTORY_USER" "$ARTIFACTORY_TOKEN" > /root/.pip/pip.conf && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.pip

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

CMD ["python", "src/app/main.py", "--host", "0.0.0.0", "--port", "5000"]
