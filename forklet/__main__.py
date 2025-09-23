import sys
from typing import Optional, List
import logging

import click

from forklet.interfaces.cli import ForkletCLI
from forklet.models import DownloadStrategy


# Create Click command group
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--token', '-t', help='GitHub authentication token')
@click.pass_context
def cli(ctx, verbose: bool, token: Optional[str]):
    """Forklet - Download files and folders from GitHub repositories."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['token'] = token
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        click.echo("🔍 Verbose mode enabled")


@cli.command()
@click.argument('repository')
@click.argument('destination', type=click.Path(file_okay=False, writable=True))
@click.option('--ref', '-r', default='main', help='Branch, tag, or commit SHA')
@click.option('--include', '-i', multiple=True, help='Include patterns (glob)')
@click.option('--exclude', '-e', multiple=True, help='Exclude patterns (glob)')
@click.option('--max-size', type=int, help='Maximum file size in bytes')
@click.option('--min-size', type=int, help='Minimum file size in bytes')
@click.option('--extensions', multiple=True, help='Allowed file extensions')
@click.option('--exclude-extensions', multiple=True, help='Excluded file extensions')
@click.option('--include-hidden', is_flag=True, help='Include hidden files')
@click.option('--no-binary', is_flag=True, help='Exclude binary files')
@click.option('--target-paths', multiple=True, help='Specific paths to download')
@click.option('--strategy', '-s', default='individual',
              type=click.Choice(['archive', 'individual', 'git_clone', 'sparse']),
              help='Download strategy')
@click.option('--concurrent', '-c', default=5, help='Concurrent downloads')
@click.option('--overwrite', '-f', is_flag=True, help='Overwrite existing files')
@click.pass_context
def download(
    ctx, 
    repository: str, 
    destination: str, 
    ref: str, 
    include: List[str],
    exclude: List[str], 
    max_size: Optional[int], 
    min_size: Optional[int],
    extensions: List[str], 
    exclude_extensions: List[str], 
    include_hidden: bool,
    no_binary: bool, 
    target_paths: List[str], 
    strategy: str,
    concurrent: int, 
    overwrite: bool
):
    """
    Download files from a GitHub repository.
    
    REPOSITORY: Format owner/repo (e.g., octocat/hello-world)
    DESTINATION: Local directory to save files
    """

    app = ForkletCLI()
    
    # Create filter criteria
    filters = app.create_filter_criteria(
        include = list(include),
        exclude = list(exclude),
        max_size = max_size,
        min_size = min_size,
        extensions = list(extensions),
        exclude_extensions = list(exclude_extensions),
        include_hidden = include_hidden,
        include_binary = not no_binary,
        target_paths = list(target_paths)
    )
    
    # Get authentication token from context or environment
    token = ctx.obj.get('token')
    
    # Execute download
    app.execute_download(
        repository = repository,
        destination = destination,
        ref = ref,
        filters = filters,
        strategy = DownloadStrategy(strategy),
        token = token,
        concurrent = concurrent,
        overwrite = overwrite
    )


@cli.command()
@click.argument('repository')
@click.option('--ref', '-r', default='main', help='Branch, tag, or commit SHA')
@click.pass_context
def info(ctx, repository: str, ref: str):
    """Show information about a repository."""

    try:
        app = ForkletCLI()
        app.initialize_services(ctx.obj.get('token'))
        
        owner, repo_name = app.parse_repository_string(repository)
        
        # Get repository info
        repo_info = app.github_service.get_repository_info(owner, repo_name)
        git_ref = app.github_service.resolve_reference(owner, repo_name, ref)
        
        # Display information
        click.echo(f"📊 Repository: {repo_info.full_name}")
        click.echo(f"📝 Description: {repo_info.description or 'No description'}")
        click.echo(f"🌐 URL: {repo_info.url}")
        click.echo(f"🔀 Default branch: {repo_info.default_branch}")
        click.echo(f"🏷️  Type: {repo_info.repo_type.value}")
        click.echo(f"📦 Size: {repo_info.size} KB")
        click.echo(f"📅 Created: {repo_info.created_at}")
        click.echo(f"🔄 Updated: {repo_info.updated_at}")
        click.echo(f"💻 Language: {repo_info.language or 'Unknown'}")
        click.echo(f"🔖 Topics: {', '.join(repo_info.topics) or 'None'}")
        click.echo(f"🎯 Current ref: {git_ref}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

####    MAIN ENTRYpoint fOR the FORKLET CLI
def main():
    cli()
