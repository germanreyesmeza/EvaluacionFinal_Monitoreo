#!/usr/bin/env python3
import time
import random
import argparse
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Counter,
    Histogram,
    Summary,
    pushadd_to_gateway,
)


def build_registry(registry):
    # 1. Clientes y Capacidad (Gauges)
    registry.isp_active_customers_gauge = Gauge(
        "isp_active_customers_gauge",
        "Active connected customers",
        ["region"],
        registry=registry,
    )
    registry.isp_peak_users_gauge = Gauge(
        "isp_peak_users_gauge",
        "Peak concurrent users observed in the last interval",
        registry=registry,
    )
    registry.isp_current_bandwidth_mbps_gauge = Gauge(
        "isp_current_bandwidth_mbps_gauge",
        "Current total bandwidth usage (instantaneous Mbps)",
        registry=registry,
    )
    registry.isp_routers_online_gauge = Gauge(
        "isp_routers_online_gauge",
        "Routers online count",
        registry=registry,
    )

    # 2. Red y Rendimiento (Counters & Histograms)
    registry.isp_packets_dropped_total = Counter(
        "isp_packets_dropped_total",
        "Total packets dropped",
        ["router"],
        registry=registry,
    )
    registry.isp_throughput_bytes_total = Counter(
        "isp_throughput_bytes_total",
        "Total throughput bytes (ingress + egress)",
        registry=registry,
    )
    registry.isp_connection_errors_total = Counter(
        "isp_connection_errors_total",
        "Connection errors total",
        ["protocol"],
        registry=registry,
    )
    registry.isp_bandwidth_usage_mbps_histogram = Histogram(
        "isp_bandwidth_usage_mbps_histogram",
        "Bandwidth distribution in Mbps",
        buckets=[1, 5, 10, 50, 100, 500, 1000, float("inf")],
        registry=registry,
    )
    registry.isp_latency_ms_histogram = Histogram(
        "isp_latency_ms_histogram",
        "Latency distribution ms (ping time)",
        buckets=[1, 5, 10, 20, 50, 100, 500, float("inf")],
        registry=registry,
    )

    # 3. Calidad de Servicio (QoS) y Fallas
    registry.isp_average_latency_ms_gauge = Gauge(
        "isp_average_latency_ms_gauge",
        "Average network latency ms",
        ["region"],
        registry=registry,
    )
    registry.isp_avg_jitter_ms_gauge = Gauge(
        "isp_avg_jitter_ms_gauge",
        "Average jitter ms",
        registry=registry,
    )
    registry.isp_outages_total = Counter(
        "isp_outages_total",
        "Total outages recorded",
        ["cause"],
        registry=registry,
    )
    registry.isp_reconnects_total = Counter(
        "isp_reconnects_total",
        "Customer device reconnect events",
        registry=registry,
    )
    registry.isp_sla_violations_total = Counter(
        "isp_sla_violations_total",
        "SLA violations (e.g., uptime, delivery time)",
        registry=registry,
    )
    registry.isp_customer_complaints_total = Counter(
        "isp_customer_complaints_total",
        "Customer complaints",
        ["topic"],
        registry=registry,
    )
    registry.isp_repair_time_hours_summary = Summary(
        "isp_repair_time_hours_summary",
        "Repair time hours summary (MTTR)",
        registry=registry,
    )

    # 4. Métricas agregadas de usuarios (nuevas)
    registry.isp_connected_users_gauge = Gauge(
        "isp_connected_users_gauge",
        "Total de usuarios conectados en la red (suma de todas las regiones)",
        registry=registry,
    )
    registry.isp_users_with_issues_gauge = Gauge(
        "isp_users_with_issues_gauge",
        "Total de usuarios con problemas de servicio",
        registry=registry,
    )
    registry.isp_delinquent_users_gauge = Gauge(
        "isp_delinquent_users_gauge",
        "Total de usuarios con cuentas impagas",
        registry=registry,
    )

    return registry


