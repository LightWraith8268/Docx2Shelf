"""Enterprise feature command handlers - extracted from cli.py."""

from __future__ import annotations

import argparse
from pathlib import Path


def run_enterprise(args) -> int:
    """Handle enterprise subcommands."""
    try:
        if args.enterprise_cmd == "batch":
            return run_enterprise_batch(args)
        elif args.enterprise_cmd == "jobs":
            return run_enterprise_jobs(args)
        elif args.enterprise_cmd == "config":
            return run_enterprise_config(args)
        elif args.enterprise_cmd == "users":
            return run_enterprise_users(args)
        elif args.enterprise_cmd == "api":
            return run_enterprise_api(args)
        elif args.enterprise_cmd == "webhooks":
            return run_enterprise_webhooks(args)
        elif args.enterprise_cmd == "reports":
            return run_enterprise_reports(args)
        else:
            print(f"Unknown enterprise command: {args.enterprise_cmd}")
            return 1
    except Exception as e:
        print(f"Error running enterprise command: {e}")
        return 1


def run_enterprise_batch(args) -> int:
    """Handle enterprise batch processing."""
    try:
        import json
        import uuid

        import yaml

        from ..enterprise import BatchJob, get_batch_processor

        # Load configuration if provided
        config = {}
        if args.config:
            config_path = Path(args.config)
            if config_path.exists():
                try:
                    if (
                        config_path.suffix.lower() == ".yaml"
                        or config_path.suffix.lower() == ".yml"
                    ):
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = yaml.safe_load(f) or {}
                    else:
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load config file: {e}")

        # Apply command line overrides
        config.update(
            {
                "theme": args.theme,
                "split_at": args.split_at,
                "title": config.get("title", ""),
                "author": config.get("author", ""),
                "language": config.get("language", "en"),
                "toc_depth": config.get("toc_depth", 2),
                "hyphenate": config.get("hyphenate", True),
                "justify": config.get("justify", True),
            }
        )

        # Create batch job
        job = BatchJob(
            id=str(uuid.uuid4()),
            name=args.name,
            input_pattern=args.input,
            output_directory=args.output,
            config=config,
            processing_mode=args.mode,
            webhook_url=args.webhook,
        )

        # Submit to batch processor
        processor = get_batch_processor()

        # Update max concurrent jobs if specified
        if args.max_concurrent:
            processor.config.max_concurrent_jobs = args.max_concurrent

        job_id = processor.submit_batch_job(job)

        print(f"✓ Batch job '{args.name}' created successfully")
        print(f"  Job ID: {job_id}")
        print(f"  Mode: {args.mode}")
        print(f"  Input: {args.input}")
        print(f"  Output: {args.output}")

        if args.webhook:
            print(f"  Webhook: {args.webhook}")

        print(f"\nUse 'docx2shelf enterprise jobs --details {job_id}' to check status")
        return 0

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        print("Install with: pip install docx2shelf[enterprise]")
        return 1
    except Exception as e:
        print(f"Error creating batch job: {e}")
        return 1


