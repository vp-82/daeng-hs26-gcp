FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Schlägt ein Modell oder Test fehl, endet dbt mit Exit-Code ungleich null und damit auch der Job.
CMD ["dbt", "build", "--profiles-dir", ".", "--target", "prod"]
