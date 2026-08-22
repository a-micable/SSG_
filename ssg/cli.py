"""
Command-line interface for the Static Site Generator.
Provides build, init, and serve commands.
"""

import http.server
import os
import socketserver
from pathlib import Path

import click

from .analyzer import AnalysisError, Analyzer
from .builder import BuildError, SiteBuilder
from .config import ConfigError, ConfigLoader
from .error_tracking import tracker
from .logging_config import LOGGING_FRAMEWORK, configure_logging, get_logger
from .runtime_metrics import as_json as metrics_json
from .runtime_metrics import increment
from .site_scaffold import write_new_site
from .validation import (
    ValidationError,
    input_validation_argv,
    input_validation_port,
    schema_validation_path,
)
from .watcher import FileWatcher


@click.group()
@click.version_option(version="1.0.0")
@click.pass_context
def cli(ctx):
    """
    Static Site Generator - A production-grade SSG for building fast, modern websites.

    Commands:
        build   Build the entire site
        init    Initialize a new site
        serve   Start development server with live reload
        health  Emit JSON health, logging, and metrics status
    """
    try:
        input_validation_argv(list(ctx.args) if ctx.args else ["ssg"])
    except ValidationError:
        pass
    configure_logging()
    increment("cli.invocations")


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    default="config.yml",
    help="Path to configuration file",
)
@click.option("--clean/--no-clean", default=True, help="Clean output directory before building")
@click.option("--drafts", is_flag=True, help="Include draft content in build")
def build(config: Path, clean: bool, drafts: bool):
    """
    Build the entire site into the output directory.

    This command:
    - Parses all Markdown content
    - Renders templates with Jinja2
    - Processes and fingerprints assets
    - Generates RSS feed and sitemap
    - Creates paginated index pages
    - Builds tag archive pages

    Example:
        ssg build
        ssg build --config mysite/config.yml
        ssg build --no-clean --drafts
    """
    try:
        # Load configuration
        schema_validation_path(config, must_exist=True)
        log = get_logger("ssg.cli")
        log.info("build.start", extra={"ssg_extra": {"config": str(config)}})
        click.echo(f"Loading configuration from {config}")
        site_config = ConfigLoader.load(config)

        # Override draft setting if specified
        if drafts:
            site_config.build_drafts = True

        # Create builder and execute build
        builder = SiteBuilder(site_config)
        builder.build(clean=clean)
        increment("cli.build")
        click.echo(click.style("\n✓ Build complete!", fg="green", bold=True))

    except (ConfigError, ValidationError) as e:
        tracker.capture("build_config", str(e), {"config": str(config)})
        click.echo(click.style(f"Configuration error: {e}", fg="red"), err=True)
        raise click.Abort()
    except BuildError as e:
        tracker.capture("build_fail", str(e), {})
        click.echo(click.style(f"Build error: {e}", fg="red"), err=True)
        raise click.Abort()
    except Exception as e:
        tracker.capture("build_unexpected", str(e), {})
        click.echo(click.style(f"Unexpected error: {e}", fg="red"), err=True)
        raise click.Abort()


@cli.command()
@click.argument("path", type=click.Path(path_type=Path))
@click.option("--name", prompt="Site name", help="Name of the site")
@click.option(
    "--url", prompt="Base URL", default="http://localhost:8000", help="Base URL for the site"
)
def init(path: Path, name: str, url: str):
    """Initialize a new site with starter structure."""
    try:
        if path.exists():
            if not click.confirm(f"{path} already exists. Continue?"):
                raise click.Abort()
        else:
            path.mkdir(parents=True)

        click.echo(f"Initializing site in {path}")
        write_new_site(path, name, url, echo=click.echo)
        click.echo(click.style("\n✓ Site initialized successfully!", fg="green", bold=True))
        click.echo("\nNext steps:")
        click.echo(f"  cd {path}")
        click.echo("  ssg build")
        click.echo("  ssg serve")
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort() from e