def run_enterprise_jobs(args) -> int:
    """Handle enterprise job management."""
    try:
        from ..enterprise import get_batch_processor

        processor = get_batch_processor()

        if args.list:
            jobs = processor.list_jobs(status_filter=args.status)

            if not jobs:
                print("No batch jobs found")
                return 0

            print(
                f"{'Job ID':<36} {'Name':<20} {'Mode':<8} {'Status':<12} {'Progress':<10} {'Created'}"
            )
            print("-" * 100)

            for job in jobs:
                created = (
                    job.created_at[:19]
                    if isinstance(job.created_at, str)
                    else str(job.created_at)[:19]
                )
                print(
                    f"{job.id:<36} {job.name[:19]:<20} {job.processing_mode:<8} {job.status:<12} {job.progress:>3}% {created}"
                )

            return 0

        elif args.details:
            job = processor.get_job_status(args.details)
            if not job:
                print(f"Job not found: {args.details}")
                return 1

            print(f"Job Details: {job.name}")
            print("=" * 50)
            print(f"ID: {job.id}")
            print(f"Name: {job.name}")
            print(f"Mode: {job.processing_mode}")
            print(f"Status: {job.status}")
            print(f"Progress: {job.progress}%")
            print(f"Input: {job.input_pattern}")
            print(f"Output: {job.output_directory}")
            print(f"Created: {job.created_at}")

            if job.started_at:
                print(f"Started: {job.started_at}")
            if job.completed_at:
                print(f"Completed: {job.completed_at}")

            print("\nProgress Details:")
            print(f"  Total Items: {job.total_items}")
            print(f"  Processed: {job.processed_items}")
            print(f"  Failed: {job.failed_items}")
            print(f"  Total Files: {job.total_files}")
            print(f"  Files Processed: {job.processed_files}")
            print(f"  Files Failed: {job.failed_files}")

            if job.processing_mode == "books" and job.book_results:
                print("\nBook Results:")
                for book_name, result in job.book_results.items():
                    print(f"  {book_name}: {result['status']}")

            if job.error_log:
                print("\nRecent Errors:")
                for error in job.error_log[-5:]:
                    print(f"  - {error}")

            return 0

        elif args.cancel:
            success = processor.cancel_job(args.cancel)
            if success:
                print(f"✓ Job {args.cancel} cancelled successfully")
                return 0
            else:
                print(f"✗ Could not cancel job {args.cancel} (may have already completed)")
                return 1

        elif args.cleanup:
            cleaned = processor.cleanup_old_jobs()
            print(f"✓ Cleaned up {cleaned} old jobs")
            return 0

        else:
            print("Please specify an action: --list, --details <id>, --cancel <id>, or --cleanup")
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error managing jobs: {e}")
        return 1


def run_enterprise_config(args) -> int:
    """Handle enterprise configuration."""
    try:
        from ..enterprise import get_config_manager

        config_manager = get_config_manager()

        if args.init:
            # Initialize default configuration
            config_manager.reset_to_defaults()
            print("✓ Enterprise configuration initialized with defaults")
            print(f"Configuration saved to: {config_manager.config_path}")
            return 0

        elif args.show:
            config = config_manager.config
            print("Enterprise Configuration:")
            print("=" * 30)
            print(f"Max Concurrent Jobs: {config.max_concurrent_jobs}")
            print(f"Max Files Per Job: {config.max_files_per_job}")
            print(f"Job Timeout (hours): {config.job_timeout_hours}")
            print(f"Auto Cleanup (days): {config.auto_cleanup_days}")
            print(f"Enable Webhooks: {config.enable_webhooks}")
            print(f"Enable API: {config.enable_api}")
            print(f"API Host: {config.api_host}")
            print(f"API Port: {config.api_port}")
            print(f"Log Level: {config.log_level}")
            return 0

        elif args.set:
            key, value = args.set

            # Convert value to appropriate type
            if key in [
                "max_concurrent_jobs",
                "max_files_per_job",
                "job_timeout_hours",
                "auto_cleanup_days",
                "api_port",
            ]:
                value = int(value)
            elif key in ["enable_webhooks", "enable_api"]:
                value = value.lower() in ["true", "1", "yes", "on"]

            config_manager.update_config(**{key: value})
            print(f"✓ Configuration updated: {key} = {value}")
            return 0

        elif args.reset:
            config_manager.reset_to_defaults()
            print("✓ Configuration reset to defaults")
            return 0

        elif args.export:
            import shutil

            shutil.copy2(config_manager.config_path, args.export)
            print(f"✓ Configuration exported to: {args.export}")
            return 0

        elif args.import_config:
            import shutil

            shutil.copy2(args.import_config, config_manager.config_path)
            config_manager.config = config_manager._load_config()
            print(f"✓ Configuration imported from: {args.import_config}")
            return 0

        else:
            print(
                "Please specify an action: --init, --show, --set KEY VALUE, --reset, --export FILE, or --import FILE"
            )
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error managing configuration: {e}")
        return 1


