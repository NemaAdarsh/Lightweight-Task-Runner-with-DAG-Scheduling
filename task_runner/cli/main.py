import click
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

from ..core import TaskRunner, DAG
from ..utils import (
    ConfigLoader, 
    ConfigValidator,
    setup_logging,
    setup_dag_logging,
    visualize_dag_ascii,
    visualize_dag_tree,
    print_dag_summary,
    print_execution_plan,
    create_progress_bar
)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--log-file', type=click.Path(), help='Log file path')
@click.pass_context
def cli(ctx, verbose, log_file):
    """Lightweight Task Runner with DAG Scheduling"""
    ctx.ensure_object(dict)
    
    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    ctx.obj['logger'] = setup_logging(
        level=log_level,
        log_file=log_file,
        console_output=True
    )


@cli.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True), 
              help='Path to DAG configuration file')
@click.option('--visualize', is_flag=True, help='Show DAG visualization before execution')
@click.option('--max-workers', type=int, help='Override max workers setting')
@click.option('--execution-mode', type=click.Choice(['threading', 'multiprocessing']),
              help='Override execution mode')
@click.option('--log-dir', type=click.Path(), default='logs', 
              help='Directory for execution logs')
@click.pass_context
def run(ctx, config, visualize, max_workers, execution_mode, log_dir):
    """Run a DAG from configuration file"""
    logger = ctx.obj['logger']
    
    try:
        # Load DAG configuration
        click.echo(f"Loading DAG configuration from: {config}")
        dag = ConfigLoader.load_from_json(config)
        
        # Override settings if provided
        if max_workers:
            dag.max_workers = max_workers
        if execution_mode:
            dag.execution_mode = execution_mode
        
        # Set up DAG-specific logging
        setup_dag_logging(dag.dag_id, log_dir)
        
        # Show visualization if requested
        if visualize:
            click.echo("\nDAG Visualization:")
            click.echo(visualize_dag_ascii(dag, show_states=False))
            click.echo("\nExecution Plan:")
            click.echo(print_execution_plan(dag))
            
            if not click.confirm("Proceed with execution?"):
                click.echo("Execution cancelled.")
                return
        
        # Create task runner
        runner = TaskRunner(
            max_workers=dag.max_workers,
            execution_mode=dag.execution_mode
        )
        
        # Execute DAG
        click.echo(f"\nStarting execution of DAG: {dag.dag_id}")
        start_time = datetime.now()
        
        # Run in blocking mode for simpler result handling
        result = runner.run_dag(dag, blocking=True)
        
        # Use the returned result directly
        final_result = result
        
        # Display results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        click.echo(f"\nExecution completed in {duration:.2f} seconds")
        click.echo(f"Final state: {final_result.state.value}")
        click.echo(f"Success rate: {final_result.success_rate:.2%}")
        
        # Show failed tasks if any
        failed_tasks = final_result.get_failed_tasks()
        if failed_tasks:
            click.echo(f"\nFailed tasks ({len(failed_tasks)}):")
            for task_id, task_result in failed_tasks.items():
                click.echo(f"  - {task_id}: {task_result.error}")
        
        # Exit with error code if DAG failed
        if final_result.state.value in ['failed', 'partial_success']:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error running DAG: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--dag-id', required=True, help='DAG ID to check status for')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), 
              default='text', help='Output format')
@click.pass_context
def status(ctx, dag_id, output_format):
    """Check status of a running or completed DAG"""
    try:
        # This is a simplified status check
        # In a full implementation, you'd have a persistent store for DAG states
        click.echo(f"Status checking for DAG: {dag_id}")
        click.echo("Note: Status tracking requires a persistent storage backend")
        
        if output_format == 'json':
            status_data = {
                'dag_id': dag_id,
                'status': 'unknown',
                'message': 'Status tracking not implemented'
            }
            click.echo(json.dumps(status_data, indent=2))
        else:
            click.echo(f"DAG ID: {dag_id}")
            click.echo("Status: Unknown (requires persistent storage)")
            
    except Exception as e:
        ctx.obj['logger'].error(f"Error checking status: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), 
              default='text', help='Output format')
@click.pass_context
def list(ctx, output_format):
    """List all available DAGs"""
    try:
        # This would typically scan a DAG directory or database
        click.echo("Listing DAGs requires a DAG registry or directory structure")
        
        if output_format == 'json':
            dag_list = {
                'dags': [],
                'message': 'DAG listing not implemented'
            }
            click.echo(json.dumps(dag_list, indent=2))
        else:
            click.echo("No DAGs found (requires DAG registry)")
            
    except Exception as e:
        ctx.obj['logger'].error(f"Error listing DAGs: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True),
              help='Path to DAG configuration file')
