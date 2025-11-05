"""
Generate a CSV of image files from a local folder (recursive).
Output CSV columns: nama_proyek, periode, nama_di, nama_gambar, url

Usage:
  python link-list.py [path/to/folder]
  If no path provided, scans all Oplah folders in current directory
"""

import csv
import os
import subprocess
import sys
from typing import List, Tuple


ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg"}


def is_image(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_EXT


def get_git_info() -> Tuple[str, str, str]:
    """Get GitHub repository info from local git repo."""
    try:
        # Get remote URL
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True
        ).strip()
        
        # Extract owner/repo from remote URL
        # Handle both HTTPS and SSH formats:
        # https://github.com/owner/repo.git
        # git@github.com:owner/repo.git
        if "github.com" not in remote:
            raise ValueError("Not a GitHub repository")
            
        if remote.startswith("https"):
            # https URL format
            _, _, _, owner, repo = remote.rstrip(".git").split("/")
        else:
            # SSH format
            _, owner_repo = remote.split(":")
            owner, repo = owner_repo.rstrip(".git").split("/")
            
        # Get current branch
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True
        ).strip()
        
        return owner, repo, branch
    except subprocess.CalledProcessError:
        raise ValueError("Not in a git repository or git not installed")


def encode_path(path: str) -> str:
    """Encode spaces in path with %20."""
    parts = path.split('/')
    encoded_parts = [part.replace(' ', '%20') for part in parts]
    return '/'.join(encoded_parts)


def make_github_url(owner: str, repo: str, branch: str, path: str) -> str:
    """Generate github.com blob URL for a file with properly encoded spaces."""
    encoded_path = encode_path(path)
    return f"https://github.com/{owner}/{repo}/blob/{branch}/{encoded_path}"


def row_from_path(path: str) -> List[str]:
    """Extract project name, period (M3, etc), DI name, and filename from path."""
    parts = path.split('/')
    if not parts:
        return ["", "", "", ""]

    # Get the project name (first folder)
    project_name = parts[0] if len(parts) > 0 else ""
    
    # Get the period (M3, M4, etc) - should be second part
    period = parts[1] if len(parts) > 1 else ""
    
    # Get DI name - should be in the folder name after M3/M4/etc
    # Often in format like "1. M3 D.I Citasuk Banten Paket I"
    di_name = ""
    if len(parts) > 2:
        folder_name = parts[2]
        # Extract D.I name if present
        if "D.I" in folder_name:
            di_start = folder_name.find("D.I")
            di_name = folder_name[di_start:].split("/")[0].strip()
    
    # Full relative path as image name
    image_path = "./"+path
    
    return [project_name, period, di_name, image_path]


def list_images(root_path: str) -> List[str]:
    """Return all image file paths under root_path recursively."""
    image_paths = []
    for dirpath, _, files in os.walk(root_path):
        for f in files:
            if is_image(f):
                # Get path relative to root_path
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, root_path)
                # Convert Windows path separators to forward slashes for URLs
                rel = rel.replace(os.sep, "/")
                image_paths.append(rel)
    return sorted(image_paths)


def scan_current_directory() -> list[str]:
    """Scan current directory for folders and return them."""
    folders = []
    for item in os.listdir():
        if os.path.isdir(item) and item.startswith("Oplah"):
            folders.append(item)
    return sorted(folders)


def main(argv: list[str] | None = None) -> int:
    if not argv:
        argv = sys.argv[1:]
    
    # If no argument provided, scan current directory
    if not argv:
        folders = scan_current_directory()
        if not folders:
            print("Error: No Oplah folders found in current directory")
            return 1
        
        print(f"Found {len(folders)} folders to scan:")
        for f in folders:
            print(f"- {f}")
            
        all_files = []
        for folder in folders:
            if not os.path.isdir(folder):
                print(f"Warning: Folder not found: {folder}")
                continue
            files = list_images(folder)
            # Prepend folder name to each file
            files = [f"{folder}/{f}" for f in files]
            all_files.extend(files)
            
        folder_path = "."  # Current directory
        files = all_files
    else:
        folder_path = argv[0]
        if not os.path.isdir(folder_path):
            print(f"Error: Folder not found: {folder_path}", file=sys.stderr)
            return 2
        files = [f"{folder_path}/{f}" for f in list_images(folder_path)]
    
    out_file = "images.csv"
    
    try:
        # Get GitHub repo info first
        try:
            owner, repo, branch = get_git_info()
            print(f"Found GitHub repo: {owner}/{repo} @ {branch}")
        except ValueError as e:
            print(f"Warning: {e}")
            print("URLs will not be generated")
            owner = repo = branch = None
            
        if not files:
            print("No image files found.")
            return 0

        with open(out_file, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["nama_proyek", "periode", "nama_di", "nama_gambar", "url"])
            for pth in files:
                project_name, period, di_name, image_path = row_from_path(pth)
                # Create URL with encoded path
                if owner and repo and branch:
                    url = make_github_url(owner, repo, branch, pth)
                else:
                    url = ""
                writer.writerow([project_name, period, di_name, image_path, url])

        print(f"Wrote {len(files)} rows to {out_file}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())