def run_enterprise_users(args) -> int:
    """Handle enterprise user management."""
    try:
        from ..enterprise import get_user_manager

        user_manager = get_user_manager()

        if args.create:
            if not args.email:
                print("Error: --email is required when creating a user")
                return 1

            permissions = []
            if args.permissions:
                permissions = [p.strip() for p in args.permissions.split(",")]

            user = user_manager.create_user(
                username=args.create, email=args.email, role=args.role, permissions=permissions
            )

            print("✓ User created successfully")
            print(f"  ID: {user.id}")
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  API Key: {user.api_key}")
            print(f"  Permissions: {', '.join(user.permissions)}")
            return 0

        elif args.list:
            users = user_manager.list_users()

            if not users:
                print("No users found")
                return 0

            print(f"{'Username':<20} {'Email':<30} {'Role':<10} {'Created'}")
            print("-" * 70)

            for user in users:
                created = (
                    user.created_at[:19]
                    if isinstance(user.created_at, str)
                    else str(user.created_at)[:19]
                )
                print(f"{user.username:<20} {user.email:<30} {user.role:<10} {created}")

            return 0

        elif args.generate_key:
            user = user_manager.get_user(args.generate_key)
            if not user:
                print(f"User not found: {args.generate_key}")
                return 1

            # Generate new API key
            from ..enterprise import get_api_manager

            api_manager = get_api_manager()
            new_key = api_manager.generate_api_key(
                name=f"Generated for {user.username}", user_id=user.id, permissions=user.permissions
            )

            print(f"✓ New API key generated for {user.username}")
            print(f"  API Key: {new_key}")
            return 0

        elif args.deactivate:
            success = user_manager.delete_user(args.deactivate)
            if success:
                print(f"✓ User {args.deactivate} deactivated successfully")
                return 0
            else:
                print(f"✗ Could not deactivate user {args.deactivate}")
                return 1

        else:
            print(
                "Please specify an action: --create USERNAME --email EMAIL, --list, --generate-key USER_ID, or --deactivate USER_ID"
            )
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error managing users: {e}")
        return 1


def run_enterprise_api(args) -> int:
    """Handle enterprise API server."""
    try:
        if args.start:
            from ..enterprise_api import start_api_server

            if not start_api_server:
                print("Error: FastAPI not available. Install with: pip install fastapi uvicorn")
                return 1

            print("🚀 Starting Enterprise API server...")
            print(f"   Host: {args.host}")
            print(f"   Port: {args.port}")
            print(f"   Debug: {args.debug}")
            print(f"   API Documentation: http://{args.host}:{args.port}/docs")

            # This will block until the server is stopped
            start_api_server(host=args.host, port=args.port, debug=args.debug)
            return 0

        elif args.status:
            import socket

            from ..enterprise_api import get_api_manager

            try:
                # Get the API manager to access database
                api_manager = get_api_manager()

                # Try to connect to the API server
                host = args.host if hasattr(args, "host") else "localhost"
                port = args.port if hasattr(args, "port") else 8000

                server_running = False
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((host, port))
                    server_running = result == 0
                    sock.close()
                except Exception:
                    server_running = False

                # Display status
                print("\n📊 Docx2Shelf API Server Status")
                print("=" * 40)

                if server_running:
                    print("✅ Status: Running")
                    print(f"   Host: {host}:{port}")
                    print(f"   URL: http://{host}:{port}")
                    print(f"   Docs: http://{host}:{port}/docs")
                else:
                    print("⛔ Status: Not Running")
                    print(f"   Expected at: {host}:{port}")
                    print("   Start with: docx2shelf enterprise api --start")

                # Display database info
                print("\n📁 Database Information")
                print("=" * 40)
                db_path = api_manager.db_path
                if db_path.exists():
                    db_size = db_path.stat().st_size / (1024 * 1024)  # Convert to MB
                    print("✓ Database exists")
                    print(f"  Path: {db_path}")
                    print(f"  Size: {db_size:.2f} MB")
                else:
                    print("⚠ Database not found")
                    print(f"  Path: {db_path}")

                # Display queue status
                print("\n📋 Job Queue Status")
                print("=" * 40)
                queue_status = api_manager.get_job_queue_status()
                print(f"Pending jobs: {queue_status.get('pending_jobs', 0)}")
                print(f"Running jobs: {queue_status.get('running_jobs', 0)}")
                print(f"Total queue: {queue_status.get('queue_size', 0)}")

                # Display user count
                print("\n👥 User Accounts")
                print("=" * 40)
                try:
                    users = api_manager.db_manager.list_users()
                    print(f"Total users: {len(users) if users else 0}")
                except Exception:
                    print("Could not retrieve user count")

                print("\n")
                return 0

            except ImportError:
                print("❌ Error: Enterprise API requires additional dependencies")
                print("   Install with: pip install fastapi uvicorn")
                return 1
            except Exception as e:
                print(f"❌ Error checking API status: {e}")
                return 1

        else:
            print("Please specify an action: --start or --status")
            return 1

    except ImportError:
        print("Error: Enterprise API requires additional dependencies")
        print("Install with: pip install fastapi uvicorn")
        return 1
    except Exception as e:
        print(f"Error managing API server: {e}")
        return 1


