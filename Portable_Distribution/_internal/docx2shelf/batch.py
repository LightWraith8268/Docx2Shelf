from __future__ import annotations

import argparse
import concurrent.futures
from pathlib import Path
from typing import Any, Dict, List, Optional


def find_docx_files(directory: Path, pattern: str = "*.docx") -> List[Path]:
    """Find DOCX files in directory matching pattern."""
    if not directory.exists() or not directory.is_dir():
        return []

    return sorted(directory.glob(pattern))


def create_batch_args(base_args: argparse.Namespace, input_file: Path, output_file: Optional[Path] = None) -> argparse.Namespace:
    """Create argument namespace for batch processing a single file."""
    # Create a copy of base args
    batch_args = argparse.Namespace(**vars(base_args))

    # Override input and output for this specific file
    batch_args.input = str(input_file)

    if output_file:
        batch_args.output = str(output_file)
    else:
        # Generate output filename based on input
        output_name = input_file.stem + ".epub"
        output_dir = getattr(base_args, 'output_dir', input_file.parent)
        batch_args.output = str(Path(output_dir) / output_name)

    return batch_args


def process_single_file(args_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single DOCX file. Used by parallel processing."""
    from .cli import run_build

    # Reconstruct args namespace
    args = argparse.Namespace(**args_dict)

    input_file = Path(args.input)
    output_file = Path(args.output)

    result = {
        'input': str(input_file),
        'output': str(output_file),
        'success': False,
        'error': None
    }

    try:
        # Force quiet mode for batch processing
        args.quiet = True
        args.no_prompt = True

        # Run the build
        exit_code = run_build(args)
        result['success'] = (exit_code == 0)

        if exit_code != 0:
            result['error'] = f"Build failed with exit code {exit_code}"

    except Exception as e:
        result['error'] = str(e)

    return result


def run_batch_mode(
    directory: Path,
    pattern: str = "*.docx",
    output_dir: Optional[Path] = None,
    parallel: bool = True,
    max_workers: Optional[int] = None,
    base_args: Optional[argparse.Namespace] = None,
    quiet: bool = False
) -> Dict[str, Any]:
    """Run batch processing on multiple DOCX files.

    Returns summary of batch processing results.
    """
    # Find all matching files
    docx_files = find_docx_files(directory, pattern)

    if not docx_files:
        return {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'results': [],
            'error': f"No files matching '{pattern}' found in {directory}"
        }

    if not quiet:
        print(f"📁 Found {len(docx_files)} files matching '{pattern}'")

    # Set up output directory
    if output_dir is None:
        output_dir = directory / "batch_output"

    output_dir.mkdir(parents=True, exist_ok=True)

    if not quiet:
        print(f"📤 Output directory: {output_dir}")

    # Prepare arguments for each file
    file_args = []
    for docx_file in docx_files:
        output_file = output_dir / f"{docx_file.stem}.epub"
        batch_args = create_batch_args(base_args or argparse.Namespace(), docx_file, output_file)
        file_args.append(vars(batch_args))

    results = []
    successful = 0
    failed = 0

    if parallel and len(docx_files) > 1:
        # Parallel processing
        if not quiet:
            print(f"🔄 Processing {len(docx_files)} files in parallel...")

        max_workers = max_workers or min(len(docx_files), 4)

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(process_single_file, args): args['input']
                for args in file_args
            }

            for future in concurrent.futures.as_completed(future_to_file):
                result = future.result()
                results.append(result)

                if result['success']:
                    successful += 1
                    if not quiet:
                        print(f"✅ {Path(result['input']).name} -> {Path(result['output']).name}")
                else:
                    failed += 1
                    if not quiet:
                        print(f"❌ {Path(result['input']).name}: {result['error']}")

    else:
        # Sequential processing
        if not quiet:
            print(f"🔄 Processing {len(docx_files)} files sequentially...")

        for i, args_dict in enumerate(file_args, 1):
            if not quiet:
                print(f"📖 Processing {i}/{len(docx_files)}: {Path(args_dict['input']).name}")

            result = process_single_file(args_dict)
            results.append(result)

            if result['success']:
                successful += 1
                if not quiet:
                    print(f"✅ Completed: {Path(result['output']).name}")
            else:
                failed += 1
                if not quiet:
                    print(f"❌ Failed: {result['error']}")

    # Generate summary
    summary = {
        'total_files': len(docx_files),
        'successful': successful,
        'failed': failed,
        'results': results,
        'output_dir': str(output_dir)
    }

    if not quiet:
        print("\n📊 Batch processing complete:")
        print(f"   Total files: {summary['total_files']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")
        if failed > 0:
            print(f"   Success rate: {(successful / len(docx_files)) * 100:.1f}%")

    return summary


def create_batch_report(summary: Dict[str, Any], output_path: Path) -> None:
    """Create a detailed batch processing report."""
    import json
    from datetime import datetime

    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': summary,
        'details': []
    }

    for result in summary['results']:
        detail = {
            'input_file': result['input'],
            'output_file': result['output'],
            'success': result['success'],
            'error': result.get('error')
        }
        report['details'].append(detail)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def validate_batch_args(args: argparse.Namespace) -> List[str]:
    """Validate arguments for batch mode."""
    errors = []

    if not hasattr(args, 'batch_dir') or not args.batch_dir:
        errors.append("Batch directory is required")
        return errors

    batch_dir = Path(args.batch_dir)
    if not batch_dir.exists():
        errors.append(f"Batch directory does not exist: {batch_dir}")
    elif not batch_dir.is_dir():
        errors.append(f"Batch directory is not a directory: {batch_dir}")

    pattern = getattr(args, 'batch_pattern', '*.docx')
    if not pattern:
        errors.append("Batch pattern cannot be empty")

    return errors