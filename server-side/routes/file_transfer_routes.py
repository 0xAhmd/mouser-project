"""
Enhanced File Transfer Server with PC-to-Phone capability
Add these routes to your existing Flask server
"""

import os
import json
import mimetypes
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Add this blueprint to your existing server
pc_transfer_bp = Blueprint('pc_transfer', __name__)

# Configuration
ALLOWED_DOWNLOAD_EXTENSIONS = {
    'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
    'mp3', 'mp4', 'avi', 'mov', 'wav', 'flac',
    'zip', 'rar', '7z', 'tar', 'gz',
    'json', 'xml', 'csv', 'log'
}

MAX_FILE_SIZE_MB = 100  # Limit file size for mobile downloads
MAX_FILES_PER_REQUEST = 10

def is_safe_path(base_path, path):
    """Check if path is safe (prevents directory traversal)"""
    try:
        base_path = Path(base_path).resolve()
        file_path = Path(base_path / path).resolve()
        return str(file_path).startswith(str(base_path))
    except (OSError, ValueError):
        return False

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0

def format_file_size(size_bytes):
    """Format file size for display"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

@pc_transfer_bp.route('/pc-transfer/browse', methods=['GET'])
def browse_directories():
    """Browse PC directories for file selection"""
    try:
        path = request.args.get('path', '')
        
        # Default to user's home directory if no path provided
        if not path:
            path = str(Path.home())
        
        # Security check
        base_path = Path.home()
        if not is_safe_path(base_path, path):
            return jsonify({
                "status": "error",
                "error": "Access denied to this path"
            }), 403
        
        target_path = Path(path)
        
        if not target_path.exists():
            return jsonify({
                "status": "error",
                "error": "Path does not exist"
            }), 404
        
        if not target_path.is_dir():
            return jsonify({
                "status": "error", 
                "error": "Path is not a directory"
            }), 400
        
        directories = []
        files = []
        
        try:
            for item in target_path.iterdir():
                try:
                    if item.is_dir():
                        directories.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "directory",
                            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                        })
                    elif item.is_file():
                        file_stat = item.stat()
                        file_ext = item.suffix.lower().lstrip('.')
                        
                        files.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "file",
                            "size": file_stat.st_size,
                            "size_formatted": format_file_size(file_stat.st_size),
                            "extension": file_ext,
                            "downloadable": file_ext in ALLOWED_DOWNLOAD_EXTENSIONS and get_file_size_mb(item) <= MAX_FILE_SIZE_MB,
                            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            "mime_type": mimetypes.guess_type(str(item))[0] or 'application/octet-stream'
                        })
                except (OSError, PermissionError):
                    continue  # Skip inaccessible files
                    
        except PermissionError:
            return jsonify({
                "status": "error",
                "error": "Permission denied to read directory"
            }), 403
        
        # Sort directories first, then files
        directories.sort(key=lambda x: x['name'].lower())
        files.sort(key=lambda x: x['name'].lower())
        
        return jsonify({
            "status": "success",
            "current_path": str(target_path),
            "parent_path": str(target_path.parent) if target_path != target_path.parent else None,
            "directories": directories,
            "files": files,
            "total_directories": len(directories),
            "total_files": len(files)
        })
        
    except Exception as e:
        logger.error(f"Error browsing directories: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@pc_transfer_bp.route('/pc-transfer/file-info', methods=['POST'])
def get_file_info():
    """Get detailed information about selected files"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400
        
        file_paths = data.get('paths', [])
        if not file_paths:
            return jsonify({"status": "error", "error": "No file paths provided"}), 400
        
        if len(file_paths) > MAX_FILES_PER_REQUEST:
            return jsonify({
                "status": "error", 
                "error": f"Too many files selected. Maximum {MAX_FILES_PER_REQUEST} files allowed"
            }), 400
        
        file_info_list = []
        total_size = 0
        downloadable_count = 0
        
        for file_path in file_paths:
            try:
                # Security check
                if not is_safe_path(Path.home(), file_path):
                    continue
                
                path = Path(file_path)
                if not path.exists() or not path.is_file():
                    continue
                
                file_stat = path.stat()
                file_size = file_stat.st_size
                file_ext = path.suffix.lower().lstrip('.')
                size_mb = get_file_size_mb(path)
                
                is_downloadable = (
                    file_ext in ALLOWED_DOWNLOAD_EXTENSIONS and 
                    size_mb <= MAX_FILE_SIZE_MB
                )
                
                file_info = {
                    "path": str(path),
                    "name": path.name,
                    "size": file_size,
                    "size_formatted": format_file_size(file_size),
                    "size_mb": round(size_mb, 2),
                    "extension": file_ext,
                    "downloadable": is_downloadable,
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "mime_type": mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
                }
                
                if not is_downloadable:
                    if file_ext not in ALLOWED_DOWNLOAD_EXTENSIONS:
                        file_info["skip_reason"] = f"File type '.{file_ext}' not allowed"
                    elif size_mb > MAX_FILE_SIZE_MB:
                        file_info["skip_reason"] = f"File too large ({size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB)"
                else:
                    downloadable_count += 1
                    total_size += file_size
                
                file_info_list.append(file_info)
                
            except (OSError, PermissionError) as e:
                logger.warning(f"Cannot access file {file_path}: {e}")
                continue
        
        return jsonify({
            "status": "success",
            "files": file_info_list,
            "summary": {
                "total_files": len(file_info_list),
                "downloadable_files": downloadable_count,
                "total_size": total_size,
                "total_size_formatted": format_file_size(total_size),
                "max_file_size_mb": MAX_FILE_SIZE_MB,
                "allowed_extensions": list(ALLOWED_DOWNLOAD_EXTENSIONS)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@pc_transfer_bp.route('/pc-transfer/download', methods=['POST'])
def download_files():
    """Download files to phone - returns download URLs"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400
        
        file_paths = data.get('paths', [])
        if not file_paths:
            return jsonify({"status": "error", "error": "No file paths provided"}), 400
        
        download_info = []
        
        for file_path in file_paths:
            try:
                # Security check
                if not is_safe_path(Path.home(), file_path):
                    download_info.append({
                        "path": file_path,
                        "status": "error",
                        "error": "Access denied"
                    })
                    continue
                
                path = Path(file_path)
                if not path.exists() or not path.is_file():
                    download_info.append({
                        "path": file_path,
                        "status": "error", 
                        "error": "File not found"
                    })
                    continue
                
                file_ext = path.suffix.lower().lstrip('.')
                size_mb = get_file_size_mb(path)
                
                if file_ext not in ALLOWED_DOWNLOAD_EXTENSIONS:
                    download_info.append({
                        "path": file_path,
                        "status": "error",
                        "error": f"File type '.{file_ext}' not allowed"
                    })
                    continue
                
                if size_mb > MAX_FILE_SIZE_MB:
                    download_info.append({
                        "path": file_path,
                        "status": "error",
                        "error": f"File too large ({size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB)"
                    })
                    continue
                
                # Generate download URL
                # Use base64 encoding of path for security
                import base64
                encoded_path = base64.urlsafe_b64encode(file_path.encode()).decode()
                download_url = f"/pc-transfer/download-file/{encoded_path}"
                
                download_info.append({
                    "path": file_path,
                    "name": path.name,
                    "status": "ready",
                    "download_url": download_url,
                    "size": path.stat().st_size,
                    "size_formatted": format_file_size(path.stat().st_size),
                    "mime_type": mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
                })
                
            except Exception as e:
                logger.error(f"Error preparing download for {file_path}: {e}")
                download_info.append({
                    "path": file_path,
                    "status": "error",
                    "error": str(e)
                })
        
        successful_downloads = [d for d in download_info if d.get("status") == "ready"]
        
        return jsonify({
            "status": "success" if successful_downloads else "partial",
            "downloads": download_info,
            "summary": {
                "total_requested": len(file_paths),
                "ready_for_download": len(successful_downloads),
                "errors": len(download_info) - len(successful_downloads)
            }
        })
        
    except Exception as e:
        logger.error(f"Error preparing downloads: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@pc_transfer_bp.route('/pc-transfer/download-file/<encoded_path>', methods=['GET'])
def download_file(encoded_path):
    """Download a single file"""
    try:
        # Decode the file path
        import base64
        try:
            file_path = base64.urlsafe_b64decode(encoded_path.encode()).decode()
        except Exception:
            return jsonify({"error": "Invalid file path"}), 400
        
        # Security check
        if not is_safe_path(Path.home(), file_path):
            return jsonify({"error": "Access denied"}), 403
        
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return jsonify({"error": "File not found"}), 404
        
        # Check file type and size
        file_ext = path.suffix.lower().lstrip('.')
        if file_ext not in ALLOWED_DOWNLOAD_EXTENSIONS:
            return jsonify({"error": "File type not allowed"}), 403
        
        if get_file_size_mb(path) > MAX_FILE_SIZE_MB:
            return jsonify({"error": "File too large"}), 413
        
        # Get MIME type
        mime_type = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        
        # Send file
        return send_file(
            str(path),
            as_attachment=True,
            download_name=path.name,
            mimetype=mime_type
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({"error": str(e)}), 500

@pc_transfer_bp.route('/pc-transfer/quick-access', methods=['GET'])
def get_quick_access_folders():
    """Get commonly used folders for quick access"""
    try:
        home = Path.home()
        quick_folders = []
        
        # Common folders
        common_paths = [
            ("Home", home),
            ("Desktop", home / "Desktop"),
            ("Documents", home / "Documents"), 
            ("Downloads", home / "Downloads"),
            ("Pictures", home / "Pictures"),
            ("Videos", home / "Videos"),
            ("Music", home / "Music"),
        ]
        
        for name, path in common_paths:
            if path.exists() and path.is_dir():
                try:
                    # Count files in directory
                    file_count = sum(1 for item in path.iterdir() if item.is_file())
                    dir_count = sum(1 for item in path.iterdir() if item.is_dir())
                    
                    quick_folders.append({
                        "name": name,
                        "path": str(path),
                        "file_count": file_count,
                        "dir_count": dir_count,
                        "accessible": True
                    })
                except PermissionError:
                    quick_folders.append({
                        "name": name,
                        "path": str(path),
                        "file_count": 0,
                        "dir_count": 0,
                        "accessible": False
                    })
        
        return jsonify({
            "status": "success",
            "folders": quick_folders,
            "home_path": str(home)
        })
        
    except Exception as e:
        logger.error(f"Error getting quick access folders: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

