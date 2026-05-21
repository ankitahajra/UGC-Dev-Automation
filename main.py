"""
Main Entry Point
Command-line interface for the Azure Function Auto-Diagnose and Auto-Fix Pipeline.
"""

import sys
import click
import logging
from pathlib import Path

from src.config_manager import get_config
from src.logger import setup_logging, get_logger
from src.pipeline_orchestrator import PipelineOrchestrator
from src.diagnostics_webhook import DiagnosticsWebhook
from src.azure_monitor import AzureMonitor
from src.ica_client import ICAClient
from src.bob_automation import BOBAutomation

# Initialize logger (will be configured by setup_logging)
logger = get_logger(__name__)


@click.group()
@click.option('--config', default='config.yaml', help='Path to configuration file')
@click.option('--log-level', default='INFO', help='Logging level')
@click.option('--log-format', default='json', help='Log format (json or text)')
@click.pass_context
def cli(ctx, config, log_level, log_format):
    """Azure Function Auto-Diagnose and Auto-Fix Pipeline."""
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Load configuration
    try:
        config_manager = get_config(config)
        ctx.obj['config'] = config_manager
        
        # Setup logging
        log_config = config_manager.get('logging', {})
        setup_logging(
            level=log_level,
            log_format=log_format,
            output=log_config.get('output', 'both'),
            log_file=log_config.get('file_path', 'logs/pipeline.log'),
            max_file_size_mb=log_config.get('max_file_size_mb', 100),
            backup_count=log_config.get('backup_count', 5)
        )
        
        logger.info("Application initialized successfully")
        
    except Exception as e:
        click.echo(f"Error initializing application: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def validate_config(ctx):
    """Validate configuration file."""
    config = ctx.obj['config']
    
    click.echo("Validating configuration...")
    
    if config.validate_config():
        click.secho("✓ Configuration is valid", fg='green')
        
        # Display key configuration values
        click.echo("\nKey Configuration:")
        click.echo(f"  Azure Function: {config.get('azure.function_name')}")
        click.echo(f"  Resource Group: {config.get('azure.resource_group')}")
        click.echo(f"  ICA Enabled: {config.get('ica.enabled')}")
        click.echo(f"  BOB Approval Required: {config.get('bob.require_approval')}")
        
        sys.exit(0)
    else:
        click.secho("✗ Configuration validation failed", fg='red')
        sys.exit(1)


@cli.command()
@click.option('--operation-id', help='Specific operation ID to process')
@click.pass_context
def run_pipeline(ctx, operation_id):
    """Execute the complete pipeline once."""
    config = ctx.obj['config']
    
    click.echo("Starting pipeline execution...")
    
    try:
        orchestrator = PipelineOrchestrator(config)
        result = orchestrator.execute_pipeline(operation_id)
        
        # Display result
        click.echo(f"\nPipeline Status: {result['status']}")
        click.echo(f"Duration: {result['duration']}")
        click.echo(f"Final Stage: {result['final_stage']}")
        
        if result['status'] == 'success':
            click.secho("\n✓ Pipeline completed successfully", fg='green')
            
            # Display stage results
            for stage_name, stage_result in result.get('stages', {}).items():
                click.echo(f"\n{stage_name.upper()}:")
                click.echo(f"  Status: {stage_result.get('status', 'unknown')}")
                
                if stage_name == 'automation':
                    automation_result = stage_result.get('automation_result', {})
                    pr_url = automation_result.get('pr_url')
                    if pr_url:
                        click.echo(f"  Pull Request: {pr_url}")
        else:
            click.secho(f"\n✗ Pipeline failed: {result.get('error', 'Unknown error')}", fg='red')
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error executing pipeline: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--interval', default=60, help='Check interval in seconds')
@click.pass_context
def monitor(ctx, interval):
    """Continuously monitor for failures and trigger pipeline."""
    config = ctx.obj['config']
    
    click.echo(f"Starting continuous monitoring (interval: {interval}s)")
    click.echo("Press Ctrl+C to stop\n")
    
    try:
        orchestrator = PipelineOrchestrator(config)
        orchestrator.monitor_continuously(check_interval_seconds=interval)
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped by user")
    except Exception as e:
        click.echo(f"Error in monitoring: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--host', default='0.0.0.0', help='Webhook host address')
@click.option('--port', default=8080, help='Webhook port')
@click.pass_context
def webhook(ctx, host, port):
    """Start the diagnostics webhook server."""
    config = ctx.obj['config']
    
    click.echo(f"Starting diagnostics webhook on {host}:{port}")
    
    try:
        azure_monitor = AzureMonitor(config)
        webhook_server = DiagnosticsWebhook(config, azure_monitor)
        webhook_server.run(host=host, port=port)
    except Exception as e:
        click.echo(f"Error starting webhook: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def check_health(ctx):
    """Check health of all components."""
    config = ctx.obj['config']
    
    click.echo("Checking component health...\n")
    
    all_healthy = True
    
    # Check Azure Monitor
    try:
        azure_monitor = AzureMonitor(config)
        health = azure_monitor.check_function_health()
        status = health.get('state', 'unknown')
        
        if status == 'Running':
            click.secho("✓ Azure Function: Healthy", fg='green')
        else:
            click.secho(f"✗ Azure Function: {status}", fg='yellow')
            all_healthy = False
    except Exception as e:
        click.secho(f"✗ Azure Monitor: Error - {str(e)}", fg='red')
        all_healthy = False
    
    # Check ICA
    try:
        ica_client = ICAClient(config)
        if ica_client.check_health():
            click.secho("✓ ICA Service: Healthy", fg='green')
        else:
            click.secho("✗ ICA Service: Unhealthy", fg='red')
            all_healthy = False
    except Exception as e:
        click.secho(f"✗ ICA Service: Error - {str(e)}", fg='red')
        all_healthy = False
    
    # Check BOB (Git connectivity)
    try:
        bob = BOBAutomation(config)
        click.secho("✓ BOB Automation: Configured", fg='green')
    except Exception as e:
        click.secho(f"✗ BOB Automation: Error - {str(e)}", fg='red')
        all_healthy = False
    
    click.echo()
    if all_healthy:
        click.secho("All components are healthy", fg='green')
        sys.exit(0)
    else:
        click.secho("Some components have issues", fg='yellow')
        sys.exit(1)


@cli.command()
@click.option('--limit', default=10, help='Number of executions to show')
@click.pass_context
def history(ctx, limit):
    """Show pipeline execution history."""
    config = ctx.obj['config']
    
    try:
        orchestrator = PipelineOrchestrator(config)
        history_list = orchestrator.get_execution_history(limit)
        
        if not history_list:
            click.echo("No execution history available")
            return
        
        click.echo(f"\nShowing last {len(history_list)} executions:\n")
        
        for i, execution in enumerate(reversed(history_list), 1):
            click.echo(f"{i}. Pipeline ID: {execution['pipeline_id']}")
            click.echo(f"   Status: {execution['status']}")
            click.echo(f"   Start Time: {execution['start_time']}")
            click.echo(f"   Duration: {execution['duration']}")
            click.echo(f"   Final Stage: {execution['final_stage']}")
            click.echo()
            
    except Exception as e:
        click.echo(f"Error retrieving history: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('operation_id')
@click.pass_context
def analyze(ctx, operation_id):
    """Analyze a specific failure by operation ID."""
    config = ctx.obj['config']
    
    click.echo(f"Analyzing operation: {operation_id}\n")
    
    try:
        # Create diagnostic package
        azure_monitor = AzureMonitor(config)
        diagnostic_package = azure_monitor.create_diagnostic_package(operation_id)
        
        click.echo("Diagnostic Package Created:")
        click.echo(f"  Function: {diagnostic_package.get('function_name')}")
        click.echo(f"  Timestamp: {diagnostic_package.get('timestamp')}")
        
        # Analyze with ICA
        ica_client = ICAClient(config)
        analysis = ica_client.process_analysis(diagnostic_package)
        
        if analysis.get('status') == 'success':
            click.secho("\n✓ Analysis completed successfully", fg='green')
            
            root_cause = analysis.get('root_cause', {})
            click.echo(f"\nRoot Cause:")
            click.echo(f"  Category: {root_cause.get('category')}")
            click.echo(f"  Summary: {root_cause.get('summary')}")
            click.echo(f"  Confidence: {root_cause.get('confidence', 0):.1%}")
            
            risk = analysis.get('risk_assessment', {})
            click.echo(f"\nRisk Assessment:")
            click.echo(f"  Overall Risk: {risk.get('overall_risk')}")
            click.echo(f"  Approval Required: {risk.get('approval_required')}")
            
            fixes = analysis.get('fixes', {})
            click.echo(f"\nRecommended Fixes:")
            if fixes.get('code_fix'):
                click.echo(f"  ✓ Code fix available")
            if fixes.get('iac_fix'):
                click.echo(f"  ✓ Infrastructure fix available")
            if fixes.get('config_fix'):
                click.echo(f"  ✓ Configuration fix available")
        else:
            click.secho(f"\n✗ Analysis failed: {analysis.get('message')}", fg='red')
            
    except Exception as e:
        click.echo(f"Error analyzing operation: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    from src import __version__
    
    click.echo(f"Azure Function Auto-Diagnose and Auto-Fix Pipeline")
    click.echo(f"Version: {__version__}")
    click.echo(f"Python: {sys.version.split()[0]}")


if __name__ == '__main__':
    cli(obj={})

# Made with Bob
