"""Local RabbitMQ worker simulator for XAI integration testing.

This script:
1) Connects to RabbitMQ.
2) Creates task/result queues if they do not exist.
3) Consumes messages from TASK_QUEUE.
4) Publishes simulated results to RESULT_QUEUE.

Usage:
    python backend/tests/test_endpoints/xai_rabbitmq_simulator.py

Optional environment variables:
    RABBIT_URL       (default: amqp://guest:guest@localhost/)
    TASK_QUEUE       (default: xai_jobs)
    RESULT_QUEUE     (default: xai_results)
    MESSAGE_VERSION  (default: 0.1)
    SIMULATOR_DELAY_SEC (default: 1.0)
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import aio_pika
from aio_pika import Message


RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@localhost/")
TASK_QUEUE = os.getenv("TASK_QUEUE", "xai_jobs")
RESULT_QUEUE = os.getenv("RESULT_QUEUE", "xai_results")
MESSAGE_VERSION = os.getenv("MESSAGE_VERSION", "0.1")
SIMULATOR_DELAY_SEC = float(os.getenv("SIMULATOR_DELAY_SEC", "1.0"))


def build_success_result(task_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a result payload compatible with backend update_xai_job."""
    job_id = task_payload.get("job_id")
    if not job_id:
        raise ValueError("Incoming task does not include required field 'job_id'")


    return {
        "job_id": str(job_id),
        "status": "completed",
        "result_location": f"ROK_TEST/xai_results/999/R-999999",
        "result_file_names": [
            "lime.json",
            "nearest_ticket.json",
        ],
        "version": MESSAGE_VERSION,
    }


async def main() -> None:
    print(f"[simulator] Connecting to RabbitMQ: {RABBIT_URL}")
    connection = await aio_pika.connect_robust(RABBIT_URL)

    async with connection:
        channel = await connection.channel()

        # Create queues so backend passive-consume does not fail on startup.
        await channel.declare_queue(TASK_QUEUE, durable=True)
        await channel.declare_queue(RESULT_QUEUE, durable=True)

        task_queue = await channel.declare_queue(TASK_QUEUE, durable=True)

        print(f"[simulator] Waiting for tasks on '{TASK_QUEUE}'")
        print(f"[simulator] Publishing simulated results to '{RESULT_QUEUE}'")

        async def on_task(message: aio_pika.abc.AbstractIncomingMessage) -> None:
            async with message.process():
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    print(f"[simulator] Invalid JSON task payload: {exc}")
                    return

                print(f"[simulator] Received task for job_id={payload.get('job_id')}")

                await asyncio.sleep(SIMULATOR_DELAY_SEC)

                result_payload = build_success_result(payload)

                await channel.default_exchange.publish(
                    Message(
                        body=json.dumps(result_payload).encode("utf-8"),
                        delivery_mode=2,
                    ),
                    routing_key=RESULT_QUEUE,
                )

                print(
                    f"[simulator] Published completed result for job_id={result_payload['job_id']}"
                )

        await task_queue.consume(on_task)

        # Keep running until interrupted.
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[simulator] Stopped")