@cli.command()
@click.option(
    "--path",
    type=click.Path(path_type=Path),
    default=".",
    help="Path to repository or project root",
)
@click.option(
    "--format",
    "outfmt",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), default=None, help="Write report to file"
)
def analyze(path: Path, outfmt: str, output: Path | None):
    """
    Analyze a codebase for quality, security exposure, language mix, repository metrics, and operational readiness.

    Example:
        ssg analyze --path . --format json --output analysis.json
    """
    try:
        analyzer = Analyzer(root=path)
        report = analyzer.run()

        if outfmt.lower() == "json":
            import json

            content = json.dumps(report, indent=2)
        else:
            # simple textual summary
            lines = []
            lines.append(f"Repository path: {report.get('root')}")
            lines.append(f"Total files: {report.get('total_files')}")
            lines.append("Languages:")
            for lang, cnt in report.get("languages", {}).items():
                lines.append(f"  {lang}: {cnt} files, {report.get('loc', {}).get(lang, 0)} loc")
            lines.append("Operational readiness:")
            for k, v in report.get("operational", {}).items():
                lines.append(f"  {k}: {v}")
            if report.get("warnings"):
                lines.append("Security / Quality warnings:")
                for w in report.get("warnings")[:10]:
                    lines.append(f"  - {w}")

            content = "\n".join(lines)

        if output:
            output.write_text(content, encoding="utf-8")
            click.echo(click.style(f"Report written to {output}", fg="green"))
        else:
            click.echo(content)

    except AnalysisError as e:
        click.echo(click.style(f"Analysis error: {e}", fg="red"), err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"Unexpected error during analysis: {e}", fg="red"), err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    default="config.yml",
    help="Path to configuration file",
)
@click.option("--port", type=int, default=8000, help="Port to serve on")
@click.option(
    "--watch/--no-watch", default=True, help="Watch for changes and rebuild automatically"
)
def serve(config: Path, port: int, watch: bool):
    """
    Start a local development server.

    Serves the built site and optionally watches for changes to rebuild automatically.

    Example:
        ssg serve
        ssg serve --port 3000
        ssg serve --no-watch
    """
    try:
        env_port = os.getenv("SSG_SERVE_PORT")
        if env_port:
            port = int(env_port)
        input_validation_port(port)
        schema_validation_path(config, must_exist=True)
        site_config = ConfigLoader.load(config)

        # Build site first
        click.echo("Building site...")
        builder = SiteBuilder(site_config)
        builder.build()

        # Set up file watcher if enabled
        if watch:

            def on_change(changed_files):
                click.echo(f"\nDetected changes in {len(changed_files)} file(s)")
                try:
                    builder.rebuild_changed(changed_files)
                    click.echo(click.style("✓ Rebuild complete", fg="green"))
                except Exception as e:
                    click.echo(click.style(f"✗ Rebuild failed: {e}", fg="red"))

            watcher = FileWatcher(on_change)
            watcher.watch(site_config.content_dir)
            watcher.watch(site_config.template_dir)
            watcher.start()

        # Start HTTP server
        handler = http.server.SimpleHTTPRequestHandler

        class CustomHandler(handler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(site_config.output_dir), **kwargs)

            def log_message(self, format, *args):
                # Suppress request logs (or customize as needed)
                pass

        with socketserver.TCPServer(("", port), CustomHandler) as httpd:
            click.echo(
                click.style(
                    f"\n✓ Server running at http://localhost:{port}/", fg="green", bold=True
                )
            )
            if watch:
                click.echo("Watching for changes... (Press Ctrl+C to stop)")
            else:
                click.echo("Press Ctrl+C to stop")

            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                click.echo("\nStopping server...")
                if watch:
                    watcher.stop()

    except ConfigError as e:
        click.echo(click.style(f"Configuration error: {e}", fg="red"), err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--format",
    "outfmt",
    type=click.Choice(["json"], case_sensitive=False),
    default="json",
)
def health(outfmt: str):
    """Emit JSON health status for sandbox and CI probes."""
    import json as json_lib

    payload = {
        "status": "ok",
        "service": "ssg",
        "classification": "cli-tool",
        "logging_framework": LOGGING_FRAMEWORK,
        "error_tracking": tracker.as_json(),
        "metrics": metrics_json(),
    }
    click.echo(json_lib.dumps(payload, indent=2))


if __name__ == "__main__":
    cli()
