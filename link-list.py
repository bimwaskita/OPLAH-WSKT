"""
Generate a CSV of image files from a local folder (recursive).
Output CSV columns: folder, subfolder, subfolder, nama gambar, url (raw.githubusercontent.com)

Usage:
  python link-list.py path/to/folder
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
    """Generate raw.githubusercontent.com URL for a file with properly encoded spaces."""
    encoded_path = encode_path(path)
    return f"https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/{branch}/{encoded_path}"

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
def row_from_path(path: str) -> List[str]:
    """Split path into up to 3 folder levels and filename."""
    parts = path.split(os.sep)
    if not parts:
        return ["", "", "", ""]
    filename = parts[-1]
    folders = parts[:-1]
    folder0 = folders[0] if len(folders) >= 1 else ""
    folder1 = folders[1] if len(folders) >= 2 else ""
    folder2 = os.sep.join(folders[2:]) if len(folders) >= 3 else ""
    return [folder0, folder1, folder2, filename]


def main(argv: list[str] | None = None) -> int:
    if not argv:
        argv = sys.argv[1:]
    
    if not argv:
        print("Error: Please provide the folder path")
        print("Usage: python link-list.py path/to/folder")
        return 1
        
    folder_path = argv[0]
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found: {folder_path}", file=sys.stderr)
        return 2
        
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
        
        # Encode the root folder path for URL
        encoded_root = folder_path.replace(" ", "%20")
        files = list_images(folder_path)
        # Prepend the encoded root folder to all files
        files = [f"{encoded_root}/{f}" for f in files]
    except Exception as e:
        print(f"Error scanning folder: {e}", file=sys.stderr)
        return 3

    if not files:
        print("No image files found.")
        return 0

    with open(out_file, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["folder", "subfolder", "subfolder", "nama gambar", "url"])
        for pth in files:
            row = row_from_path(pth)
            if owner and repo and branch:
                url = make_github_url(owner, repo, branch, pth)
                row.append(url)
            else:
                row.append("")  # Empty URL if not in git repo
            writer.writerow(row)

    print(f"Wrote {len(files)} rows to {out_file}")
    return 0
if __name__ == "__main__":
	raise SystemExit(main())
