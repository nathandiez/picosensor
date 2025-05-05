docker compose exec timescaledb psql -U iotuser -d iotdb -c "SELECT * FROM sensor_data ORDER BY time DESC LIMIT 10;"
