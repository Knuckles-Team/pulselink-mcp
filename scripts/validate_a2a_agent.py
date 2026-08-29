#!/usr/bin/env python3
import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager

import httpx
from agent_utilities.core.transport_security import resolve_configured_tls_profile

A2A_URL = os.environ.get("A2A_URL", "")


@asynccontextmanager
async def configured_http_client():
    """Yield an HTTPX client under the runtime AgentConfig TLS policy."""
    profile = resolve_configured_tls_profile("pulselink")
    try:
        async with httpx.AsyncClient(
            timeout=10000.0,
            **profile.httpx_kwargs(),
        ) as client:
            yield client
    finally:
        profile.cleanup()


def _build_send_payload(query: str) -> dict:
    """Build the JSON-RPC ``message/send`` request body for one query."""
    return {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "role": "user",
                "parts": [{"kind": "text", "text": query}],
                "messageId": str(uuid.uuid4()),
            }
        },
        "id": 1,
    }


def _build_poll_payload(task_id) -> dict:
    """Build the JSON-RPC ``tasks/get`` request body for one task id."""
    return {
        "jsonrpc": "2.0",
        "method": "tasks/get",
        "params": {"id": task_id},
        "id": 2,
    }


def _last_non_user_message(history: list) -> dict | None:
    """Find the most recent non-user message in a task's history, if any."""
    for msg in reversed(history):
        if msg.get("role") != "user":
            return msg
    return None


def _print_message_parts(parts: list) -> None:
    """Report each text/content part of an agent message (body itself withheld)."""
    print("\n--- Agent Response ---")
    for part in parts:
        if "text" in part or "content" in part:
            print("Agent response content omitted.")


def _print_history_response(history: list) -> None:
    """Print the final non-user message found in a finished task's history."""
    if not history:
        return
    last_msg = _last_non_user_message(history)
    if last_msg and "parts" in last_msg:
        _print_message_parts(last_msg["parts"])
    elif last_msg:
        print("Final response received without structured parts.")
    else:
        print("\n--- No Agent Response Found in History ---")


def _print_task_finished(state: str, poll_result: dict) -> None:
    """Report a terminal task state and, if present, its history's final response."""
    print(f"\nTask Finished with state: {state}")
    if "history" in poll_result:
        _print_history_response(poll_result["history"])
    print("Validation result received; body omitted.")


def _handle_poll_result(poll_data: dict) -> bool:
    """Handle one successful ``tasks/get`` poll response.

    Returns True once the poll loop should stop (terminal state reached, or
    the response carried no ``result`` to keep polling from).
    """
    if "result" not in poll_data:
        print("Starting polling error key check...")
        if "error" in poll_data:
            print(
                f"Polling JSON-RPC error code: {poll_data['error'].get('code', 'unknown')}"
            )
        return True
    state = poll_data["result"]["status"]["state"]
    print(f"Task State: {state}")
    if state in ("submitted", "running", "working"):
        return False
    _print_task_finished(state, poll_data["result"])
    return True


async def _poll_task(client, url, task_id) -> None:
    """Poll ``tasks/get`` every 2s until the task reaches a terminal state."""
    while True:
        await asyncio.sleep(2)
        poll_resp = await client.post(
            url,
            json=_build_poll_payload(task_id),
            headers={"Content-Type": "application/json"},
        )
        if poll_resp.status_code != 200:
            print(f"Polling Failed: {poll_resp.status_code}")
            print(f"Polling failed with HTTP {poll_resp.status_code}.")
            return
        if _handle_poll_result(poll_resp.json()):
            return


async def _process_send_result(client, url, data: dict) -> None:
    """Handle the parsed ``message/send`` response: poll if a task, then report errors."""
    if "result" in data and "id" in data["result"]:
        task_id = data["result"]["id"]
        print("\nTask submitted; polling for result...")
        await _poll_task(client, url, task_id)
    if "error" in data:
        print(f"JSON-RPC error code: {data['error'].get('code', 'unknown')}")


async def _submit_query(client, url, query: str) -> None:
    """Send one validation query and report its result (and any polled task's)."""
    print("\nSubmitting the configured validation query.")
    print("--- Sending Request ---")
    payload = _build_send_payload(query)
    try:
        print("Trying the configured endpoint with JSON-RPC (message/send)...")
        resp = await client.post(
            url, json=payload, headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error: {resp.status_code}")
            print(f"Response body omitted (HTTP {resp.status_code}).")
            return
        try:
            data = resp.json()
            print("JSON response received.")
            await _process_send_result(client, url, data)
        except json.JSONDecodeError:
            print(f"Response body omitted (HTTP {resp.status_code}).")
    except httpx.RequestError as e:
        print(f"Operation failed: {type(e).__name__}")


async def main():
    if not A2A_URL:
        raise RuntimeError("A2A_URL is required")
    print("Validating the configured A2A agent...")

    questions = [
        os.environ.get("A2A_VALIDATION_QUERY", "Describe your available capabilities.")
    ]

    async with configured_http_client() as client:
        for q in questions:
            await _submit_query(client, A2A_URL, q)


if __name__ == "__main__":
    asyncio.run(main())