def simulate_and_push(args):
    registry = CollectorRegistry()
    registry = build_registry(registry)

    regions = ["north", "south", "east", "west"]
    routers = ["core_r1", "core_r2", "edge_r3", "edge_r4"]
    complaint_topics = ["speed", "outage", "billing"]

    while True:
        # --- 1. Clientes y Capacidad (Gauges) ---
        peak_users = random.randint(20000, 120000)
        registry.isp_peak_users_gauge.set(peak_users)
        registry.isp_current_bandwidth_mbps_gauge.set(random.uniform(100, 5000))
        registry.isp_routers_online_gauge.set(random.randint(4, 12))

        # Calcular usuarios conectados totales y derivados
        total_connected_users = 0

        for r in regions:
            active_customers = random.randint(10000, 90000)
            total_connected_users += active_customers

            registry.isp_active_customers_gauge.labels(region=r).set(active_customers)
            # Gauges de promedio
            registry.isp_average_latency_ms_gauge.labels(region=r).set(
                random.uniform(5, 120)
            )

        # 4. Métricas agregadas de usuarios (totales)
        registry.isp_connected_users_gauge.set(total_connected_users)

        # Supongamos un % aleatorio de usuarios con problemas (1% a 5%)
        users_with_issues = int(total_connected_users * random.uniform(0.01, 0.05))
        registry.isp_users_with_issues_gauge.set(users_with_issues)

        # Supongamos un % aleatorio de usuarios impagos (0.5% a 2%)
        delinquent_users = int(total_connected_users * random.uniform(0.005, 0.02))
        registry.isp_delinquent_users_gauge.set(delinquent_users)

        # --- 2. Red y Rendimiento (Counters & Histograms) ---
        for rt in routers:
            registry.isp_packets_dropped_total.labels(router=rt).inc(
                random.randint(0, 500)
            )

        # Throughput total
        registry.isp_throughput_bytes_total.inc(
            random.randint(1_000_000_000, 10_000_000_000)
        )

        # Errores de conexión (ej. DHCP, PPPoE)
        registry.isp_connection_errors_total.labels(protocol="dhcp").inc(
            random.randint(0, 50)
        )

        # Latency & Bandwidth distributions
        for _ in range(random.randint(10, 50)):
            registry.isp_bandwidth_usage_mbps_histogram.observe(
                random.uniform(1, 800)
            )
            registry.isp_latency_ms_histogram.observe(random.uniform(1, 400))

        # Jitter
        registry.isp_avg_jitter_ms_gauge.set(random.uniform(0.1, 30))

        # --- 3. Calidad de Servicio (QoS) y Fallas ---
        if random.random() < 0.05:
            # Outage event
            registry.isp_outages_total.labels(cause="fiber_cut").inc()
            registry.isp_repair_time_hours_summary.observe(random.uniform(0.5, 24))

        registry.isp_reconnects_total.inc(random.randint(0, 300))

        if random.random() < 0.02:
            registry.isp_sla_violations_total.inc()

        # Quejas de clientes
        complaints = random.randint(0, 5)
        if complaints > 0:
            topic = random.choice(complaint_topics)
            registry.isp_customer_complaints_total.labels(topic=topic).inc(complaints)

        # --- Push al Pushgateway ---
        instance = args.instance or "telecom-sim-1"
        try:
            pushadd_to_gateway(
                args.pushgateway,
                job=args.job,
                registry=registry,
                grouping_key={"instance": instance},
            )
            print(
                f"Pushed metrics to {args.pushgateway} "
                f"(job={args.job}, instance={instance}) "
                f"at {time.strftime('%H:%M:%S')}"
            )
        except Exception as e:
            print(f"Error pushing to Pushgateway: {e}")

        time.sleep(args.interval)


def main():
    parser = argparse.ArgumentParser(
        description="Telecom metrics simulator (push to Pushgateway)"
    )
    parser.add_argument(
        "--pushgateway", default="http://localhost:9091", help="Pushgateway URL"
    )
    parser.add_argument(
        "--job", default="telecom_job", help="Pushgateway job name"
    )
    parser.add_argument(
        "--instance",
        default="telecom-sim-1",
        help="Instance label to push (grouping_key)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Seconds between pushes",
    )
    args = parser.parse_args()

    simulate_and_push(args)


if __name__ == "__main__":
    main()