#!/usr/bin/env python3
"""Read-only SMTP authentication check used by precheck_smtp.yml.

Performs STARTTLS (when requested) and LOGIN only, then disconnects. No
message is ever composed or sent, so this is safe to run repeatedly against
a production SMTP account. Credentials are read from the SMTP_USERNAME /
SMTP_PASSWORD environment variables rather than argv, so they never appear
in the process list or in Ansible's task output.
"""
import os
import smtplib
import ssl
import sys


def main():
    if len(sys.argv) != 4:
        print("Usage: smtp_auth_check.py <host> <port> <use_tls: true|false>")
        sys.exit(2)

    host = sys.argv[1]
    port = int(sys.argv[2])
    use_tls = sys.argv[3].lower() == "true"
    username = os.environ.get("SMTP_USERNAME", "")
    password = os.environ.get("SMTP_PASSWORD", "")

    try:
        server = smtplib.SMTP(host, port, timeout=10)
        server.ehlo()
        if use_tls:
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        if username:
            server.login(username, password)
        server.quit()
    except Exception as exc:  # noqa: BLE001 - report any failure to the operator
        print(f"SMTP authentication failed for {username}@{host}:{port} - {exc}")
        sys.exit(1)

    print(f"SMTP authentication succeeded for {username}@{host}:{port} (STARTTLS: {use_tls})")


if __name__ == "__main__":
    main()
