"""
Generate a CSV of image files from local folders with GitHub raw URLs.
Output columns: nama_proyek, periode, nama_di, nama_gambar, url
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
    encoded_path = encode_path(path)  # path already includes ./
    return f"https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/{branch}/{encoded_path}"


def clean_folder_name(name: str) -> str:
    """Clean up folder names by removing numbering prefixes."""
    # Remove numbering like "1. " or "1. M3" from DI folder names
    if '. ' in name and name[0].isdigit():
        name = name.split('. ', 1)[1]
    return name

def parse_path_info(path: str) -> Tuple[str, str, str, str]:
    """Parse path into nama_proyek, periode, nama_di, and nama_gambar."""
    parts = path.split('/')
    
    # Remove ./ prefix if present
    if parts[0] == '.':
        parts = parts[1:]
    
    # Handle files directly in project folder
    if len(parts) == 2:
        nama_proyek, nama_gambar = parts
        return nama_proyek, "", "", path
        
    # Handle files in period folders (e.g., M3, M4)
    if len(parts) == 3:
        nama_proyek, periode, nama_gambar = parts
        return nama_proyek, periode, "", path
        
    # Handle files in DI folders
    nama_proyek = parts[0]  # First part is always project name
    periode = parts[1]      # Second part is period (M3, M4, etc)
    
    # For DI name, we want the part after the period numbering
    # Example: "1. M3 D.I Citasuk Banten Paket I" -> "D.I Citasuk Banten Paket I"
    di_folder = parts[2]
    nama_di = clean_folder_name(di_folder)
    
    return nama_proyek, periode, nama_di, path


def list_images(root_path: str) -> List[str]:
    """Return all image file paths under root_path recursively."""
    image_paths = []
    for dirpath, _, files in os.walk(root_path):
        for f in files:
            if is_image(f):
                # Get path relative to root_path
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, root_path)
                # Convert Windows path separators to forward slashes
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
            # Prepend ./ and folder name to each file
            files = [f"./{folder}/{f}" for f in files]
            all_files.extend(files)
            
        files = all_files
    else:
        folder_path = argv[0]
        if not os.path.isdir(folder_path):
            print(f"Error: Folder not found: {folder_path}", file=sys.stderr)
            return 2
        files = [f"./{folder_path}/{f}" for f in list_images(folder_path)]
    
    # Get GitHub info for URLs
    try:
        owner, repo, branch = get_git_info()
        print(f"Found GitHub repo: {owner}/{repo} @ {branch}")
    except ValueError as e:
        print(f"Warning: {e}")
        print("URLs will not be generated")
        owner = repo = branch = None

    out_file = "images.csv"
    
    if not files:
        print("No image files found.")
        return 0

    with open(out_file, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["nama_proyek", "periode", "nama_di", "nama_gambar", "url"])
        for path in files:
            nama_proyek, periode, nama_di, nama_gambar = parse_path_info(path)
            if owner and repo and branch:
                url = make_github_url(owner, repo, branch, path)
            else:
                url = ""
            writer.writerow([
                nama_proyek,
                periode,
                nama_di,
                nama_gambar,
                url
            ])

    print(f"Wrote {len(files)} rows to {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())