def run_enterprise_webhooks(args) -> int:
    """Handle enterprise webhook management."""
    try:
        from ..enterprise_api import get_api_manager

        api_manager = get_api_manager()
        webhook_manager = api_manager.webhook_manager

        if args.add:
            from ..enterprise_api import WebhookEndpoint

            endpoint = WebhookEndpoint(
                url=args.add, secret=args.secret, events=args.events or [], headers={}, enabled=True
            )

            webhook_manager.add_endpoint(endpoint)
            print(f"✓ Webhook added: {args.add}")
            if args.events:
                print(f"  Events: {', '.join(args.events)}")
            return 0

        elif args.list:
            if not webhook_manager.endpoints:
                print("No webhooks configured")
                return 0

            print("Configured Webhooks:")
            print("-" * 50)
            for i, endpoint in enumerate(webhook_manager.endpoints, 1):
                print(f"{i}. {endpoint.url}")
                print(f"   Events: {', '.join(endpoint.events) if endpoint.events else 'All'}")
                print(f"   Enabled: {endpoint.enabled}")
                print()

            return 0

        elif args.test:
            # Send a test webhook
            test_data = {
                "test": True,
                "message": "This is a test webhook from docx2shelf enterprise",
            }

            webhook_manager.send_webhook("test", test_data)
            print("✓ Test webhook sent to all configured endpoints")
            return 0

        else:
            print("Please specify an action: --add URL, --list, or --test")
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error managing webhooks: {e}")
        return 1