@click.option('--fix', is_flag=True, help='Attempt to fix common validation issues')
@click.pass_context
def validate(ctx, config, fix):
    """Validate a DAG configuration file"""
    logger = ctx.obj['logger']
    
    try:
        click.echo(f"Validating configuration: {config}")
        
        # Validate the configuration
        errors = ConfigValidator.validate_json_file(config)
        
        if not errors:
            click.echo("✅ Configuration is valid!")
            
            # Load and show summary
            dag = ConfigLoader.load_from_json(config)
            click.echo("\nDAG Summary:")
            click.echo(print_dag_summary(dag))
            
            return
        
        # Show validation errors
        click.echo(f"❌ Found {len(errors)} validation error(s):")
        for i, error in enumerate(errors, 1):
            click.echo(f"  {i}. {error}")
        
        if fix:
            click.echo("\nAttempting to fix common issues...")
            # Here you could implement common fixes
            click.echo("Automatic fixing not implemented yet")
        
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--dag-id', help='DAG ID to show logs for')
@click.option('--task-id', help='Task ID to show logs for')
@click.option('--log-dir', type=click.Path(exists=True), default='logs',
              help='Directory containing log files')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.pass_context
def logs(ctx, dag_id, task_id, log_dir, follow):
    """View execution logs"""
    try:
        if not os.path.exists(log_dir):
            click.echo(f"Log directory not found: {log_dir}")
            return
        
        # Find relevant log files
        log_files = []
        for file in os.listdir(log_dir):
            if file.endswith('.log'):
                if dag_id and dag_id in file:
                    log_files.append(os.path.join(log_dir, file))
                elif not dag_id:
                    log_files.append(os.path.join(log_dir, file))
        
        if not log_files:
            click.echo("No log files found")
            return
        
        # Show most recent log file
        latest_log = max(log_files, key=os.path.getmtime)
        click.echo(f"Showing logs from: {latest_log}")
        
        if follow:
            # Simple tail -f implementation
            _tail_file(latest_log)
        else:
            with open(latest_log, 'r') as f:
                content = f.read()
                if task_id:
                    # Filter for specific task
                    lines = [line for line in content.split('\n') if task_id in line]
                    click.echo('\n'.join(lines))
                else:
                    click.echo(content)
                    
    except Exception as e:
        ctx.obj['logger'].error(f"Error viewing logs: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', required=True, type=click.Path(exists=True),
              help='Path to DAG configuration file')
@click.option('--style', type=click.Choice(['ascii', 'tree']), default='ascii',
              help='Visualization style')
@click.option('--show-states', is_flag=True, help='Show task states')
@click.pass_context
def visualize(ctx, config, style, show_states):
    """Visualize a DAG structure"""
    try:
        # Load DAG
        dag = ConfigLoader.load_from_json(config)
        
        # Show summary
        click.echo(print_dag_summary(dag))
        click.echo()
        
        # Show visualization
        if style == 'tree':
            click.echo(visualize_dag_tree(dag, show_states))
        else:
            click.echo(visualize_dag_ascii(dag, show_states))
        
        click.echo()
        click.echo(print_execution_plan(dag))
        
    except Exception as e:
        ctx.obj['logger'].error(f"Error visualizing DAG: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _monitor_dag_execution(runner: TaskRunner, dag_id: str):
    """Monitor DAG execution progress"""
    last_progress = {}
    
    while True:
        result = runner.get_dag_status(dag_id)
        if not result:
            break
        
        # Check if execution is complete
        if result.state.value in ['success', 'failed', 'partial_success']:
            break
        
        # Show progress
        total_tasks = len(result.task_results) if result.task_results else 0
        completed_tasks = sum(
            1 for r in result.task_results.values() 
            if r.state.value in ['success', 'failed', 'skipped']
        )
        
        current_progress = {
            'total': total_tasks,
            'completed': completed_tasks
        }
        
        # Only update if progress changed
        if current_progress != last_progress:
            if total_tasks > 0:
                progress_bar = create_progress_bar(completed_tasks, total_tasks)
                click.echo(f"\rProgress: {progress_bar}", nl=False)
            last_progress = current_progress
        
        time.sleep(1)  # Check every second
    
    click.echo()  # New line after progress


def _tail_file(filepath: str):
    """Simple tail -f implementation"""
    try:
        with open(filepath, 'r') as f:
            # Go to end of file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    click.echo(line.rstrip())
                else:
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        click.echo("\nStopped following logs")


if __name__ == '__main__':
    cli()
