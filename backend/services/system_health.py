import os
import psutil
import time
from datetime import datetime, timezone


class SystemHealth:
    """Real system metrics and service health monitoring."""

    HEALTH_OPERATIONAL = "operational"
    HEALTH_WARNING = "warning"
    HEALTH_DEGRADED = "degraded"
    HEALTH_OFFLINE = "offline"

    @staticmethod
    def get_system_metrics() -> dict:
        """
        Get real system metrics: CPU, RAM, disk, network.

        Returns dict with current system utilization.
        """
        try:
            # CPU percent (1 second sampling for accuracy)
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory info
            mem = psutil.virtual_memory()
            memory_used_gb = mem.used / (1024 ** 3)
            memory_total_gb = mem.total / (1024 ** 3)
            memory_percent = mem.percent

            # Disk info - check root and common paths
            disk_usage = {}
            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        "total_gb": usage.total / (1024 ** 3),
                        "used_gb": usage.used / (1024 ** 3),
                        "free_gb": usage.free / (1024 ** 3),
                        "percent": usage.percent,
                    }
                except Exception:
                    pass

            # Network I/O
            net = psutil.net_io_counters()
            network = {
                "bytes_sent": net.bytes_sent,
                "bytes_received": net.bytes_recv,
                "packets_sent": net.packets_sent,
                "packets_received": net.packets_recv,
            }

            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "used_gb": round(memory_used_gb, 2),
                    "total_gb": round(memory_total_gb, 2),
                    "percent": memory_percent,
                },
                "disk": disk_usage,
                "network": network,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    @staticmethod
    def check_service_health(service_name: str, service_func) -> dict:
        """
        Check the health of a specific service.

        Args:
            service_name: Name of the service for display
            service_func: Function that returns True if healthy, False otherwise

        Returns:
            dict with service name, status, and details
        """
        try:
            is_healthy = service_func()
            timestamp = datetime.now(timezone.utc).isoformat()

            if is_healthy:
                return {
                    "service": service_name,
                    "status": SystemHealth.HEALTH_OPERATIONAL,
                    "timestamp": timestamp,
                    "details": "Service functioning normally",
                }
            else:
                return {
                    "service": service_name,
                    "status": SystemHealth.HEALTH_DEGRADED,
                    "timestamp": timestamp,
                    "details": "Service experiencing issues",
                }
        except Exception as e:
            timestamp = datetime.now(timezone.utc).isoformat()
            return {
                "service": service_name,
                "status": SystemHealth.HEALTH_OFFLINE,
                "timestamp": timestamp,
                "details": f"Service check failed: {str(e)}",
            }

    @staticmethod
    def get_overall_health(service_checks: dict) -> dict:
        """
        Determine overall system health based on individual service checks.

        Health hierarchy (worst to best):
        OFFLINE < DEGRADED < WARNING < OPERATIONAL

        Args:
            service_checks: dict of service_name -> health status

        Returns:
            dict with overall status and details
        """
        status_order = {
            SystemHealth.HEALTH_OFFLINE: 0,
            SystemHealth.HEALTH_DEGRADED: 1,
            SystemHealth.HEALTH_WARNING: 2,
            SystemHealth.HEALTH_OPERATIONAL: 3,
        }

        # Find the worst status
        worst_status = SystemHealth.HEALTH_OPERATIONAL
        worst_score = 3

        for service, status in service_checks.items():
            score = status_order.get(status, 3)
            if score < worst_score:
                worst_score = score
                worst_status = status

        # Generate details
        unhealthy_services = [
            s for s, st in service_checks.items()
            if st in (SystemHealth.HEALTH_DEGRADED, SystemHealth.HEALTH_OFFLINE)
        ]

        details = []
        if unhealthy_services:
            details.append(f"{len(unhealthy_services)} service(s) unhealthy: {', '.join(unhealthy_services)}")
        details.append(f"System overall: {worst_status}")

        return {
            "overall_status": worst_status,
            "health_score": worst_score,
            "details": " | ".join(details),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "unhealthy_count": len(unhealthy_services),
            "total_services": len(service_checks),
        }