def run_enterprise_reports(args) -> int:
    """Handle enterprise reporting."""
    try:
        import csv
        import json
        from datetime import datetime, timedelta

        from ..enterprise import get_batch_processor
        from ..enterprise_api import get_api_manager

        processor = get_batch_processor()
        api_manager = get_api_manager()

        if args.stats:
            # Get job statistics
            jobs = processor.list_jobs()

            total_jobs = len(jobs)
            completed_jobs = len([j for j in jobs if j.status == "completed"])
            failed_jobs = len([j for j in jobs if j.status == "failed"])
            running_jobs = len([j for j in jobs if j.status == "running"])
            pending_jobs = len([j for j in jobs if j.status == "pending"])

            success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

            print("Enterprise Processing Statistics:")
            print("=" * 40)
            print(f"Total Jobs: {total_jobs}")
            print(f"Completed: {completed_jobs}")
            print(f"Failed: {failed_jobs}")
            print(f"Running: {running_jobs}")
            print(f"Pending: {pending_jobs}")
            print(f"Success Rate: {success_rate:.1f}%")

            # Calculate processing time stats
            processing_times = []
            for job in jobs:
                if job.started_at and job.completed_at and job.status == "completed":
                    try:
                        started = datetime.fromisoformat(job.started_at.replace("Z", "+00:00"))
                        completed = datetime.fromisoformat(job.completed_at.replace("Z", "+00:00"))
                        duration = (completed - started).total_seconds()
                        processing_times.append(duration)
                    except (ValueError, AttributeError):
                        # Skip jobs with invalid timestamp formats
                        pass

            if processing_times:
                avg_time = sum(processing_times) / len(processing_times)
                print(f"Average Processing Time: {avg_time:.1f} seconds")

            return 0

        elif args.usage:
            # Display usage analytics by user and API key
            print("\n📊 Usage Analytics")
            print("=" * 50)

            try:
                users = api_manager.db_manager.list_users()
                if not users:
                    print("No users found in the system.")
                    return 0

                total_conversions = 0
                total_api_calls = 0

                print(f"\n👥 User Statistics (Total Users: {len(users)})")
                print("-" * 50)

                for user in users:
                    user_id = user.get("id") if isinstance(user, dict) else user.user_id
                    username = (
                        user.get("username", "Unknown") if isinstance(user, dict) else user.username
                    )

                    # Get user's jobs
                    user_jobs = api_manager.db_manager.list_conversion_jobs(user_id=user_id)
                    completed = (
                        len([j for j in user_jobs if j.status == "completed"]) if user_jobs else 0
                    )
                    failed = len([j for j in user_jobs if j.status == "failed"]) if user_jobs else 0
                    total_jobs = len(user_jobs) if user_jobs else 0

                    # Get API keys for this user
                    api_keys = (
                        api_manager.db_manager.list_api_keys(user_id=user_id)
                        if hasattr(api_manager.db_manager, "list_api_keys")
                        else []
                    )

                    print(f"\nUser: {username}")
                    print(
                        f"  Conversions: {completed} completed, {failed} failed (Total: {total_jobs})"
                    )
                    if api_keys:
                        print(
                            f"  API Keys: {len(api_keys) if isinstance(api_keys, list) else len(api_keys)}"
                        )

                    total_conversions += completed
                    if api_keys:
                        total_api_calls += (
                            len(api_keys) if isinstance(api_keys, list) else len(api_keys)
                        )

                # Display overall statistics
                print("\n" + "=" * 50)
                print("📈 Overall Usage")
                print("-" * 50)
                print(f"Total Conversions: {total_conversions}")
                print(f"Total API Keys: {total_api_calls}")

                # Display rate limit statistics if available
                print("\n🔐 Rate Limiting Status")
                print("-" * 50)
                rate_limited_keys = 0
                for user in users:
                    user_id = user.get("id") if isinstance(user, dict) else user.user_id
                    if hasattr(api_manager.db_manager, "list_api_keys"):
                        api_keys = api_manager.db_manager.list_api_keys(user_id=user_id)
                        for key in (api_keys if isinstance(api_keys, list) else []):
                            if hasattr(key, "rate_limit_per_minute"):
                                rate_limited_keys += 1

                print(f"API Keys with Rate Limiting: {rate_limited_keys}")
                print(f"Total API Keys Tracked: {total_api_calls}")

                return 0

            except Exception as e:
                print(f"Error generating usage analytics: {e}")
                return 1

        elif args.export:
            jobs = processor.list_jobs()

            if args.export.endswith(".json"):
                # Export as JSON
                export_data = []
                for job in jobs:
                    export_data.append(
                        {
                            "id": job.id,
                            "name": job.name,
                            "status": job.status,
                            "processing_mode": job.processing_mode,
                            "total_items": job.total_items,
                            "processed_items": job.processed_items,
                            "failed_items": job.failed_items,
                            "created_at": job.created_at,
                            "started_at": job.started_at,
                            "completed_at": job.completed_at,
                        }
                    )

                with open(args.export, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2)

            elif args.export.endswith(".csv"):
                # Export as CSV
                with open(args.export, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "ID",
                            "Name",
                            "Status",
                            "Mode",
                            "Total Items",
                            "Processed",
                            "Failed",
                            "Created",
                            "Started",
                            "Completed",
                        ]
                    )

                    for job in jobs:
                        writer.writerow(
                            [
                                job.id,
                                job.name,
                                job.status,
                                job.processing_mode,
                                job.total_items,
                                job.processed_items,
                                job.failed_items,
                                job.created_at,
                                job.started_at or "",
                                job.completed_at or "",
                            ]
                        )
            else:
                print("Error: Export format must be .json or .csv")
                return 1

            print(f"✓ Report exported to: {args.export}")
            return 0

        else:
            print("Please specify an action: --stats, --usage, or --export FILE")
            return 1

    except ImportError:
        print("Error: Enterprise features require additional dependencies")
        return 1
    except Exception as e:
        print(f"Error generating reports: {e}")
        return 1
